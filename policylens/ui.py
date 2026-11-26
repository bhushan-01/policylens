"""
PolicyLens web UI (Gradio) — Evidence Pack, Classifier, Evidence Tribunal.

  python -m policylens.ui
Then open the local URL printed in the terminal.

Set POLICYLENS_SHARE=1 for a temporary public Gradio link.
"""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr

from policylens.answer import generate_answer, retrieval_only
from policylens.config import load_env
from policylens.search import search


EXAMPLES = [
    "We build CV screening software for HR teams",
    "Can I use AI to detect my employees' emotions at work?",
    "Customer support chatbot that answers FAQs",
    "Face recognition camera in a shopping mall",
    "Talent acquisition ranking engine for job applicants",
]

CSS = """
/* Gradio puts the `dark` class on <body> (not <html>), so every theme rule keys off body.dark.
   We never force text colours: Gradio picks readable text for each mode, we only tint the page. */
.gradio-container {
  font-family: "IBM Plex Sans", "Source Sans 3", ui-sans-serif, system-ui, sans-serif !important;
}
body:not(.dark) .gradio-container {
  background:
    radial-gradient(1200px 500px at 10% -10%, #cfe8df 0%, transparent 55%),
    radial-gradient(900px 400px at 100% 0%, #d9e4f0 0%, transparent 50%),
    linear-gradient(180deg, #f7faf8 0%, #eef3f0 100%) !important;
}
body.dark .gradio-container {
  background:
    radial-gradient(1200px 500px at 10% -10%, #123329 0%, transparent 55%),
    linear-gradient(180deg, #0f1714 0%, #0b1210 100%) !important;
}
.pl-hero h1 {
  font-family: "IBM Plex Serif", "Source Serif 4", Georgia, serif !important;
  font-size: 2.1rem !important;
  letter-spacing: -0.02em;
  margin-bottom: 0.25rem !important;
}
body:not(.dark) .pl-hero h1 { color: #0f1c18 !important; }
body.dark .pl-hero h1 { color: #e8f0ec !important; }
body:not(.dark) .pl-hero p { color: #345045 !important; }
body.dark .pl-hero p { color: #a9c2b6 !important; }
.pl-hero p { max-width: 46rem; }
.pl-badge {
  display: inline-block;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #1f6f5b;
  font-weight: 600;
  margin-bottom: 0.4rem;
}
body.dark .pl-badge { color: #6fd0b0; }
/* Inline code chips: readable in both themes */
.prose code { padding: 0.1rem 0.35rem; border-radius: 0.3rem; white-space: nowrap; }
body:not(.dark) .prose code { background: #dfeae4 !important; color: #10211b !important; }
body.dark .prose code { background: #1f3a30 !important; color: #d9efe5 !important; }
/* Keep short table columns (Status, Cite) on one line; let the last column wrap */
.prose th, .prose td { white-space: nowrap; }
.prose td:last-child, .prose th:last-child { white-space: normal; }
footer { display: none !important; }
"""


def run(product: str, top_k: int = 8) -> tuple[str, str]:
    product = (product or "").strip()
    if not product:
        return "Enter a product description.", ""

    results = search(product, top_k=int(top_k))
    evidence_lines = [
        f"- {r['score']:.3f}  {r['citation']} ({r['id']}) — {r['title']}"
        for r in results
    ]
    evidence = "\n".join(evidence_lines)

    from policylens.classification import classify_product

    first = classify_product(product)
    header = f"**Rule-based first pass: {first['tier']}**\n\n" + "\n".join(
        f"- **{b['cite']}** — {b['why']}"
        + (f"\n  > {b['quote']}" if b["quote"] else "")
        for b in first["basis"]
    )
    if first.get("semantic_near"):
        header += "\n\n**Semantic near-misses:** " + ", ".join(
            f"`{n['rule']}` ({n['score']})" for n in first["semantic_near"]
        )
    header += "\n\n---\n\n"

    env = load_env()
    try:
        if env.get("OPENROUTER_API_KEY") or env.get("ANTHROPIC_API_KEY"):
            answer = generate_answer(product, results)
        else:
            answer = retrieval_only(product, results)
    except Exception as e:
        answer = f"Generation failed: {e}\n\nEvidence still available on the right."

    return header + answer, evidence


def run_pack(files, questionnaire, no_llm):
    """Evidence Pack tab: vendor docs + buyer questionnaire -> cited draft answers + gap list."""
    import tempfile

    from policylens.blueprint import blueprints_for_gaps
    from policylens.pack import build_pack
    from policylens.render import render_markdown, write_outputs

    if not files or not questionnaire:
        return "Upload your company documents (.md/.txt) and a questionnaire.", None, ""
    tmp = Path(tempfile.mkdtemp())
    docs = tmp / "docs"
    docs.mkdir()
    for f in files:
        src = Path(getattr(f, "name", f))
        (docs / src.name).write_bytes(src.read_bytes())
    q = Path(getattr(questionnaire, "name", questionnaire))
    pack = build_pack(str(docs), str(q), use_llm=False if no_llm else None)
    paths = write_outputs(pack, tmp / "out")
    bps = blueprints_for_gaps(pack["gaps"])
    fix = ["## Fix-first blueprints", ""]
    for bp in bps[:8]:
        fix.append(f"### {bp['topic']} ({bp['article']}) — {bp['status']}")
        fix.append(bp["note"])
        for s in bp["sections"]:
            fix.append(f"- {s}")
        fix.append("")
    return render_markdown(pack), [str(p) for p in paths], "\n".join(fix)


def run_tribunal(product: str, promote: bool):
    from policylens.tribunal import render_tribunal_markdown, run_tribunal as _run

    product = (product or "").strip()
    if not product:
        return "Enter a product description.", ""
    result = _run(product, promote_semantic=bool(promote))
    md = render_tribunal_markdown(result)
    import json

    return md, json.dumps(
        {
            "verdict": result["verdict"],
            "ledger": result["ledger"],
            "semantic_near": result.get("semantic_near"),
        },
        indent=2,
    )


def main():
    share = os.environ.get("POLICYLENS_SHARE", "").lower() in {"1", "true", "yes"}
    with gr.Blocks(title="PolicyLens") as demo:
        with gr.Column(elem_classes=["pl-hero"]):
            gr.HTML(
                '<div class="pl-badge">PolicyLens · EU AI Act</div>'
                "<h1>Cited answers. Adversarial proof.</h1>"
                "<p>Classify products, draft questionnaire packs from your own docs, and run an "
                "Evidence Tribunal that only keeps claims with verified Article/Annex quotes. "
                "Not legal advice.</p>"
            )
        with gr.Tab("Evidence Pack"):
            gr.Markdown(
                "Upload vendor docs and a buyer questionnaire. Every answer is cited to the "
                "law and to *your* documents; gaps become **NEEDS INPUT**, never guesses."
            )
            f_docs = gr.File(label="Company documents (.md / .txt)", file_count="multiple")
            f_q = gr.File(
                label="Questionnaire (.md numbered list, or .csv with a 'question' column)"
            )
            c_off = gr.Checkbox(label="Offline mode (no LLM)", value=False)
            b_pack = gr.Button("Build evidence pack", variant="primary")
            o_md = gr.Markdown()
            o_fix = gr.Markdown(label="Fix-first blueprints")
            o_files = gr.File(label="Downloads (md, html, json, csv)", file_count="multiple")
            b_pack.click(run_pack, inputs=[f_docs, f_q, c_off], outputs=[o_md, o_files, o_fix])
        with gr.Tab("Evidence Tribunal"):
            gr.Markdown(
                "### Adversarial proof ledger\n"
                "Prosecutor charges → Defense motions → Citation audit → Verdict. "
                "Only VERIFIED / CHALLENGED rows survive. Replaces the old free-form agent."
            )
            t_in = gr.Textbox(label="AI product description", lines=4)
            t_prom = gr.Checkbox(
                label="Promote semantic near-misses into charges (exploratory)",
                value=False,
            )
            t_btn = gr.Button("Convene tribunal", variant="primary")
            t_md = gr.Markdown()
            with gr.Accordion("Ledger JSON (machine-readable)", open=False):
                t_json = gr.Code(language="json", label="Ledger JSON")
            gr.Examples(EXAMPLES, inputs=[t_in])
            t_btn.click(run_tribunal, inputs=[t_in, t_prom], outputs=[t_md, t_json])
            t_in.submit(run_tribunal, inputs=[t_in, t_prom], outputs=[t_md, t_json])
        with gr.Tab("Classify"):
            _classify_tab()
    # Gradio >= 6 takes theme/css in launch(); older versions take them in Blocks().
    demo.launch(share=share, theme=gr.themes.Soft(primary_hue="emerald"), css=CSS)


def _classify_tab():
    gr.Markdown(
        "Describe a product → risk first pass with verbatim law quotes + retrieved citations."
    )
    inp = gr.Textbox(
        label="AI product description",
        lines=4,
        placeholder="e.g. We build CV screening software for HR teams",
    )
    top_k = gr.Slider(3, 10, value=8, step=1, label="Chunks to retrieve")
    btn = gr.Button("Classify", variant="primary")
    with gr.Row():
        out_answer = gr.Markdown(label="Answer")
        out_evidence = gr.Textbox(label="Retrieved citations", lines=16)
    gr.Examples(EXAMPLES, inputs=[inp])
    btn.click(run, inputs=[inp, top_k], outputs=[out_answer, out_evidence])
    inp.submit(run, inputs=[inp, top_k], outputs=[out_answer, out_evidence])


if __name__ == "__main__":
    main()

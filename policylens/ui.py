"""
Simple PolicyLens web UI (Gradio).

  python -m policylens.ui
Then open the local URL printed in the terminal.
"""

from __future__ import annotations

import sys
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
]


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
        f"- **{b['cite']}** — {b['why']}" + (f"\n  > {b['quote']}" if b["quote"] else "") for b in first["basis"]) + "\n\n---\n\n"

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
    from policylens.pack import build_pack
    from policylens.render import render_markdown, write_outputs

    if not files or not questionnaire:
        return "Upload your company documents (.md/.txt) and a questionnaire.", None
    tmp = Path(tempfile.mkdtemp())
    docs = tmp / "docs"
    docs.mkdir()
    for f in files:
        src = Path(getattr(f, "name", f))
        (docs / src.name).write_bytes(src.read_bytes())
    q = Path(getattr(questionnaire, "name", questionnaire))
    pack = build_pack(str(docs), str(q), use_llm=False if no_llm else None)
    paths = write_outputs(pack, tmp / "out")
    return render_markdown(pack), [str(p) for p in paths]


def main():
    with gr.Blocks(title="PolicyLens") as demo:
        with gr.Tab("Evidence Pack (for vendors)"):
            gr.Markdown(
                "### Answer an EU buyer's AI Act questionnaire\n"
                "Upload your own product docs and the questionnaire. Every answer is cited to the "
                "law and to *your* documents; gaps become **NEEDS INPUT**, never guesses."
            )
            f_docs = gr.File(label="Company documents (.md / .txt)", file_count="multiple")
            f_q = gr.File(label="Questionnaire (.md numbered list, or .csv with a 'question' column)")
            c_off = gr.Checkbox(label="Offline mode (no LLM)", value=False)
            b_pack = gr.Button("Build evidence pack", variant="primary")
            o_md = gr.Markdown()
            o_files = gr.File(label="Downloads (md, html, json, csv)", file_count="multiple")
            b_pack.click(run_pack, inputs=[f_docs, f_q, c_off], outputs=[o_md, o_files])
        with gr.Tab("Classify a product"):
            _classify_tab()
    demo.launch()


def _classify_tab():
    gr.Markdown("EU AI Act governance copilot — describe a product, get risk + citations. Not formal legal advice.")
    inp = gr.Textbox(label="AI product description", lines=4, placeholder="e.g. We build CV screening software for HR teams")
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

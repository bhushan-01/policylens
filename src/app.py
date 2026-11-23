"""
Simple PolicyLens web UI (Gradio).

  python src/app.py
Then open the local URL printed in the terminal.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gradio as gr

from answer import generate_answer, load_env, retrieval_only
from search import search


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

    env = load_env()
    try:
        if env.get("OPENROUTER_API_KEY") or env.get("ANTHROPIC_API_KEY"):
            answer = generate_answer(product, results)
        else:
            answer = retrieval_only(product, results)
    except Exception as e:
        answer = f"Generation failed: {e}\n\nEvidence still available on the right."

    return answer, evidence


def main():
    with gr.Blocks(title="PolicyLens") as demo:
        gr.Markdown(
            """
# PolicyLens
EU AI Act governance copilot — describe a product, get risk + citations.

Not formal legal advice.
"""
        )
        with gr.Row():
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

    demo.launch()


if __name__ == "__main__":
    main()

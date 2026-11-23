"""
Step 10: answer a product/question using retrieved law chunks + Claude.

Requires ANTHROPIC_API_KEY in the environment (or a .env file).
Without a key, prints retrieval-only evidence (no generated answer).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from search import search

# Digital Omnibus on AI (2026) — not in the 2024 PDF
OMNIBUS_NOTE = """
IMPORTANT DATE UPDATES (EU Digital Omnibus on AI, 2026 — not in the 2024 PDF text):
- Stand-alone high-risk systems (Annex III / Article 6(2)): apply from 2 December 2027
  (delayed from 2 August 2026).
- High-risk systems in regulated products (Annex I / Article 6(1)): apply from 2 August 2028.
Always mention these updated dates when discussing when high-risk obligations apply.
""".strip()

SYSTEM = """You are PolicyLens, an EU AI Act governance copilot.

Rules:
1. Answer ONLY using the retrieved law excerpts provided.
2. Every claim must cite an Article or Annex (e.g. "According to Article 5...").
3. If the excerpts are not enough, say you are not sure — do NOT guess.
4. Classify risk when possible: Prohibited / High-risk / Transparency obligations / Minimal risk.
5. Include "When it applies" using the Omnibus date note when relevant.
6. This is not formal legal advice.
"""


def build_context(results: list[dict]) -> str:
    blocks = []
    for r in results:
        blocks.append(
            f"[{r['citation']} | {r['id']} | score={r['score']:.3f}]\n"
            f"Title: {r['title']}\n"
            f"{r['text']}"
        )
    return "\n\n---\n\n".join(blocks)


def answer_with_claude(question: str, results: list[dict]) -> str:
    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise SystemExit(
            "Install anthropic first: pip install anthropic"
        ) from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # try .env
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key:
        raise RuntimeError("missing_api_key")

    client = Anthropic(api_key=api_key)
    user = (
        f"{OMNIBUS_NOTE}\n\n"
        f"User question:\n{question}\n\n"
        f"Retrieved law excerpts:\n{build_context(results)}\n\n"
        "Write a clear answer with: Risk category (if possible), Why (with citations), "
        "When it applies (with Omnibus dates if high-risk)."
    )

    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1200,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


def retrieval_only(question: str, results: list[dict]) -> str:
    lines = [
        "Retrieval-only mode (no ANTHROPIC_API_KEY set).",
        "Here are the most relevant law pieces. Add a key to generate a full answer.",
        "",
        f"Question: {question}",
        "",
        "Top evidence:",
    ]
    for r in results:
        lines.append(f"- {r['citation']} ({r['id']}) score={r['score']:.3f}: {r['title']}")
    lines.append("")
    lines.append(OMNIBUS_NOTE)
    return "\n".join(lines)


def main():
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "My startup makes software that screens job applicants' CVs. How does the EU AI Act apply?"

    results = search(question, top_k=8)
    print("=" * 60)
    try:
        text = answer_with_claude(question, results)
        print(text)
    except RuntimeError as e:
        if str(e) == "missing_api_key":
            print(retrieval_only(question, results))
        else:
            raise
    print("=" * 60)
    print("\nCitations used:")
    for r in results:
        print(f"  {r['score']:.3f}  {r['citation']}  {r['id']}")


if __name__ == "__main__":
    main()

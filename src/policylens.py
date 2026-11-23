"""
PolicyLens — the sensible main entry point.

What this product is:
  A founder/builder describes their AI product.
  PolicyLens checks the EU AI Act in a fixed order (like a compliance checklist)
  and returns a clear risk result with citations.

Why not just ChatGPT?
  ChatGPT can invent Articles. PolicyLens only answers from retrieved law text
  (and must say "not sure" if evidence is weak).

Usage:
  python src/policylens.py "We build CV screening software for HR teams"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from answer import generate_answer, load_env, OMNIBUS_NOTE
from search import search


def gather_evidence(product: str) -> dict:
    """
    Fixed checklist (this is the useful 'agent-like' workflow):
    1) prohibited?
    2) high-risk?
    3) transparency?
    """
    steps = {
        "prohibited": search(
            f"prohibited AI practices Article 5: {product}", top_k=4
        ),
        "high_risk": search(
            f"Annex III high-risk recruitment hiring job applications employment: {product}",
            top_k=5,
        ),
        "transparency": search(
            f"Article 50 transparency obligations for AI systems: {product}",
            top_k=3,
        ),
    }

    # Merge unique chunks for the final write-up (best scores first)
    merged = {}
    for group in steps.values():
        for r in group:
            prev = merged.get(r["id"])
            if prev is None or r["score"] > prev["score"]:
                merged[r["id"]] = r
    ranked = sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:8]
    return {"steps": steps, "merged": ranked}


def format_evidence(steps: dict) -> str:
    lines = []
    labels = {
        "prohibited": "1) Prohibited check (Article 5 area)",
        "high_risk": "2) High-risk check (Article 6 / Annex III)",
        "transparency": "3) Transparency check (Article 50 area)",
    }
    for key, title in labels.items():
        lines.append(title)
        for r in steps[key][:3]:
            lines.append(
                f"   - {r['score']:.2f} {r['citation']} | {r['title']}"
            )
        lines.append("")
    return "\n".join(lines)


def main():
    product = " ".join(sys.argv[1:]).strip()
    if not product:
        print('Usage: python src/policylens.py "describe your AI product"')
        print('Example: python src/policylens.py "CV screening for HR teams"')
        sys.exit(1)

    print("=" * 64)
    print("POLICYLENS — EU AI Act check")
    print("=" * 64)
    print(f"Product: {product}\n")

    print("Running checklist (prohibited → high-risk → transparency)...\n")
    bundle = gather_evidence(product)
    print(format_evidence(bundle["steps"]))

    env = load_env()
    print("-" * 64)
    if env.get("OPENROUTER_API_KEY") or env.get("ANTHROPIC_API_KEY"):
        # Ask the LLM to synthesize ONLY from checklist evidence
        answer = generate_answer(product, bundle["merged"])
        print(answer)
    else:
        print("No API key in .env — showing evidence only.\n")
        print(OMNIBUS_NOTE)
        print("\nTop combined citations:")
        for r in bundle["merged"]:
            print(f"  {r['score']:.2f}  {r['citation']}  {r['id']}")

    print("\n" + "=" * 64)
    print("Remember: not formal legal advice. Citations must come from the law text above.")
    print("=" * 64)

    # Machine-readable dump for debugging / evals
    if "--json" in sys.argv:
        print(json.dumps(
            {
                "product": product,
                "evidence_ids": [r["id"] for r in bundle["merged"]],
            },
            indent=2,
        ))


if __name__ == "__main__":
    main()

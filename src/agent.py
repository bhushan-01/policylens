"""
Phase 3 (simple workflow agent): check prohibited → high-risk → transparency.

Uses tool-style functions (search_law, get_article) without a framework.
If ANTHROPIC_API_KEY is set, Claude can call tools; otherwise runs a fixed workflow.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from search import load, search, cite_label


def search_law(query: str, top_k: int = 5) -> list[dict]:
    return [
        {
            "citation": r["citation"],
            "id": r["id"],
            "parent_id": r["parent_id"],
            "title": r["title"],
            "score": round(r["score"], 3),
            "excerpt": r["text"][:500],
        }
        for r in search(query, top_k=top_k)
    ]


def get_article(parent_id: str) -> dict | None:
    _, chunks, _ = load()
    parts = [c for c in chunks if c["parent_id"] == parent_id]
    if not parts:
        return None
    return {
        "parent_id": parent_id,
        "citation": cite_label(parts[0]),
        "title": parts[0]["title"],
        "chapter": parts[0]["chapter"],
        "pieces": len(parts),
        "text": "\n\n".join(p["text"] for p in parts)[:8000],
    }


def workflow(product: str) -> dict:
    """Deterministic checklist workflow (no LLM required)."""
    prohibited = search_law(f"prohibited AI practices related to: {product}", top_k=4)
    high_risk = search_law(f"high-risk AI classification for: {product}", top_k=4)
    transparency = search_law(f"transparency obligations for: {product}", top_k=3)

    return {
        "product": product,
        "steps": {
            "1_prohibited_check": prohibited,
            "2_high_risk_check": high_risk,
            "3_transparency_check": transparency,
        },
        "suggested_next": (
            "Review citations above. For a written opinion with Omnibus dates, run: "
            'python src/classify.py "your product"'
        ),
    }


def main():
    product = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "CV screening software for hiring"

    # Optional: raw tool-calling agent with Claude
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and Path(".env").exists():
        for line in Path(".env").read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")

    if api_key:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            tools = [
                {
                    "name": "search_law",
                    "description": "Semantic search over the EU AI Act. Returns top matching Articles/Annexes.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "top_k": {"type": "integer"},
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "get_article",
                    "description": "Fetch full text pieces for a parent id like art_5 or annex_III.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "parent_id": {"type": "string"},
                        },
                        "required": ["parent_id"],
                    },
                },
            ]

            messages = [{"role": "user", "content": (
                "Classify this AI product under the EU AI Act. "
                "Use tools. Cite Articles/Annexes. If unsure, say so.\n\n"
                f"Product: {product}"
            )}]

            for _ in range(6):
                resp = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=1600,
                    tools=tools,
                    messages=messages,
                )
                messages.append({"role": "assistant", "content": resp.content})

                tool_uses = [b for b in resp.content if b.type == "tool_use"]
                if resp.stop_reason == "end_turn" or not tool_uses:
                    texts = [b.text for b in resp.content if hasattr(b, "text")]
                    print("\n".join(texts))
                    return

                tool_results = []
                for tu in tool_uses:
                    if tu.name == "search_law":
                        out = search_law(tu.input["query"], tu.input.get("top_k", 5))
                    elif tu.name == "get_article":
                        out = get_article(tu.input["parent_id"])
                    else:
                        out = {"error": "unknown tool"}
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": json.dumps(out)[:12000],
                    })
                messages.append({"role": "user", "content": tool_results})
            return
        except Exception as e:
            print(f"Agent LLM path failed ({e}); falling back to workflow.\n")

    result = workflow(product)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""
Phase 3: PolicyLens agent.

1) Deterministic workflow (no LLM): prohibited → high-risk → transparency
2) Optional tool-calling loop via OpenRouter (or Anthropic) using search_law / get_article
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from answer import load_env
from search import cite_label, load, search


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
    return {
        "product": product,
        "steps": {
            "1_prohibited_check": search_law(
                f"prohibited AI practices related to: {product}", top_k=4
            ),
            "2_high_risk_check": search_law(
                f"high-risk AI classification for: {product}", top_k=4
            ),
            "3_transparency_check": search_law(
                f"transparency obligations for: {product}", top_k=3
            ),
        },
        "suggested_next": (
            'For a written opinion: python src/classify.py "your product"'
        ),
    }


TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "search_law",
            "description": "Semantic search over the EU AI Act.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_article",
            "description": "Fetch full text pieces for parent id like art_5 or annex_III.",
            "parameters": {
                "type": "object",
                "properties": {"parent_id": {"type": "string"}},
                "required": ["parent_id"],
            },
        },
    },
]


def run_tool(name: str, args: dict):
    if name == "search_law":
        return search_law(args["query"], args.get("top_k", 5))
    if name == "get_article":
        return get_article(args["parent_id"])
    return {"error": f"unknown tool: {name}"}


def agent_openrouter(product: str, env: dict) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=env["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    model = env.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")
    messages = [
        {
            "role": "system",
            "content": (
                "You are PolicyLens. Use tools to classify the product under the EU AI Act. "
                "Cite Articles/Annexes. If unsure, say so. Not formal legal advice."
            ),
        },
        {
            "role": "user",
            "content": f"Classify this AI product under the EU AI Act:\n\n{product}",
        },
    ]

    for _ in range(6):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS_OPENAI,
            max_tokens=1600,
        )
        msg = resp.choices[0].message
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": msg.tool_calls,
            }
        )
        if not msg.tool_calls:
            return msg.content or ""

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            out = run_tool(call.function.name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(out)[:12000],
                }
            )
    return "Agent stopped after max tool loops."


def main():
    product = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "CV screening software for hiring"
    )
    env = load_env()

    if env.get("OPENROUTER_API_KEY"):
        try:
            print(agent_openrouter(product, env))
            return
        except Exception as e:
            print(f"OpenRouter agent failed ({e}); falling back to workflow.\n")

    print(json.dumps(workflow(product), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

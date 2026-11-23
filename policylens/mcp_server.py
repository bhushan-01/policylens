"""
Phase 4: PolicyLens MCP server.

Exposes tools to Cursor / Claude Code / Claude Desktop:
- search_law, get_article, classify_product
- scan_codebase, evidence_gaps, verify_citations

Run (stdio), from the project root or after `pip install -e .`:
  python -m policylens.mcp_server

Config example: mcp_config.example.json
"""

from __future__ import annotations

import json

from mcp.server.mcpserver import MCPServer

from policylens.answer import generate_answer
from policylens.config import load_env
from policylens.search import cite_label, load, search

mcp = MCPServer(
    "policylens",
    instructions=(
        "PolicyLens: EU AI Act governance tools. "
        "Always prefer citations from search_law / classify_product. "
        "If evidence is weak, say you are not sure."
    ),
)


@mcp.tool()
def search_law(query: str, top_k: int = 5) -> str:
    """Semantic search over the EU AI Act. Returns top Articles/Annexes with scores and excerpts."""
    top_k = max(1, min(int(top_k), 10))
    results = search(query, top_k=top_k)
    payload = [
        {
            "citation": r["citation"],
            "id": r["id"],
            "parent_id": r["parent_id"],
            "title": r["title"],
            "chapter": r["chapter"],
            "score": round(r["score"], 3),
            "excerpt": r["text"][:700],
        }
        for r in results
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False)


@mcp.tool()
def get_article(parent_id: str) -> str:
    """Fetch text for a parent id like art_5, art_6, or annex_III."""
    _, chunks, _ = load()
    parts = [c for c in chunks if c["parent_id"] == parent_id]
    if not parts:
        return json.dumps({"error": f"Unknown parent_id: {parent_id}"})
    payload = {
        "parent_id": parent_id,
        "citation": cite_label(parts[0]),
        "title": parts[0]["title"],
        "chapter": parts[0]["chapter"],
        "section": parts[0]["section"],
        "pieces": len(parts),
        "text": "\n\n".join(p["text"] for p in parts)[:12000],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


@mcp.tool()
def classify_product(product_description: str) -> str:
    """
    Classify an AI product under the EU AI Act.
    Retrieves relevant law text and (if an API key is configured) generates a cited answer.
    """
    results = search(product_description, top_k=8)
    evidence = [
        {
            "citation": r["citation"],
            "id": r["id"],
            "parent_id": r["parent_id"],
            "title": r["title"],
            "score": round(r["score"], 3),
        }
        for r in results
    ]

    env = load_env()
    if not env.get("OPENROUTER_API_KEY") and not env.get("ANTHROPIC_API_KEY"):
        return json.dumps(
            {
                "mode": "retrieval_only",
                "product": product_description,
                "evidence": evidence,
                "note": "Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY in .env for a full written answer.",
            },
            indent=2,
            ensure_ascii=False,
        )

    answer = generate_answer(product_description, results)
    return json.dumps(
        {
            "mode": "full_answer",
            "product": product_description,
            "answer": answer,
            "evidence": evidence,
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def scan_codebase(path: str) -> str:
    """
    Scan a code repository for EU AI Act red flags (emotion/biometric use, automated decisions
    with no human step, missing logging, missing AI disclosure, protected attributes as features).
    Every finding has file:line, a verified Article, why it matters, and a fix. Heuristic only.
    """
    from policylens import scanner

    return json.dumps(scanner.scan(path), indent=2, ensure_ascii=False)


@mcp.tool()
def evidence_gaps(docs_dir: str) -> str:
    """
    Check a folder of company docs (.md/.txt) against 14 buyer-expected AI Act obligations
    (Art. 4, 9-15, 17, 43, 49, 72, 73, 86). Returns Evidenced/Partial/Missing per obligation
    with the document passages found. Keyword triage, not a compliance finding.
    """
    from policylens.company import load_passages
    from policylens.pack import gap_analysis

    return json.dumps(gap_analysis(load_passages(docs_dir)), indent=2, ensure_ascii=False)


@mcp.tool()
def verify_citations(text: str) -> str:
    """Check every Article/Annex mentioned in `text` actually exists in the EU AI Act."""
    import laws

    cited = laws.extract_citations(text)
    return json.dumps({"cited": sorted(cited), "nonexistent": sorted(c for c in cited if not laws.exists(c))})


def main():
    # stdio transport for Cursor / Claude Desktop
    mcp.run()


if __name__ == "__main__":
    main()

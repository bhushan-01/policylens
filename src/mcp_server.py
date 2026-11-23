"""
Phase 4: PolicyLens MCP server.

Exposes tools to Cursor / Claude Desktop:
- search_law
- get_article
- classify_product

Run (stdio):
  .venv/bin/python src/mcp_server.py

Cursor MCP config example is in README / mcp_config.example.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root + src are importable when launched by MCP hosts
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from mcp.server.mcpserver import MCPServer

from answer import generate_answer, load_env
from search import cite_label, load, search

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
    import code_scan

    return json.dumps(code_scan.scan(path), indent=2, ensure_ascii=False)


@mcp.tool()
def evidence_gaps(docs_dir: str) -> str:
    """
    Check a folder of company docs (.md/.txt) against 14 buyer-expected AI Act obligations
    (Art. 4, 9-15, 17, 43, 49, 72, 73, 86). Returns Evidenced/Partial/Missing per obligation
    with the document passages found. Keyword triage, not a compliance finding.
    """
    from company import load_passages
    from evidence_pack import gap_analysis

    return json.dumps(gap_analysis(load_passages(docs_dir)), indent=2, ensure_ascii=False)


@mcp.tool()
def verify_citations(text: str) -> str:
    """Check every Article/Annex mentioned in `text` actually exists in the EU AI Act."""
    import laws

    cited = laws.extract_citations(text)
    return json.dumps({"cited": sorted(cited), "nonexistent": sorted(c for c in cited if not laws.exists(c))})


if __name__ == "__main__":
    # stdio transport for Cursor / Claude Desktop
    mcp.run()

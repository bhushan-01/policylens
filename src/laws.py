"""
Law lookup + citation checking.

The core trust feature of PolicyLens: every Article/Annex an answer mentions must
(a) exist in the Act and (b) have been in the evidence the model was shown.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "data" / "chunks.json"

# "Article 14", "Art. 14(4)", "Articles 9", "Annex III"  (only the first number of a range)
CITE_RE = re.compile(r"\b(Article|Articles|Art\.|Annex)\s+(\d+|[IVX]+)\b")


@lru_cache(maxsize=1)
def parents() -> dict[str, dict]:
    """Full Articles/Annexes keyed by id (e.g. art_14, annex_III)."""
    return {c["id"]: c for c in json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))}


def label(chunk: dict) -> str:
    return f"{'Article' if chunk['type'] == 'article' else 'Annex'} {chunk['number']}"


def norm_cite(kind: str, num: str) -> str:
    return f"{'Annex' if kind == 'Annex' else 'Article'} {num}"


def get(cite: str) -> dict | None:
    """'Article 14' / 'Annex III' -> full chunk, or None if it does not exist."""
    m = CITE_RE.search(cite)
    if not m:
        return None
    kind, num = m.groups()
    prefix = "annex" if kind == "Annex" else "art"
    return parents().get(f"{prefix}_{num}")


def exists(cite: str) -> bool:
    return get(cite) is not None


def extract_citations(text: str) -> set[str]:
    return {norm_cite(k, n) for k, n in CITE_RE.findall(text)}


def check_citations(text: str, allowed: set[str]) -> dict:
    """
    Compare citations in `text` to what is real and what was supplied as evidence.
      nonexistent  -> not an Article/Annex in the Act at all (hallucination)
      unsupported  -> real, but the model was never shown it (ungrounded)
    """
    cited = extract_citations(text)
    return {
        "cited": sorted(cited),
        "nonexistent": sorted(c for c in cited if not exists(c)),
        "unsupported": sorted(c for c in cited if exists(c) and c not in allowed),
    }


def excerpt(cite: str, limit: int = 3500) -> str:
    c = get(cite)
    if not c:
        return ""
    text = c["text"]
    return text if len(text) <= limit else text[:limit] + " […]"


def quote_around(cite: str, marker: str, before: int = 0, after: int = 420) -> str:
    """Verbatim quote from an Article/Annex starting at `marker` (empty if not found)."""
    c = get(cite)
    if not c:
        return ""
    t = re.sub(r"\s+", " ", c["text"])
    i = t.find(marker)
    if i < 0:
        return ""
    return t[max(0, i - before): i + after].strip()

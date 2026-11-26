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

from policylens.paths import DATA_DIR

CHUNKS_PATH = DATA_DIR / "chunks.json"

# "Article 14", "Art. 14(4)", "article 999", "Articles 9 and 999", "Annex III".
# Articles/Art/Annex is case-insensitive. Every number in "9 and 999" is checked, not only the first.
CITE_HEAD = re.compile(r"\b(Articles\b|Article\b|Art\.|Art\b|Annex\b)", re.I)
_NUM = r"(?:\d+|[IVX]+\b)"  # the \b stops "Article in" being read as "Article I"
CITE_RUN = re.compile(rf"\s*({_NUM}(?:\s*(?:,|and|&)\s*{_NUM})*)", re.I)


@lru_cache(maxsize=1)
def parents() -> dict[str, dict]:
    """Full Articles/Annexes keyed by id (e.g. art_14, annex_III)."""
    return {c["id"]: c for c in json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))}


def label(chunk: dict) -> str:
    return f"{'Article' if chunk['type'] == 'article' else 'Annex'} {chunk['number']}"


def norm_cite(kind: str, num: str) -> str:
    number = num.upper() if not num.isdigit() else num
    if kind.lower().startswith("annex"):
        return f"Annex {number}"
    return f"Article {number}"


def _first_cite(text: str) -> tuple[str, str] | None:
    m = CITE_HEAD.search(text or "")
    if not m:
        return None
    run = CITE_RUN.match(text, m.end())
    if not run:
        return None
    num = re.findall(r"\d+|[IVX]+", run.group(1), re.I)[0]
    return m.group(1), num


def get(cite: str) -> dict | None:
    """'Article 14' / 'Annex III' / 'article 14' -> full chunk, or None if it does not exist."""
    parsed = _first_cite(cite)
    if not parsed:
        return None
    kind, num = parsed
    label = norm_cite(kind, num)
    prefix = "annex" if label.startswith("Annex") else "art"
    return parents().get(f"{prefix}_{label.split(' ', 1)[1]}")


def exists(cite: str) -> bool:
    return get(cite) is not None


def extract_citations(text: str) -> set[str]:
    found: set[str] = set()
    for m in CITE_HEAD.finditer(text or ""):
        run = CITE_RUN.match(text, m.end())
        if not run:
            continue
        for num in re.findall(r"\d+|[IVX]+", run.group(1), re.I):
            found.add(norm_cite(m.group(1), num))
    return found


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

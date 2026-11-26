"""Load a vendor's own documents (markdown/text) as numbered, citable passages."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np


# A sentence that denies a fact must not count as evidence of that fact.
_NEGATION = re.compile(
    r"\b(not|no|never|without|cannot|can't|don't|doesn't|didn't|isn't|aren't|won't|hasn't|haven't)\b",
    re.I,
)
# Keywords cut off on purpose so they match a longer word ("notify authorities", "explainability").
_STEMS = ("authorit", "explainab")
_PATTERNS: dict[str, re.Pattern] = {}


def _keyword_pattern(keyword: str) -> re.Pattern:
    """Word-boundary match. 'bias' does not match 'unbiased'; 'audit log' matches 'audit logs'."""
    cached = _PATTERNS.get(keyword)
    if cached is not None:
        return cached
    raw = keyword.lower().strip()
    parts = [re.escape(w) for w in raw.split()]
    stem = any(raw.endswith(s) for s in _STEMS)
    if not stem and parts and parts[-1][-1].isalpha() and not raw.endswith("s"):
        parts[-1] = parts[-1] + r"s?"
    body = r"\s+".join(parts)
    pattern = re.compile(r"\b" + body if stem else r"\b" + body + r"\b", re.I)
    _PATTERNS[keyword] = pattern
    return pattern


def keyword_in(text: str, keyword: str) -> bool:
    return _keyword_pattern(keyword).search(text) is not None


def _sentences(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+|\n+", text) if p.strip()]


def load_passages(docs_dir: str | Path) -> list[dict]:
    """Split each .md/.txt file into passages by heading section. id = 'relative/path § n'."""
    root = Path(docs_dir)
    passages = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(root).as_posix()
        title = path.stem.replace("_", " ")
        sections, heading, buf = [], path.stem, []
        for line in text.splitlines():
            if line.startswith("#"):
                if buf:
                    sections.append((heading, "\n".join(buf).strip()))
                heading, buf = line.lstrip("# ").strip(), []
            else:
                buf.append(line)
        if buf:
            sections.append((heading, "\n".join(buf).strip()))
        n = 0
        for heading, body in sections:
            # Keep short policy lines ("We log every API call."). Drop headings with no body.
            if len(body.split()) < 3:
                continue
            n += 1
            passages.append({
                "id": f"{rel} § {n}",
                "file": rel,
                "title": title,
                "heading": heading,
                "text": body,
            })
    return passages


def keyword_hits(passages: list[dict], keywords: list[str]) -> list[tuple[dict, list[str]]]:
    """Passages containing any keyword, with which keywords matched. Strongest first.

    Matches are whole words, not substrings. A keyword inside a negated sentence
    ("no CE marking", "not registered", "unbiased") does not count.
    """
    out = []
    for p in passages:
        hits = []
        for k in keywords:
            in_title = keyword_in(p["title"], k)
            in_heading = keyword_in(p["heading"], k) and not _NEGATION.search(p["heading"])
            in_body = any(keyword_in(s, k) and not _NEGATION.search(s) for s in _sentences(p["text"]))
            if in_title or in_heading or in_body:
                hits.append(k)
        if hits:
            out.append((p, hits))
    return sorted(out, key=lambda x: -len(x[1]))


def rank_by_meaning(query: str, passages: list[dict], top_k: int = 4) -> list[dict]:
    """Embedding similarity (same model as law search) between a question and vendor passages.

    Returns [] if the embedding model cannot be loaded. Keyword evidence still works.
    """
    if not passages:
        return []
    try:
        from policylens.search import QUERY_PREFIX, load

        model, _, _ = load()
        vecs = model.encode([p["heading"] + ". " + p["text"] for p in passages], normalize_embeddings=True)
        q = model.encode([QUERY_PREFIX + query], normalize_embeddings=True)[0]
        scores = np.asarray(vecs) @ q
        order = np.argsort(scores)[::-1][:top_k]
        return [{**passages[int(i)], "score": float(scores[int(i)])} for i in order]
    except Exception:
        return []


def embed_passages(passages: list[dict]):
    """Encode passages once for batch semantic gap scoring. Returns (passages, matrix)."""
    if not passages:
        return passages, None
    from policylens.search import load

    model, _, _ = load()
    vecs = model.encode(
        [p["heading"] + ". " + p["text"] for p in passages],
        normalize_embeddings=True,
    )
    return passages, np.asarray(vecs)


def semantic_obligation_hits(
    passages: list[dict],
    ask: str,
    topic: str,
    top_k: int = 3,
    min_score: float = 0.42,
    passage_vecs=None,
) -> list[dict]:
    """
    Passages that mean something close to an obligation's ask/topic, even if keywords miss.
    Returns [{id, score, heading}] — advisory; does not by itself prove evidence.
    Pass `passage_vecs` from embed_passages() to avoid re-encoding.
    """
    if not passages:
        return []
    from policylens.search import QUERY_PREFIX, load

    model, _, _ = load()
    if passage_vecs is None:
        _, passage_vecs = embed_passages(passages)
    q = model.encode([QUERY_PREFIX + f"{topic}. {ask}"], normalize_embeddings=True)[0]
    scores = passage_vecs @ q
    order = np.argsort(scores)[::-1][:top_k]
    out = []
    for i in order:
        sc = float(scores[int(i)])
        if sc < min_score:
            continue
        p = passages[int(i)]
        out.append({"id": p["id"], "score": round(sc, 3), "heading": p["heading"]})
    return out

"""Load a vendor's own documents (markdown/text) as numbered, citable passages."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np


def load_passages(docs_dir: str | Path) -> list[dict]:
    """Split each .md/.txt file into passages by heading section. id = 'file § n'."""
    passages = []
    for path in sorted(Path(docs_dir).rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
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
            if len(body.split()) < 6:
                continue
            n += 1
            passages.append({
                "id": f"{path.name} § {n}",
                "file": path.name,
                "title": title,
                "heading": heading,
                "text": body,
            })
    return passages


def keyword_hits(passages: list[dict], keywords: list[str]) -> list[tuple[dict, list[str]]]:
    """Passages containing any keyword, with which keywords matched. Strongest first."""
    out = []
    for p in passages:
        hay = f"{p['title']} {p['heading']} {p['text']}".lower()
        hits = [k for k in keywords if k in hay]
        if hits:
            out.append((p, hits))
    return sorted(out, key=lambda x: -len(x[1]))


def rank_by_meaning(query: str, passages: list[dict], top_k: int = 4) -> list[dict]:
    """Embedding similarity (same model as law search) between a question and vendor passages."""
    if not passages:
        return []
    from policylens.search import QUERY_PREFIX, load

    model, _, _ = load()
    vecs = model.encode([p["heading"] + ". " + p["text"] for p in passages], normalize_embeddings=True)
    q = model.encode([QUERY_PREFIX + query], normalize_embeddings=True)[0]
    scores = np.asarray(vecs) @ q
    order = np.argsort(scores)[::-1][:top_k]
    return [{**passages[int(i)], "score": float(scores[int(i)])} for i in order]


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

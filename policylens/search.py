"""
Step 8: semantic search over embedded EU AI Act chunks.
"""

import json
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from policylens.paths import DATA_DIR

MODEL_NAME = "BAAI/bge-small-en-v1.5"
# Recommended query prefix for bge-small-en-v1.5
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Light keyword boost for phrases the dense model sometimes under-ranks
BOOST_PHRASES = [
    "emotion",
    "emotions",
    "social scoring",
    "social score",
    "recruitment",
    "job application",
    "biometric",
    "prohibited",
    "high-risk",
    "chatbot",
    "general-purpose",
]

CHUNKS_PATH = DATA_DIR / "chunks_split.json"
EMB_PATH = DATA_DIR / "embeddings.npy"

_model = None
_chunks = None
_embeddings = None


def keyword_bonus(query: str, text: str) -> float:
    q = query.lower()
    t = text.lower()
    # normalize close variants so "social scoring" matches "social score"
    q_norm = q.replace("social scoring", "social score")
    t_norm = t.replace("social scoring", "social score")
    bonus = 0.0
    for phrase in BOOST_PHRASES:
        if phrase in q_norm and phrase in t_norm:
            bonus += 0.08
    # tiny overlap on longer words
    q_words = set(re.findall(r"[a-z]{5,}", q_norm))
    t_words = set(re.findall(r"[a-z]{5,}", t_norm))
    if q_words:
        overlap = len(q_words & t_words) / len(q_words)
        bonus += 0.04 * overlap
    return bonus


def load():
    global _model, _chunks, _embeddings
    if _chunks is None:
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            _chunks = json.load(f)
        _embeddings = np.load(EMB_PATH)
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model, _chunks, _embeddings


def cite_label(chunk: dict) -> str:
    if chunk["type"] == "article":
        return f"Article {chunk['number']}"
    return f"Annex {chunk['number']}"


def search(query: str, top_k: int = 5, diversify_parents: bool = True) -> list[dict]:
    model, chunks, embeddings = load()
    q = model.encode([QUERY_PREFIX + query], normalize_embeddings=True)[0]
    scores = embeddings @ q
    # hybrid: dense score + small keyword bonus
    for i, c in enumerate(chunks):
        scores[i] = float(scores[i]) + keyword_bonus(query, c["text"])
    # pull a wider pool, then optionally keep diverse parents
    pool = min(len(scores), max(top_k * 8, 40))
    idxs = np.argsort(scores)[::-1][:pool]

    results = []
    seen_parents = set()
    for i in idxs:
        c = chunks[int(i)]
        parent = c["parent_id"]
        if diversify_parents and parent in seen_parents and len(results) >= top_k:
            continue
        if diversify_parents and parent in seen_parents:
            # allow at most 2 pieces per parent in the shortlist
            parent_count = sum(1 for r in results if r["parent_id"] == parent)
            if parent_count >= 2:
                continue
        seen_parents.add(parent)
        results.append({
            "id": c["id"],
            "parent_id": parent,
            "citation": cite_label(c),
            "title": c["title"],
            "chapter": c["chapter"],
            "section": c["section"],
            "score": float(scores[int(i)]),
            "text": c["text"],
        })
        if len(results) >= top_k:
            break
    return results


def print_results(query: str, top_k: int = 5):
    print(f"Query: {query}\n")
    for r in search(query, top_k=top_k):
        print(f"{r['score']:.3f}  {r['citation']}  ({r['id']})")
        print(f"       {r['title']}")
        if r["chapter"]:
            print(f"       {r['chapter']}")
        print(f"       {r['text'][:160].replace(chr(10), ' ')}...")
        print()


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "Is CV screening software high-risk?"
    print_results(query, top_k=5)

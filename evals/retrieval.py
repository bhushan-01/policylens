"""
Step 9: small retrieval eval — hit rate @k.
A question is a hit if any expected parent_id appears in the top-k results.
"""

import json
import sys
from pathlib import Path

from policylens.paths import EVALS_DIR
from policylens.search import search

EVAL_PATH = EVALS_DIR / "fixtures" / "eval_questions.json"


def main(top_k: int = 8):
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    hits = 0
    print(f"Retrieval eval @ {top_k}\n")

    for q in questions:
        results = search(q["question"], top_k=top_k)
        parents = {r["parent_id"] for r in results}
        expected = set(q["expect_any"])
        ok = bool(parents & expected)
        hits += int(ok)
        mark = "HIT " if ok else "MISS"
        found = ", ".join(sorted(parents & expected)) or "-"
        top = ", ".join(f"{r['parent_id']}({r['score']:.2f})" for r in results[:3])
        print(f"{mark}  {q['id']}: {q['question'][:60]}")
        print(f"      expected one of {sorted(expected)}; matched: {found}")
        print(f"      top: {top}")
        print()

    rate = hits / len(questions)
    print(f"Hit rate @{top_k}: {hits}/{len(questions)} = {rate:.0%}")
    return rate


if __name__ == "__main__":
    main(top_k=8)

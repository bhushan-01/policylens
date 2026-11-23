"""
Phase 5 (light): assertion-based evals on end-to-end answers.

Checks (when possible):
1. Retrieval hit: expected parent_id in top results
2. Citation present in generated answer
3. Risk keyword present
4. Omnibus date present when required

Usage:
  python src/eval_assertions.py              # retrieval assertions only (fast)
  python src/eval_assertions.py --llm        # also generate answers (needs API key)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from answer import generate_answer, load_env
from search import search

EVAL_PATH = Path("data/eval_assertions.json")


def contains_any(text: str, needles: list[str]) -> bool:
    t = text.lower()
    return any(n.lower() in t for n in needles)


def run_case(case: dict, use_llm: bool) -> dict:
    results = search(case["question"], top_k=8)
    parents = {r["parent_id"] for r in results}
    citations = " ".join(r["citation"] for r in results)

    checks = {}
    expected_parents = case.get("expect_parents_any") or []
    if expected_parents:
        checks["retrieval_hit"] = bool(parents & set(expected_parents))
    else:
        checks["retrieval_hit"] = True  # no parent requirement

    answer_text = ""
    if use_llm:
        answer_text = generate_answer(case["question"], results)
        if case.get("expect_citations_any"):
            checks["citation_in_answer"] = contains_any(
                answer_text, case["expect_citations_any"]
            )
        else:
            checks["citation_in_answer"] = True

        if case.get("expect_risk_keywords"):
            checks["risk_keyword"] = contains_any(
                answer_text, case["expect_risk_keywords"]
            )
        else:
            checks["risk_keyword"] = True

        if case.get("expect_date_any"):
            checks["omnibus_date"] = contains_any(answer_text, case["expect_date_any"])
        else:
            checks["omnibus_date"] = True
    else:
        # retrieval-only mode still checks citation labels among retrieved docs
        if case.get("expect_citations_any"):
            checks["citation_in_retrieval"] = contains_any(
                citations, case["expect_citations_any"]
            )

    ok = all(checks.values())
    return {
        "id": case["id"],
        "ok": ok,
        "checks": checks,
        "top_parents": [r["parent_id"] for r in results[:5]],
        "answer_preview": (answer_text[:240] + "…") if answer_text else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Generate full answers and assert on citations/risk/dates",
    )
    args = parser.parse_args()

    if args.llm:
        env = load_env()
        if not env.get("OPENROUTER_API_KEY") and not env.get("ANTHROPIC_API_KEY"):
            raise SystemExit("Need OPENROUTER_API_KEY or ANTHROPIC_API_KEY for --llm")

    cases = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    print(f"Assertion eval ({'LLM' if args.llm else 'retrieval-only'})\n")

    passed = 0
    reports = []
    for case in cases:
        report = run_case(case, use_llm=args.llm)
        reports.append(report)
        passed += int(report["ok"])
        mark = "PASS" if report["ok"] else "FAIL"
        print(f"{mark}  {report['id']}")
        print(f"      checks: {report['checks']}")
        print(f"      top: {report['top_parents']}")
        if report["answer_preview"]:
            print(f"      answer: {report['answer_preview']}")
        print()

    rate = passed / len(cases)
    print(f"Passed: {passed}/{len(cases)} = {rate:.0%}")
    out = Path("data/eval_assertion_report.json")
    out.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out}")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())

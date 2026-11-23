"""
Evals for the Evidence Pack. Deterministic, no API key or network needed.

  python src/eval_evidence.py

Checks the SAFETY NET, not the prose: classification, gap detection, and that
fabricated claims/citations from a (mocked) misbehaving model are caught.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidence_pack as ep
import laws
import llm

RESULTS = []


def check(name: str, ok: bool, detail: str = ""):
    ok = bool(ok)
    RESULTS.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))


def main():
    # 1. citation checker
    r = laws.check_citations("Per Article 14(4), Article 999 and Annex III.", {"Article 14"})
    check("citation: flags nonexistent Article 999", r["nonexistent"] == ["Article 999"], str(r))
    check("citation: flags real-but-unshown Annex III", r["unsupported"] == ["Annex III"], str(r))
    check("citation: accepts shown Article 14(4)", "Article 14" not in r["unsupported"] + r["nonexistent"])

    # 2. classification
    cases = [
        ("We build CV screening software for HR teams", "HIGH-RISK"),
        ("AI that ranks job applicants and evaluates candidates", "HIGH-RISK"),
        ("Tool that detects employees' emotions from webcam during work", "PROHIBITED"),
        ("Customer support chatbot that answers FAQs", "TRANSPARENCY"),
        ("Weather forecasting model for farmers", "No Annex III"),
        ("Algorithm to decide promotion and termination of staff", "HIGH-RISK"),
    ]
    for desc, want in cases:
        tier = ep.classify_product(desc)["tier"]
        check(f"classify: {desc[:48]!r} -> {want}", want.lower() in tier.lower(), tier)
    hire = ep.classify_product("CV screening for recruiters")
    check("classify: quotes real Annex III text", any("recruitment or selection" in b["quote"] for b in hire["basis"]))
    check("classify: every basis cite exists in the Act", all(laws.exists(b["cite"]) for b in hire["basis"]))

    # 3. gap analysis on the sample company (known by construction)
    passages = ep.load_passages("data/sample_company")
    gaps = {g["article"]: g["status"] for g in ep.gap_analysis(passages)}
    for art in ["Article 12", "Article 73", "Article 43", "Article 49", "Article 11", "Article 17", "Article 9"]:
        check(f"gaps: {art} reported Missing", gaps[art] == "Missing", gaps[art])
    for art in ["Article 14", "Article 15", "Article 10"]:
        check(f"gaps: {art} reported Evidenced", gaps[art] == "Evidenced", gaps[art])
    check("gaps: all obligation Articles exist", all(laws.exists(a) for a in gaps))

    # 4. offline pack never claims readiness it cannot back
    pack = ep.build_pack("data/sample_company", "data/sample_questionnaire.md", use_llm=False)
    check("offline: 14 questions parsed", len(pack["answers"]) == 14, str(len(pack["answers"])))
    check("offline: no answer marked READY without an LLM", all(a["status"] != "ready" for a in pack["answers"]))
    check("offline: all cited law exists", all(laws.exists(c) for a in pack["answers"] for c in a["law"]))

    # 5. adversarial: a misbehaving model invents capabilities and citations
    real = llm.complete_json
    try:
        llm.complete_json = lambda *a, **k: {
            "answer": "Yes, we log every event for 5 years in a tamper-proof ledger [doc: security_and_accuracy.md § 1] (Article 999).",
            "missing": []}
        a = ep.draft_answer("Does the system automatically log events, and for how long are logs retained?",
                            passages, True, {g["id"]: g for g in ep.gap_analysis(passages)}, hire)
        check("adversarial: invented logging claim forced to NEEDS INPUT", a["status"] == "needs_input" and "[NEEDS INPUT" in a["answer"], a["status"])
        check("adversarial: fake Article 999 caught", "Article 999" in a["verification"]["nonexistent"])

        llm.complete_json = lambda *a, **k: {"answer": "We do not use emotion recognition [doc: product_overview.md § 2].", "missing": []}
        a = ep.draft_answer("Does the system infer candidates' emotions?", passages, True,
                            {g["id"]: g for g in ep.gap_analysis(passages)}, hire)
        check("adversarial: unsupported negative claim sent to review", a["status"] == "review" and a["claim_flags"], a["status"])

        llm.complete_json = lambda *a, **k: {"answer": "We keep it safe [doc: made_up.md § 9].", "missing": []}
        a = ep.draft_answer("What cybersecurity measures protect the system?", passages, True,
                            {g["id"]: g for g in ep.gap_analysis(passages)}, hire)
        check("adversarial: fabricated doc reference caught", bool(a["verification"]["bad_doc_refs"]) and a["status"] == "review", a["status"])
    finally:
        llm.complete_json = real

    # 6. code scanner on a fictional repo with known problems
    import code_scan
    res = code_scan.scan("data/sample_repo")
    rules = {f["rule"] for f in res["findings"]}
    for rule in ["emotion-or-biometric", "automated-decision-no-human", "no-event-logging",
                 "no-ai-disclosure", "protected-attribute-as-feature", "employment-use-case", "no-incident-procedure"]:
        check(f"scan: detects {rule}", rule in rules)
    check("scan: all finding citations exist", all(laws.exists(f["cite"]) for f in res["findings"]))
    check("scan: critical finding sorted first", res["findings"][0]["severity"] == "critical")
    clean = code_scan.scan("data/sample_company")  # docs only, no code
    check("scan: no code findings on a docs-only folder", clean["findings"] == [], str(clean["findings"][:1]))

    passed = sum(RESULTS)
    print(f"\n{passed}/{len(RESULTS)} passed")
    sys.exit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).resolve().parents[1])
    main()

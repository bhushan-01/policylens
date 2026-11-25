"""
Evals for the Evidence Pack. Deterministic, no API key or network needed.

  python -m evals.evidence

Checks the SAFETY NET, not the prose: classification, gap detection, and that
fabricated claims/citations from a (mocked) misbehaving model are caught.
"""

from __future__ import annotations

import sys

from policylens import laws, llm
from policylens import pack as ep
from policylens import scanner as code_scan
from policylens.paths import EXAMPLES_DIR

COMPANY = EXAMPLES_DIR / "sample_company"
QUESTIONNAIRE = EXAMPLES_DIR / "sample_questionnaire.md"
REPO = EXAMPLES_DIR / "sample_repo"

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
        ("Face recognition camera in a shopping mall", "HIGH-RISK"),
        ("Live facial recognition used by police in public squares", "PROHIBITED"),
        ("Credit scoring for consumer loans", "HIGH-RISK"),
        ("AI proctoring that detects cheating during exams", "HIGH-RISK"),
        ("Automated grading of student essays", "HIGH-RISK"),
        ("Emergency call triage for ambulances", "HIGH-RISK"),
        ("Visa application risk scoring for border control", "HIGH-RISK"),
        ("Predicts which citizens will commit crime", "PROHIBITED"),
        ("Social scoring of citizens by their behaviour", "PROHIBITED"),
        ("Scrapes facial images from the internet to build a face database", "PROHIBITED"),
        ("Generates synthetic video of people", "TRANSPARENCY"),
        ("Selection of lunch menu items for the cafeteria", "No Annex III"),
        ("Inventory forecasting for a warehouse", "No Annex III"),
    ]
    for desc, want in cases:
        tier = ep.classify_product(desc)["tier"]
        check(f"classify: {desc[:48]!r} -> {want}", want.lower() in tier.lower(), tier)
    import re
    from policylens.risk_rules import RULES
    for r in RULES:  # a rule may only quote text the Act really contains
        text = re.sub(r"\s+", " ", laws.get(r["cite"])["text"])
        check(f"rules: marker for {r['id']} exists in {r['cite']}", r["marker"] in text)
    mall = ep.classify_product("Face recognition camera in a shopping mall")
    check("classify: mall camera cites Annex III 1(a) quote", any("remote biometric identification" in b["quote"] for b in mall["basis"]))
    check("classify: face-unlock note about verification exception",
          any("VERIFICATION" in n for n in ep.classify_product("Face recognition used to verify identity at login")["notes"]))
    sample = " ".join(p["text"] for p in ep.load_passages(COMPANY) if p["file"] == "product_overview.md")
    sc = ep.classify_product(sample)
    check("classify: stated exclusions are ignored (sample is 4(a) only, not 4(b))", sc["rule_ids"] == ["A4a"], str(sc["rule_ids"]))
    check("classify: exclusion does not hide a real use",
          "A4b" in ep.classify_product("It is not intended for hiring. It decides promotion and termination.")["rule_ids"])
    hire = ep.classify_product("CV screening for recruiters")
    check("classify: quotes real Annex III text", any("recruitment or selection" in b["quote"] for b in hire["basis"]))
    check("classify: every basis cite exists in the Act", all(laws.exists(b["cite"]) for b in hire["basis"]))

    # 3. gap analysis on the sample company (known by construction)
    passages = ep.load_passages(COMPANY)
    gaps = {g["article"]: g["status"] for g in ep.gap_analysis(passages)}
    for art in ["Article 12", "Article 73", "Article 43", "Article 49", "Article 11", "Article 17", "Article 9"]:
        check(f"gaps: {art} reported Missing", gaps[art] == "Missing", gaps[art])
    for art in ["Article 14", "Article 15", "Article 10"]:
        check(f"gaps: {art} reported Evidenced", gaps[art] == "Evidenced", gaps[art])
    check("gaps: all obligation Articles exist", all(laws.exists(a) for a in gaps))

    # 4. offline pack never claims readiness it cannot back
    pack = ep.build_pack(str(COMPANY), str(QUESTIONNAIRE), use_llm=False)
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

    # 5b. synonym / unusual-wording classification (keyword expansions)
    check(
        "classify: talent acquisition ranking → HIGH-RISK",
        "HIGH-RISK" in ep.classify_product("Talent acquisition ranking engine for job applicants")["tier"],
    )
    check(
        "classify: conversational agent → TRANSPARENCY",
        "TRANSPARENCY" in ep.classify_product("A conversational agent that chats with customers")["tier"],
    )

    # 5c. Evidence Tribunal: ledger only keeps real cites; defense motions fire
    from policylens.tribunal import run_tribunal
    from policylens.blueprint import blueprints_for_gaps

    t = run_tribunal("Face recognition used to verify identity at login")
    check("tribunal: returns a proof ledger", len(t["ledger"]) >= 1)
    check(
        "tribunal: every charge cite exists",
        all(laws.exists(r["cite"]) for r in t["ledger"] if r.get("cite")),
    )
    check(
        "tribunal: verification defense motion fires",
        any(m["id"] == "verification_only" for m in t["defense"]),
        str([m["id"] for m in t["defense"]]),
    )
    check(
        "tribunal: every non-defense ledger cite exists",
        all(laws.exists(r["cite"]) for r in t["ledger"] if r.get("cite") and not str(r["rule"]).startswith("defense:")),
    )
    hire_t = run_tribunal("CV screening software for HR teams")
    check(
        "tribunal: hiring product finds HIGH-RISK or surviving Annex charge",
        "HIGH-RISK" in hire_t["verdict"]["finding"]
        or any(r["rule"].startswith("A4") and r["status"] in {"VERIFIED", "CHALLENGED"} for r in hire_t["ledger"]),
        hire_t["verdict"]["finding"],
    )
    bps = blueprints_for_gaps(ep.gap_analysis(passages, use_semantic=False))
    check("blueprint: missing gaps get outlines", len(bps) >= 5 and all(bp.get("sections") for bp in bps))
    check(
        "blueprint: never claims compliance",
        all("NEEDS INPUT" in bp["note"] for bp in bps),
    )

    # 6. code scanner on a fictional repo with known problems
    res = code_scan.scan(REPO)
    rules = {f["rule"] for f in res["findings"]}
    for rule in ["emotion-or-biometric", "automated-decision-no-human", "no-event-logging",
                 "no-ai-disclosure", "protected-attribute-as-feature", "employment-use-case", "no-incident-procedure"]:
        check(f"scan: detects {rule}", rule in rules)
    check("scan: all finding citations exist", all(laws.exists(f["cite"]) for f in res["findings"]))
    check("scan: critical finding sorted first", res["findings"][0]["severity"] == "critical")
    clean = code_scan.scan(COMPANY)  # docs only, no code
    check("scan: no code findings on a docs-only folder", clean["findings"] == [], str(clean["findings"][:1]))

    passed = sum(RESULTS)
    print(f"\n{passed}/{len(RESULTS)} passed")
    sys.exit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    main()

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

        llm.complete_json = lambda *a, **k: {
            "answer": "Our technical documentation is available to every customer and regulator. "
                      "Recruiters can override any ranking [doc: human_oversight.md § 2].",
            "missing": []}
        a = ep.draft_answer("How do you ensure effective human oversight of the system?", passages, True,
                            {g["id"]: g for g in ep.gap_analysis(passages, use_semantic=False)}, hire)
        check("adversarial: uncited company claim is flagged, not READY",
              any("uncited company claim" in f for f in a["claim_flags"]) and a["status"] != "ready", str(a["claim_flags"]))
        check("pack: law list has no duplicates", len(a["law"]) == len(set(a["law"])), str(a["law"]))
    finally:
        llm.complete_json = real

    # 5a. company name comes from the document title, even when the folder is called "docs"
    import tempfile
    from pathlib import Path as _P

    with tempfile.TemporaryDirectory() as tmp:
        d = _P(tmp) / "docs"
        d.mkdir()
        (d / "product_overview.md").write_text(
            "# TalentRank - Product Overview\n\n## Intended purpose\n"
            "TalentRank helps recruiters analyse and filter job applications for open roles.\n", encoding="utf-8")
        q = _P(tmp) / "q.md"
        q.write_text("1. What is the intended purpose?\n", encoding="utf-8")
        check("pack: company name taken from the title, not the folder 'docs'",
              ep.build_pack(str(d), str(q), use_llm=False)["company"] == "TalentRank")

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
    check(
        "tribunal: Art 6(3) caution does not downgrade a clear hiring charge",
        any(r["rule"] == "A4a" and r["status"] == "VERIFIED" for r in hire_t["ledger"])
        and hire_t["verdict"]["confidence"] == "high",
        str([(r["rule"], r["status"]) for r in hire_t["ledger"]]),
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

    # 6b. false evidence and false risk labels the happy-path fixtures never hit
    check(
        "citation: lowercase article 999 is nonexistent",
        laws.check_citations("article 999 is banned", set())["nonexistent"] == ["Article 999"],
    )
    both = laws.check_citations("Articles 9 and 999", set())
    check("citation: Articles 9 and 999 flags 999", "Article 999" in both["nonexistent"], str(both))

    from policylens.classification import classify_product as _clf

    def _tier(text):
        return _clf(text, use_semantic=False)["tier"]

    check("classify: denial of emotion detection is not prohibited", "PROHIBITED" not in _tier("We do not detect employee emotions or mood at work."))
    check("classify: news candidate summaries are not hiring", "HIGH-RISK" not in _tier("The model returns candidate summaries of news articles."))
    check("classify: promotional email is not employment", "HIGH-RISK" not in _tier("We send promotional emails about our weather app."))
    check("classify: session termination is not dismissal", "HIGH-RISK" not in _tier("Automatic session termination after an idle timeout for a weather API."))
    check("classify: courting customers is not a court", "HIGH-RISK" not in _tier("We court enterprise customers with a newsletter."))
    check("classify: ticket triage is not emergency triage", "HIGH-RISK" not in _tier("Support ticket triage chatbot for password resets."))
    check("classify: a student mood journal is not prohibited", "PROHIBITED" not in _tier("Students use a mood journal to pin class inspiration."))
    check("classify: foundation model is GPAI, not minimal risk", "GPAI" in _tier("We train our own foundation model."))
    check("classify: candidates excluded from hiring is still hiring", "HIGH-RISK" in _tier("Candidates excluded from hiring are stored in this list."))

    hostile = (
        "# Overview\n\n"
        "Acme is a company registered in Delaware. Account registration is self-serve.\n"
        "We have not completed conformity assessment and there is no CE marking.\n"
        "The benchmark is unbiased and the sample is representative.\n"
        "The system is unregistered and has no EU database entry at all today.\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        (_P(tmp) / "overview.md").write_text(hostile, encoding="utf-8")
        hostile_gaps = {g["article"]: g["status"] for g in ep.gap_analysis(ep.load_passages(tmp), use_semantic=False)}
    check("gaps: Delaware registration is not EU-database evidence", hostile_gaps["Article 49"] != "Evidenced", hostile_gaps["Article 49"])
    check("gaps: a denied conformity assessment is not Evidenced", hostile_gaps["Article 43"] != "Evidenced", hostile_gaps["Article 43"])
    check("gaps: unbiased does not evidence bias testing", hostile_gaps["Article 10"] != "Evidenced", hostile_gaps["Article 10"])

    with tempfile.TemporaryDirectory() as tmp:
        root = _P(tmp)
        legal = root / "legal"
        legal.mkdir()
        (legal / "overview.md").write_text(
            "# Nested Co — Product Overview\n\nThis tool screens job applicants for recruiters using a ranking model today.\n",
            encoding="utf-8",
        )
        q = root / "q.md"
        q.write_text("Q1: Is the system high-risk?\n", encoding="utf-8")
        check("parse: Q1: questions are kept", ep.parse_questions(q) == ["Is the system high-risk?"])
        nested = ep.build_pack(str(root), str(q), use_llm=False)
        check(
            "pack: a document in a subfolder does not crash",
            nested["company"] == "Nested Co" and len(nested["answers"]) == 1,
            nested["company"],
        )

    scope = run_tribunal("CV screening software for HR teams. Biometric identification is out of scope.")
    check(
        "tribunal: an out-of-scope aside does not weaken a hiring charge",
        any(r["rule"] == "A4a" and r["status"] == "VERIFIED" for r in scope["ledger"]),
        str([(r["rule"], r["status"]) for r in scope["ledger"] if not str(r["rule"]).startswith("defense:")]),
    )
    gpai = run_tribunal("We train our own foundation model.")
    check("tribunal: a foundation model is not called minimal risk", "GPAI" in gpai["verdict"]["finding"], gpai["verdict"]["finding"])

    from policylens.render import render_html

    html = render_html({
        "company": "Acme", "date": "2026-11-26", "mode": "llm",
        "classification": {"tier": "HIGH-RISK", "basis": [{"cite": "Annex III", "why": "x", "quote": "q"}], "notes": []},
        "gaps": [{"topic": "Logging", "article": "Article 12", "status": "Missing", "evidence": [], "ask": "x"}],
        "summary": {"evidenced": 0, "partial": 0, "missing": 1, "total": 1},
        "answers": [{
            "question": "Do you log?", "status": "review", "answer": "We log forever (Article 999).",
            "missing": [], "law": ["Article 12"], "evidence": [],
            "verification": {"nonexistent": ["Article 999"], "unsupported": [], "bad_doc_refs": ["made_up.md § 1"]},
            "claim_flags": ["negative claim example"],
        }],
    })
    check("html: citation failure is visible", "Article 999" in html and "made_up.md" in html and "negative claim" in html)

    # 6c. narrowing false positives must never clear a real use
    check("citation: abbreviated Art. 999 is still caught",
          laws.check_citations("See Art. 999.", set())["nonexistent"] == ["Article 999"])
    check("citation: Art. 14(4) is read", laws.extract_citations("Per Art. 14(4)") == {"Article 14"})
    check("citation: ordinary words are not Roman numerals",
          laws.extract_citations("the Article in question and the Annex volume") == set())
    for text, want in [
        ("Our tool screens job applicants and never stores resumes.", "HIGH-RISK"),
        ("Recruiters never have to screen resumes again with our AI.", "HIGH-RISK"),
        ("Our AI ranks applicants and recruiters cannot see the reasons.", "HIGH-RISK"),
        ("We score candidates for open roles.", "HIGH-RISK"),
        ("We rank candidates automatically.", "HIGH-RISK"),
        ("Software that helps you hire faster.", "HIGH-RISK"),
        ("AI video interview scoring.", "HIGH-RISK"),
        ("An algorithm that decides employee termination.", "HIGH-RISK"),
        ("AI used by a court to assess defendants.", "HIGH-RISK"),
        ("Detects student mood in the classroom.", "PROHIBITED"),
    ]:
        check(f"classify: not cleared: {text[:44]!r}", want in _tier(text), _tier(text))

    passed = sum(RESULTS)
    print(f"\n{passed}/{len(RESULTS)} passed")
    sys.exit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    main()

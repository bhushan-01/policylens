"""
PolicyLens Evidence Pack — answer an EU buyer's AI Act questionnaire with citations.

Input : a folder of the vendor's own docs + a questionnaire (.md/.txt/.csv)
Output: out/evidence_pack.{md,html,json}, out/gaps.csv, out/ai_act_position.md

Design rules (the point of the product):
  * Statements about the LAW come only from retrieved Article/Annex text.
  * Statements about the COMPANY come only from the company's own documents.
  * Anything the documents don't support becomes "[NEEDS INPUT: ...]", never a guess.
  * Every Article/Annex an answer cites is machine-checked: it must exist AND have
    been shown to the model. Failures are flagged for human review.
  * Works with no API key (deterministic draft + evidence); an LLM only improves wording.

Usage:
  python src/evidence_pack.py --docs data/sample_company --questionnaire data/sample_questionnaire.md
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)  # search.py uses paths relative to the project root

import laws
import llm
from answer import OMNIBUS_NOTE
from company import keyword_hits, load_passages, rank_by_meaning
from obligations import BY_ID, OBLIGATIONS
from search import search

DISCLAIMER = ("Draft prepared from the vendor's own documents and the text of Regulation (EU) 2024/1689. "
              "Not legal advice. Have qualified counsel review before sending to a customer.")

# ---------------------------------------------------------------- classification

def _quote(cite: str, marker: str) -> str:
    return laws.quote_around(cite, marker, 40, 330)


def classify_product(description: str) -> dict:
    """
    Rule-based first pass over all Annex III areas, all Article 5 prohibitions and Article 50.
    Every rule quotes verbatim law text. Conservative: it flags, it never clears a product.
    """
    from risk_rules import RULES

    hits = [r for r in RULES if r["rx"].search(description) and (r.get("also") is None or r["also"].search(description))]
    prohibited = [r for r in hits if r["tier"] == "P"]
    high = [r for r in hits if r["tier"] == "H"]
    transp = [r for r in hits if r["tier"] == "T"]
    gpai = [r for r in hits if r["tier"] == "G"]
    basis, notes = [], []

    for r in prohibited + high + transp + gpai:
        basis.append({"cite": r["cite"], "rule": r["id"], "why": r["why"], "quote": _quote(r["cite"], r["marker"])})

    if prohibited:
        tier = "POSSIBLY PROHIBITED — urgent legal review"
        notes.append("Prohibited practices (Article 5) carry the Act's highest penalties. Narrow exceptions exist; only counsel can confirm whether one applies.")
    elif high:
        points = ", ".join(sorted({r["id"][1:].replace("a", "(a)").replace("b", "(b)").replace("c", "(c)").replace("d", "(d)") for r in high}))
        tier = f"HIGH-RISK (Annex III point {points})"
    elif transp:
        tier = "TRANSPARENCY obligations likely (Article 50)"
    else:
        tier = "No Annex III / Article 5 trigger found by keyword rules — likely minimal risk, confirm"

    if high:
        basis.append({"cite": "Article 6", "rule": "6(2)", "why": "Article 6(2): Annex III systems are high-risk. The Article 6(3) 'not high-risk' derogation does not apply where the system performs profiling of natural persons.",
                      "quote": laws.quote_around("Article 6", "Notwithstanding the first subparagraph", 0, 181)})
        notes.append("Ranking, scoring or predicting things about people generally counts as profiling, so do not rely on the Article 6(3) derogation without counsel.")
        notes.append(OMNIBUS_NOTE)
    ids = {r["id"] for r in hits}
    if "A1a" in ids and re.search(r"verif|unlock|authenticat|log.?in", description, re.I):
        notes.append("Annex III 1(a) excludes biometric VERIFICATION whose sole purpose is confirming a person is who they claim to be. Confirm yours is verification only.")
    if "A5b" in ids and re.search(r"fraud", description, re.I):
        notes.append("Annex III 5(b) excepts systems used to detect financial fraud. Credit scoring itself stays high-risk.")
    if high and transp:
        notes.append("Article 50 transparency duties apply in addition to the high-risk requirements.")
    if gpai:
        notes.append("If you train a general-purpose AI model you may be a provider under Article 53. Using someone else's model makes you a downstream provider or deployer instead.")
    return {"tier": tier, "basis": basis, "notes": notes, "rule_ids": sorted(ids),
            "disclaimer": "Keyword first pass; verify the intended purpose against the Annex III / Article 5 wording."}


# ---------------------------------------------------------------- gap analysis

def gap_analysis(passages: list[dict]) -> list[dict]:
    rows = []
    for o in OBLIGATIONS:
        hits = keyword_hits(passages, o["keywords"])
        matched = sorted({k for _, ks in hits for k in ks})
        if len(matched) >= 2:
            status = "Evidenced"
        elif len(matched) == 1:
            status = "Partial"
        else:
            status = "Missing"
        rows.append({
            "id": o["id"], "article": o["article"], "topic": o["topic"], "status": status,
            "ask": o["ask"], "matched_keywords": matched,
            "evidence": [p["id"] for p, _ in hits[:3]],
        })
    return rows


# ---------------------------------------------------------------- questionnaire

def parse_questions(path: str | Path) -> list[str]:
    p = Path(path)
    if p.suffix.lower() == ".csv":
        with p.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        col = next((c for c in (rows[0].keys() if rows else []) if "question" in c.lower()), None)
        return [r[col].strip() for r in rows if col and r[col].strip()]
    qs = []
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(?:\d+[.)]|[-*])\s+(.*\S)", line)
        if m:
            qs.append(m.group(1))
    return qs


def law_context(question: str) -> tuple[list[dict], set[str]]:
    """Law excerpts for a question: semantic search + best-matching known obligations."""
    hits = search(question, top_k=5)
    excerpts, allowed, seen = [], set(), set()
    for h in hits:
        if h["id"] in seen:
            continue
        seen.add(h["id"])
        excerpts.append({"cite": h["citation"], "title": h["title"], "text": h["text"][:1400]})
        allowed.add(h["citation"])
    # anchor with the obligation Article(s) whose keywords/topic match the question
    q = question.lower()
    scored = sorted(OBLIGATIONS, key=lambda o: -sum(k in q for k in o["keywords"] + o["topic"].lower().split("/")))
    for o in scored[:2]:
        if sum(k in q for k in o["keywords"]) and o["article"] not in allowed:
            excerpts.append({"cite": o["article"], "title": o["topic"], "text": laws.excerpt(o["article"], 1800)})
            allowed.add(o["article"])
    return excerpts, allowed


GENERIC_WORDS = {"system", "systems", "management", "protection", "information", "individual", "decisions"}
QUESTION_HINTS = {  # extra phrases that identify an obligation in a *question* (not used for scanning docs)
    "logging": [r"\blogs?\b", r"\blogging\b", "log events"],
    "post_market": ["after deployment", "post-deployment", r"\bmonitor"],
    "incidents": ["incident"],
    "oversight": ["oversight", "human review"],
    "explanation": ["explain"],
    "accuracy": ["accuracy", r"\bmetrics?\b"],
}


def match_obligation(question: str) -> dict | None:
    """Which known obligation is this question about? Keyword score; None if unclear."""
    q = question.lower()
    best, top = None, 0
    for o in OBLIGATIONS:
        score = 2 * sum(k in q for k in o["keywords"])
        score += 2 * sum(bool(re.search(h, q)) for h in QUESTION_HINTS.get(o["id"], []))
        score += sum(w in q for w in re.findall(r"[a-z]{5,}", o["topic"].lower()) if w not in GENERIC_WORDS)
        if score > top:
            best, top = o, score
    return best if top else None


ANSWER_SYSTEM = """You draft answers to a buyer's EU AI Act due-diligence questionnaire on behalf of an AI vendor.
Hard rules:
- Facts about the VENDOR come ONLY from the COMPANY EVIDENCE passages. Cite each as [doc: <id>] using the exact id shown.
- Statements about the LAW come ONLY from the LAW EXCERPTS. Cite as (Article N) or (Annex N). Never cite anything not shown.
- If the evidence does not support a fact the question needs, write "[NEEDS INPUT: what is missing]" instead of inventing it. Never invent numbers, dates, certifications or procedures.
- Absence of evidence is NOT evidence of absence: never state that the vendor lacks, does not do, or has not done something. Use [NEEDS INPUT: ...] instead.
- If a NOTICE says no document covers an obligation, you must not claim the vendor has it; answer only with [NEEDS INPUT: ...] and what the law expects.
- Cite exactly one document id per bracket, e.g. [doc: human_oversight.md § 2] [doc: human_oversight.md § 3].
- 2-5 sentences, professional, first person plural ("we"). No legal advice, no marketing language.
Return ONLY JSON: {"answer": "...", "missing": ["..."]}"""


def draft_answer(question: str, passages: list[dict], use_llm: bool, gaps: dict, classification: dict) -> dict:
    ob = match_obligation(question)
    ev, seen_ev = [], set()
    if ob:  # obligation keyword hits first: deterministic, then fill by meaning
        for p, _ in keyword_hits(passages, ob["keywords"])[:3]:
            ev.append(p); seen_ev.add(p["id"])
    for p in rank_by_meaning(question, passages, top_k=5):
        if len(ev) >= 4:
            break
        if p["id"] not in seen_ev:
            ev.append(p); seen_ev.add(p["id"])
    law, allowed = law_context(question)
    if ob:  # the obligation's own Article first, so it is always grounded
        law = [l for l in law if l["cite"] == ob["article"]] or \
              [{"cite": ob["article"], "title": ob["topic"], "text": laws.excerpt(ob["article"], 2200)}] + law
        allowed.add(ob["article"])
    if re.search(r"classif|high.?risk", question, re.I):  # reuse the verified classification quotes
        for b in classification["basis"]:
            if b["quote"]:
                law.append({"cite": b["cite"], "title": "quoted in classification", "text": b["quote"]}); allowed.add(b["cite"])
    law = law[:7]
    # Citations the model was shown: excerpt headers, plus Articles/Annexes named inside the shown text
    # (and the date note). Anything else it cites is ungrounded and gets flagged.
    for l in law:
        allowed |= laws.extract_citations(l["text"])
    allowed |= laws.extract_citations(OMNIBUS_NOTE)
    no_doc = bool(ob) and gaps[ob["id"]]["status"] == "Missing"
    rec = {"question": question, "law": [l["cite"] for l in law], "evidence": [e["id"] for e in ev], "mode": "offline",
           "obligation": ob["id"] if ob else None}

    if use_llm:
        user = ("QUESTION:\n" + question + "\n\nLAW EXCERPTS:\n" +
                "\n\n".join(f"[{l['cite']}] {l['title']}\n{l['text']}" for l in law) +
                "\n\nCOMPANY EVIDENCE:\n" +
                ("\n\n".join(f"[doc: {e['id']}] ({e['heading']})\n{e['text']}" for e in ev) or "(none found)") +
                (f"\n\nNOTICE: automated check found NO company document covering {ob['topic']} ({ob['article']})." if no_doc else "") +
                f"\n\n{OMNIBUS_NOTE}")
        try:
            out = llm.complete_json(ANSWER_SYSTEM, user, 900)
            ans = str(out.get("answer", "")).strip()
            missing = [str(m) for m in out.get("missing", [])]
            rec.update(answer=ans, missing=missing, mode="llm")
        except Exception as e:  # network/parse failure -> fall back, never crash the pack
            rec["llm_error"] = str(e)[:160]
            use_llm = False

    if not use_llm:
        rec["answer"] = ("[DRAFT NEEDED] Relevant company evidence: " +
                         ("; ".join(f"[doc: {e['id']}] {e['text'][:160].strip()}…" for e in ev[:2]) or "none found.") +
                         " Relevant law: " + ", ".join(sorted(allowed)[:4]) + ".")
        rec["missing"] = [] if ev else ["No company document addresses this question."]

    if no_doc and "[NEEDS INPUT" not in rec["answer"]:  # deterministic guard against invented capability claims
        rec["answer"] += f" [NEEDS INPUT: no document evidences {ob['topic']} ({ob['article']}); describe your actual practice or state it is not yet in place]"
        rec["guard"] = "forced needs-input: obligation has no supporting document"

    # --- claim guards: things documents rarely prove ---
    body = re.sub(r"\[NEEDS INPUT[^\]]*\]", "", rec["answer"])
    rec["claim_flags"] = []
    if re.search(r"\b(we|our (system|product|model)|the system)\s+(do(es)? not|don't|never|has no|have no|is not)\b", body, re.I):
        rec["claim_flags"].append("negative claim (e.g. 'we do not…'): documents rarely prove absence — confirm it is true")
    if re.search(r"\bwe (will|plan to|intend to)\b", body, re.I):
        rec["claim_flags"].append("forward commitment: confirm you actually intend to promise this")

    # --- citation verification (the trust feature) ---
    chk = laws.check_citations(rec["answer"], allowed)
    valid_docs = {e["id"] for e in ev}
    cited_docs = set()
    for ref in re.findall(r"\[doc:\s*([^\]]+?)\s*\]", rec["answer"]):
        fname = ref.split("§")[0].strip()
        for part in ref.split(","):
            part = part.strip()
            cited_docs.add(part if "§" in part and part.split("§")[0].strip() else f"{fname} {part}".replace("  ", " "))
    bad_docs = sorted(d for d in cited_docs if d not in valid_docs)
    rec["verification"] = {**chk, "bad_doc_refs": bad_docs}
    flagged = bool(chk["nonexistent"] or chk["unsupported"] or bad_docs)
    if "[NEEDS INPUT" in rec["answer"] or rec["missing"] or "[DRAFT NEEDED]" in rec["answer"]:
        rec["status"] = "needs_input"
    elif flagged:
        rec["status"] = "review"
    elif rec["claim_flags"]:
        rec["status"] = "review"
    elif rec["mode"] == "llm" and not cited_docs:
        rec["status"] = "review"  # company claims with no company citation
    else:
        rec["status"] = "ready"
    return rec


# ---------------------------------------------------------------- rendering

STATUS_LABEL = {"ready": "READY", "needs_input": "NEEDS INPUT", "review": "CHECK CITATIONS"}


def render_markdown(pack: dict) -> str:
    c, gaps, answers = pack["classification"], pack["gaps"], pack["answers"]
    L = [f"# AI Act Evidence Pack — {pack['company']}", "", f"_Generated {pack['date']} · mode: {pack['mode']}_", "",
         f"> {DISCLAIMER}", "", "## 1. Risk classification", "", f"**{c['tier']}**", ""]
    for b in c["basis"]:
        L.append(f"- **{b['cite']}** — {b['why']}")
        if b["quote"]:
            L.append(f"  > “{b['quote']}”")
    for n in c["notes"]:
        L += ["", f"_{n}_"]
    L += ["", "## 2. Readiness against buyer-expected evidence", "",
          "| Obligation | Article | Status | Where we found it |", "|---|---|---|---|"]
    for g in gaps:
        L.append(f"| {g['topic']} | {g['article']} | {g['status']} | {', '.join(g['evidence']) or '—'} |")
    s = pack["summary"]
    L += ["", f"**{s['evidenced']} evidenced · {s['partial']} partial · {s['missing']} missing** of {s['total']} obligations. _Keyword triage of your documents to show where to look first — not a compliance determination._", "",
          "### Fix first", ""]
    for g in [g for g in gaps if g["status"] != "Evidenced"]:
        L.append(f"- **{g['article']} — {g['topic']}** ({g['status']}): {g['ask']}")
    L += ["", "## 3. Questionnaire answers", ""]
    for i, a in enumerate(answers, 1):
        v = a["verification"]
        L += [f"### Q{i}. {a['question']}", "", f"**[{STATUS_LABEL[a['status']]}]**", "", a["answer"], ""]
        if a["missing"]:
            L.append("Missing: " + "; ".join(a["missing"]) + "\n")
        if v["nonexistent"] or v["unsupported"] or v["bad_doc_refs"]:
            L.append(f"⚠ Citation check failed — nonexistent: {v['nonexistent']}, not in evidence: {v['unsupported']}, bad doc refs: {v['bad_doc_refs']}\n")
        for fl in a.get("claim_flags", []):
            L.append(f"⚠ {fl}\n")
        L.append(f"_Law consulted: {', '.join(a['law'])}. Company docs consulted: {', '.join(a['evidence']) or 'none'}._\n")
    return "\n".join(L)


def render_html(pack: dict) -> str:
    e = html.escape
    badge = {"Evidenced": "ok", "Partial": "warn", "Missing": "bad", "ready": "ok", "needs_input": "bad", "review": "warn"}
    rows = "".join(f"<tr><td>{e(g['topic'])}</td><td>{e(g['article'])}</td><td><span class='b {badge[g['status']]}'>{g['status']}</span></td><td>{e(', '.join(g['evidence']) or '—')}</td></tr>" for g in pack["gaps"])
    qa = ""
    for i, a in enumerate(pack["answers"], 1):
        ans = re.sub(r"\[NEEDS INPUT[^\]]*\]", lambda m: f"<mark>{m.group(0)}</mark>", e(a["answer"]))
        qa += (f"<section><h3>Q{i}. {e(a['question'])}</h3><span class='b {badge[a['status']]}'>{STATUS_LABEL[a['status']]}</span>"
               f"<p>{ans}</p><small>Law: {e(', '.join(a['law']))} · Docs: {e(', '.join(a['evidence']) or 'none')}</small></section>")
    basis = "".join(f"<li><b>{e(b['cite'])}</b> — {e(b['why'])}<blockquote>{e(b['quote'])}</blockquote></li>" for b in pack["classification"]["basis"])
    s = pack["summary"]
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Act Evidence Pack — {e(pack['company'])}</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 16px;color:#1b1f24}}
table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left;font-size:14px}}
.b{{padding:2px 8px;border-radius:10px;font-size:12px;font-weight:600}}.ok{{background:#d8f3dc}}.warn{{background:#ffe8a3}}.bad{{background:#ffd0d0}}
blockquote{{margin:.4rem 0;padding-left:.8rem;border-left:3px solid #bbb;color:#444;font-size:14px}}section{{border-top:1px solid #eee;padding:.6rem 0}}
mark{{background:#ffd0d0}}small{{color:#666}}</style>
<h1>AI Act Evidence Pack — {e(pack['company'])}</h1><p><small>{pack['date']} · {e(DISCLAIMER)}</small></p>
<h2>Risk classification</h2><p><b>{e(pack['classification']['tier'])}</b></p><ul>{basis}</ul>
<h2>Readiness</h2><p>{s['evidenced']} evidenced · {s['partial']} partial · {s['missing']} missing of {s['total']}</p>
<table><tr><th>Obligation</th><th>Article</th><th>Status</th><th>Found in</th></tr>{rows}</table>
<h2>Questionnaire answers</h2>{qa}</html>"""


def position_page(pack: dict) -> str:
    """Public 'our AI Act position' draft built ONLY from classification + evidenced items."""
    ok = [g for g in pack["gaps"] if g["status"] == "Evidenced"]
    todo = [g for g in pack["gaps"] if g["status"] != "Evidenced"]
    L = [f"# {pack['company']} — EU AI Act position (DRAFT for counsel review)", "",
         f"**Classification:** {pack['classification']['tier']}", "",
         "## What we already have in place", ""]
    L += [f"- **{g['topic']}** ({g['article']}) — documented in {', '.join(g['evidence'])}" for g in ok] or ["- _(nothing evidenced yet)_"]
    L += ["", "## In progress (do not publish until true)", ""]
    L += [f"- {g['topic']} ({g['article']})" for g in todo]
    L += ["", "_Only publish statements you can back with documents. This page is generated from your own docs; edit before use._"]
    return "\n".join(L)


# ---------------------------------------------------------------- orchestration

def build_pack(docs: str, questionnaire: str, product: str | None = None, use_llm: bool | None = None) -> dict:
    use_llm = llm.available() if use_llm is None else use_llm
    passages = load_passages(docs)
    if not passages:
        raise SystemExit(f"No .md/.txt documents found in {docs}")
    overview = next((p for p in passages if "overview" in p["file"].lower() or "intended" in p["heading"].lower()), passages[0])
    description = product or " ".join(p["text"] for p in passages if p["file"] == overview["file"])
    company = Path(docs).name.replace("_", " ").title()
    first = next((l for l in (Path(docs) / overview["file"]).read_text().splitlines() if l.startswith("# ")), "")
    if "—" in first:
        company = first.lstrip("# ").split("—")[0].strip()

    questions = parse_questions(questionnaire)
    gaps = gap_analysis(passages)
    classification = classify_product(description)
    answers = [draft_answer(q, passages, use_llm, {g["id"]: g for g in gaps}, classification) for q in questions]
    summary = {"total": len(gaps), **{k: sum(g["status"] == v for g in gaps) for k, v in
               {"evidenced": "Evidenced", "partial": "Partial", "missing": "Missing"}.items()}}
    return {"company": company, "date": date.today().isoformat(), "mode": "LLM-assisted" if use_llm else "offline (no LLM)",
            "classification": classification, "gaps": gaps, "summary": summary, "answers": answers,
            "docs": sorted({p["file"] for p in passages})}


def write_outputs(pack: dict, out: str | Path) -> list[Path]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "evidence_pack.md": render_markdown(pack),
        "evidence_pack.html": render_html(pack),
        "evidence_pack.json": json.dumps(pack, indent=2, ensure_ascii=False),
        "ai_act_position.md": position_page(pack),
    }
    for name, content in files.items():
        (out / name).write_text(content, encoding="utf-8")
    with (out / "gaps.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["article", "topic", "status", "what_buyers_expect", "found_in"])
        for g in pack["gaps"]:
            w.writerow([g["article"], g["topic"], g["status"], g["ask"], "; ".join(g["evidence"])])
    return [out / n for n in [*files, "gaps.csv"]]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docs", required=True, help="folder of the vendor's .md/.txt documents")
    ap.add_argument("--questionnaire", required=True, help=".md/.txt (numbered list) or .csv with a 'question' column")
    ap.add_argument("--product", help="override product description used for classification")
    ap.add_argument("--out", default="out")
    ap.add_argument("--no-llm", action="store_true", help="deterministic offline mode")
    a = ap.parse_args()

    pack = build_pack(a.docs, a.questionnaire, a.product, use_llm=False if a.no_llm else None)
    paths = write_outputs(pack, a.out)
    s, ans = pack["summary"], pack["answers"]
    print(f"Classification : {pack['classification']['tier']}")
    print(f"Readiness      : {s['evidenced']} evidenced / {s['partial']} partial / {s['missing']} missing (of {s['total']})")
    print("Answers        : " + ", ".join(f"{sum(x['status']==k for x in ans)} {STATUS_LABEL[k].lower()}" for k in STATUS_LABEL))
    print("Mode           : " + pack["mode"])
    for p in paths:
        print("  wrote", p.relative_to(ROOT) if p.is_relative_to(ROOT) else p)


if __name__ == "__main__":
    main()

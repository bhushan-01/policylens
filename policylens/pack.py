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
  python -m policylens.pack --docs examples/sample_company --questionnaire examples/sample_questionnaire.md
"""

from __future__ import annotations

import argparse
import csv
import re
from datetime import date
from pathlib import Path

from policylens import laws, llm
from policylens.classification import classify_product
from policylens.company import keyword_hits, load_passages, rank_by_meaning
from policylens.obligations import OBLIGATIONS
from policylens.omnibus import OMNIBUS_NOTE
from policylens.paths import ROOT
from policylens.render import STATUS_LABEL, write_outputs
from policylens.search import search


# ---------------------------------------------------------------- gap analysis

def gap_analysis(passages: list[dict], *, use_semantic: bool = True) -> list[dict]:
    """
    Keyword triage of vendor docs against buyer-expected obligations.

    Status stays keyword-based (deterministic, eval-stable). When `use_semantic=True`,
    each row also gets `semantic_near` — passages that *mean* something close to the
    obligation even if keywords missed. That is a look-here hint, not a compliance finding.
    """
    passage_vecs = None
    if use_semantic:
        try:
            from policylens.company import embed_passages, semantic_obligation_hits

            _, passage_vecs = embed_passages(passages)
        except Exception:
            use_semantic = False
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
        semantic_near = []
        if use_semantic and passage_vecs is not None:
            semantic_near = semantic_obligation_hits(
                passages, o["ask"], o["topic"], passage_vecs=passage_vecs
            )
        rows.append({
            "id": o["id"], "article": o["article"], "topic": o["topic"], "status": status,
            "ask": o["ask"], "matched_keywords": matched,
            "evidence": [p["id"] for p, _ in hits[:3]],
            "semantic_near": semantic_near,
            "method": "keyword+semantic" if use_semantic else "keyword",
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

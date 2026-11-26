"""
Evidence Tribunal — adversarial classification that replaces the free-form agent.

Idea: a single chatty agent invents. A tribunal does not.
Four deterministic roles build a *proof ledger* before any prose:

  1. Prosecutor  — charges from keyword + optional semantic promotion + law search
  2. Defense     — finds exclusions in the product text and known legal exceptions
  3. Auditor     — every charge must have a real Article/Annex and a verbatim quote
  4. Clerk       — emits only VERIFIED / CHALLENGED / DROPPED rows; never invents

Optional LLM only narrates the ledger; it cannot add uncitable claims.

  python -m policylens.tribunal "CV screening for HR teams"
  python -m policylens.tribunal --json "..."
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from policylens import laws
from policylens.classification import classify_product
from policylens.search import search

# Defense patterns: product text that weakens a charge (not the same as EXCLUSION stripping).
DEFENSE_PATTERNS = [
    {
        "id": "verification_only",
        "rx": re.compile(r"verif|unlock|authenticat|log.?in|confirm(s|ing)? identity", re.I),
        "targets": {"A1a"},
        "argument": (
            "Product wording suggests biometric VERIFICATION. Annex III 1(a) excludes "
            "systems whose sole purpose is confirming a person is who they claim to be."
        ),
        "cite": "Annex III",
        "marker": "remote biometric identification systems",
    },
    {
        "id": "fraud_detection",
        "rx": re.compile(r"fraud detect|detect(s|ing)? (financial )?fraud", re.I),
        "targets": {"A5b"},
        "argument": (
            "Product wording suggests financial-fraud detection. Annex III 5(b) excepts "
            "systems used solely to detect financial fraud from the creditworthiness high-risk case."
        ),
        "cite": "Annex III",
        "marker": "evaluate the creditworthiness of natural persons",
    },
    {
        "id": "medical_safety_emotion",
        "rx": re.compile(r"medical|safety|therap|diagnos", re.I),
        "targets": {"5f"},
        "argument": (
            "Emotion inference in work/education is banned, but medical or safety reasons "
            "are carved out of Article 5(1)(f). Confirm the exception actually applies."
        ),
        "cite": "Article 5",
        "marker": "to infer emotions",
    },
    {
        "id": "stated_exclusion",
        "rx": re.compile(
            r"not intended (for|to)|not (designed|meant|built) for|out of scope|excluded",
            re.I,
        ),
        "targets": set(),  # applies globally as a caution
        "argument": (
            "The description contains stated exclusions. Exclusions are stripped before "
            "charging, but counsel should confirm marketing text matches real use."
        ),
        "cite": None,
        "marker": None,
    },
]


def _prosecutor(product: str, promote_semantic: bool) -> dict:
    classification = classify_product(product, use_semantic=True, promote_semantic=promote_semantic)
    law_hits = search(f"EU AI Act risk classification for: {product}", top_k=6)
    charges = []
    for b in classification["basis"]:
        if b.get("rule") == "6(2)":
            continue  # supporting cite, attached later
        charges.append({
            "rule": b["rule"],
            "cite": b["cite"],
            "why": b["why"],
            "quote": b["quote"],
            "match": b.get("match", "keyword"),
            "role": "prosecutor",
        })
    return {
        "classification": classification,
        "charges": charges,
        "law_search": [
            {
                "citation": h["citation"],
                "id": h["id"],
                "score": round(h["score"], 3),
                "title": h["title"],
            }
            for h in law_hits
        ],
    }


def _defense(product: str, charges: list[dict]) -> list[dict]:
    charged_rules = {c["rule"] for c in charges}
    motions = []
    for pat in DEFENSE_PATTERNS:
        if not pat["rx"].search(product):
            continue
        if pat["targets"] and not (pat["targets"] & charged_rules):
            continue
        quote = ""
        if pat["cite"] and pat["marker"]:
            quote = laws.quote_around(pat["cite"], pat["marker"], 0, 220)
        motions.append({
            "id": pat["id"],
            "argument": pat["argument"],
            "targets": sorted(pat["targets"]) if pat["targets"] else sorted(charged_rules),
            "cite": pat["cite"],
            "quote": quote,
            "role": "defense",
        })
    # Art 6(3) caution whenever high-risk Annex III is charged
    if any(c["rule"].startswith("A") for c in charges):
        motions.append({
            "id": "art6_3_caution",
            "argument": (
                "Article 6(3) can carve some Annex III systems out of high-risk if they do "
                "not perform profiling of natural persons — but ranking/scoring people usually "
                "is profiling. Do not rely on 6(3) without counsel."
            ),
            "targets": [c["rule"] for c in charges if c["rule"].startswith("A")],
            "cite": "Article 6",
            "quote": laws.quote_around("Article 6", "Notwithstanding the first subparagraph", 0, 181),
            "role": "defense",
            # A caution, not a real defense: it must not downgrade a charge to CHALLENGED.
            "advisory": True,
        })
    return motions


def _audit(charges: list[dict], motions: list[dict]) -> list[dict]:
    """Every surviving claim needs a real cite and a quote that appears in the Act."""
    ledger = []
    challenged = set()
    for m in motions:
        if m.get("advisory"):
            continue  # cautions are shown to the reader but do not weaken a charge
        for t in m.get("targets") or []:
            challenged.add(t)

    for c in charges:
        status = "VERIFIED"
        reasons = []
        if not laws.exists(c["cite"]):
            status = "DROPPED"
            reasons.append(f"cite {c['cite']} does not exist in the Act")
        elif c["quote"]:
            parent = laws.get(c["cite"])
            if parent and c["quote"][:40] not in re.sub(r"\s+", " ", parent["text"]):
                # soft check: quote_around should always be real; flag if truncated oddly
                blob = re.sub(r"\s+", " ", parent["text"])
                snippet = re.sub(r"\s+", " ", c["quote"])[:60]
                if snippet and snippet not in blob:
                    status = "DROPPED"
                    reasons.append("quote not found in cited Article/Annex text")
        else:
            status = "DROPPED"
            reasons.append("no verbatim quote attached")

        if status == "VERIFIED" and c["rule"] in challenged:
            status = "CHALLENGED"
            reasons.append("defense filed a motion against this charge")

        ledger.append({
            "rule": c["rule"],
            "cite": c["cite"],
            "why": c["why"],
            "quote": c["quote"],
            "match": c.get("match", "keyword"),
            "status": status,
            "reasons": reasons,
        })
    # Audit defense cites too
    for m in motions:
        if not m.get("cite"):
            continue
        ok = laws.exists(m["cite"])
        ledger.append({
            "rule": f"defense:{m['id']}",
            "cite": m["cite"],
            "why": m["argument"],
            "quote": m.get("quote") or "",
            "match": "defense",
            "status": "VERIFIED" if ok else "DROPPED",
            "reasons": [] if ok else ["defense cite missing from Act"],
        })
    return ledger


def _verdict(product: str, prosecution: dict, motions: list[dict], ledger: list[dict]) -> dict:
    charge_rows = [r for r in ledger if not str(r["rule"]).startswith("defense:")]
    verified = [r for r in charge_rows if r["status"] == "VERIFIED"]
    challenged = [r for r in charge_rows if r["status"] == "CHALLENGED"]
    dropped = [r for r in charge_rows if r["status"] == "DROPPED"]

    tiers = []
    for r in verified + challenged:
        rid = r["rule"]
        if rid.startswith("5") or rid[0].isdigit():
            tiers.append("PROHIBITED")
        elif rid.startswith("A"):
            tiers.append("HIGH-RISK")
        elif rid.startswith("T"):
            tiers.append("TRANSPARENCY")
        elif rid.startswith("G"):
            tiers.append("GPAI")

    if "PROHIBITED" in tiers:
        finding = "POSSIBLY PROHIBITED — urgent legal review"
    elif "HIGH-RISK" in tiers:
        finding = "HIGH-RISK (charges survived audit)"
    elif "TRANSPARENCY" in tiers:
        finding = "TRANSPARENCY obligations likely"
    elif challenged and not verified:
        finding = "CHARGES CHALLENGED — counsel review before deciding"
    else:
        finding = "No verified Annex III / Article 5 charge — likely minimal risk, confirm"

    confidence = "high" if verified and not challenged else (
        "medium" if verified or challenged else "low"
    )
    near = prosecution["classification"].get("semantic_near") or []

    return {
        "product": product,
        "finding": finding,
        "confidence": confidence,
        "counts": {
            "verified": len(verified),
            "challenged": len(challenged),
            "dropped": len(dropped),
            "defense_motions": len(motions),
            "semantic_near": len(near),
        },
        "surviving_cites": sorted({r["cite"] for r in verified + challenged}),
        "notes": prosecution["classification"].get("notes") or [],
        "disclaimer": (
            "Evidence Tribunal output is not legal advice. Only claims that survived "
            "citation audit are shown as VERIFIED or CHALLENGED."
        ),
    }


def run_tribunal(product: str, *, promote_semantic: bool = False) -> dict:
    product = (product or "").strip()
    if not product:
        raise ValueError("product description required")
    prosecution = _prosecutor(product, promote_semantic=promote_semantic)
    motions = _defense(product, prosecution["charges"])
    ledger = _audit(prosecution["charges"], motions)
    verdict = _verdict(product, prosecution, motions, ledger)
    return {
        "verdict": verdict,
        "ledger": ledger,
        "defense": motions,
        "law_search": prosecution["law_search"],
        "classification": prosecution["classification"],
        "semantic_near": prosecution["classification"].get("semantic_near") or [],
    }


def render_tribunal_markdown(result: dict) -> str:
    v = result["verdict"]
    lines = [
        f"# Evidence Tribunal",
        "",
        f"**Finding:** {v['finding']}",
        f"**Confidence:** {v['confidence']}",
        f"**Product:** {v['product']}",
        "",
        "## Proof ledger",
        "",
        "| Status | Rule | Cite | Why |",
        "|---|---|---|---|",
    ]
    for row in result["ledger"]:
        why = row["why"].replace("|", "/")
        if len(why) > 140:  # cut at a word boundary, never mid-sentence
            why = why[:140].rsplit(" ", 1)[0].rstrip(",;:— -") + "…"
        lines.append(f"| {row['status']} | `{row['rule']}` | {row['cite']} | {why} |")
    if result.get("semantic_near"):
        lines += ["", "## Semantic near-misses (not charged)", ""]
        for n in result["semantic_near"]:
            lines.append(f"- `{n['rule']}` score={n['score']}")
    if result.get("defense"):
        lines += ["", "## Defense motions", ""]
        for m in result["defense"]:
            lines.append(f"- **{m['id']}**: {m['argument']}")
            if m.get("quote"):
                lines.append(f"  > {m['quote'][:280]}")
    lines += ["", "---", "", v["disclaimer"]]
    return "\n".join(lines)


def main(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("product", nargs="*", help="product description")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    ap.add_argument(
        "--promote-semantic",
        action="store_true",
        help="promote semantic near-misses into charges (exploratory; stricter default is off)",
    )
    args = ap.parse_args(argv)
    product = " ".join(args.product).strip() or "CV screening software for hiring"
    result = run_tribunal(product, promote_semantic=args.promote_semantic)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_tribunal_markdown(result))


if __name__ == "__main__":
    main()

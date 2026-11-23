"""
First-pass risk classification from a plain-language product description.

Runs the rule table in `risk_rules.py` (every Annex III area, all Article 5 bans, Article 50, GPAI).
Every rule quotes verbatim law text. Conservative: it flags, it never clears a product.
"""

from __future__ import annotations

import re

from policylens import laws
from policylens.omnibus import OMNIBUS_NOTE
from policylens.risk_rules import RULES


def _quote(cite: str, marker: str) -> str:
    return laws.quote_around(cite, marker, 40, 330)


# Sentences that state what the product is NOT for must not trigger a rule
# ("not intended for promotion decisions" is an exclusion, not a use case).
EXCLUSION = re.compile(r"[^.]*\b(not intended (for|to be used)|not (designed|meant|built) for|is not used (for|in)|excluded|out of scope)\b[^.]*\.?", re.I)


def classify_product(description: str) -> dict:
    """
    Rule-based first pass over all Annex III areas, all Article 5 prohibitions and Article 50.
    Every rule quotes verbatim law text. Conservative: it flags, it never clears a product.
    """
    scanned = EXCLUSION.sub(" ", description)
    hits = [r for r in RULES if r["rx"].search(scanned) and (r.get("also") is None or r["also"].search(scanned))]
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

"""
First-pass risk classification from a plain-language product description.

Runs the rule table in `risk_rules.py` (every Annex III area, all Article 5 bans, Article 50, GPAI).
Every rule quotes verbatim law text. Conservative: it flags, it never clears a product.

Beyond keywords: a semantic near-miss layer compares the description to each rule's intents
(embedding similarity). High-similarity matches are added as charges when they clear a
strict threshold and share meaningful tokens with the rule — catching unusual wording
without inventing law.
"""

from __future__ import annotations

import re

import numpy as np

from policylens import laws
from policylens.omnibus import OMNIBUS_NOTE
from policylens.risk_rules import RULES, rule_intents


def _quote(cite: str, marker: str) -> str:
    return laws.quote_around(cite, marker, 40, 330)


# Sentences that state what the product is NOT for must not trigger a rule
# ("not intended for promotion decisions" is an exclusion, not a use case).
EXCLUSION = re.compile(
    r"[^.]*\b(not intended (for|to be used)|not (designed|meant|built) for|is not used (for|in)|excluded|out of scope)\b[^.]*\.?",
    re.I,
)

# Content words that must overlap before a semantic hit is accepted (anti-false-positive).
STOP = {
    "system", "systems", "used", "using", "natural", "person", "persons", "people",
    "article", "annex", "point", "under", "except", "excepts", "provider", "model",
    "general", "purpose", "possible", "likely", "duties", "obligations", "apply",
}

SEMANTIC_THRESHOLD = 0.58
_INTENT_CACHE: dict[str, np.ndarray] | None = None


def _token_overlap(a: str, b: str) -> int:
    wa = {w for w in re.findall(r"[a-z]{4,}", a.lower()) if w not in STOP}
    wb = {w for w in re.findall(r"[a-z]{4,}", b.lower()) if w not in STOP}
    return len(wa & wb)


def _intent_vectors() -> dict[str, np.ndarray]:
    """One averaged embedding per rule from its intents (lazy, cached)."""
    global _INTENT_CACHE
    if _INTENT_CACHE is not None:
        return _INTENT_CACHE
    from policylens.search import QUERY_PREFIX, load

    model, _, _ = load()
    cache: dict[str, np.ndarray] = {}
    for r in RULES:
        texts = [QUERY_PREFIX + t for t in rule_intents(r)]
        vecs = model.encode(texts, normalize_embeddings=True)
        cache[r["id"]] = np.mean(np.asarray(vecs), axis=0)
        cache[r["id"]] /= max(float(np.linalg.norm(cache[r["id"]])), 1e-9)
    _INTENT_CACHE = cache
    return cache


def semantic_near_misses(description: str, already: set[str], top_k: int = 3) -> list[dict]:
    """
    Embedding near-misses against rule intents. Returns candidate rules with scores.
    Only returns rules not already keyword-matched.
    """
    from policylens.search import QUERY_PREFIX, load

    model, _, _ = load()
    q = model.encode([QUERY_PREFIX + description], normalize_embeddings=True)[0]
    intents = _intent_vectors()
    scored = []
    for r in RULES:
        if r["id"] in already:
            continue
        score = float(intents[r["id"]] @ q)
        if score < SEMANTIC_THRESHOLD:
            continue
        if _token_overlap(description, " ".join(rule_intents(r))) < 1:
            continue
        scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    out = []
    for score, r in scored[:top_k]:
        out.append({
            "rule": r,
            "score": round(score, 3),
            "match": "semantic",
        })
    return out


def classify_product(description: str, *, use_semantic: bool = True, promote_semantic: bool = False) -> dict:
    """
    Rule-based first pass over all Annex III areas, all Article 5 prohibitions and Article 50.
    Every rule quotes verbatim law text. Conservative: it flags, it never clears a product.

    Semantic near-misses are always reported under `semantic_near` when `use_semantic=True`.
    They only become charges when `promote_semantic=True` (tribunal / exploratory mode) —
    the default pack/eval path stays keyword-deterministic.
    """
    scanned = EXCLUSION.sub(" ", description)
    hits = [
        r for r in RULES
        if r["rx"].search(scanned) and (r.get("also") is None or r["also"].search(scanned))
    ]
    match_of = {r["id"]: "keyword" for r in hits}
    near = []
    if use_semantic:
        try:
            near = semantic_near_misses(scanned, {r["id"] for r in hits})
            if promote_semantic:
                for n in near:
                    r = n["rule"]
                    hits.append(r)
                    match_of[r["id"]] = "semantic"
        except Exception:
            near = []  # never fail classification because embeddings are unavailable

    prohibited = [r for r in hits if r["tier"] == "P"]
    high = [r for r in hits if r["tier"] == "H"]
    transp = [r for r in hits if r["tier"] == "T"]
    gpai = [r for r in hits if r["tier"] == "G"]
    basis, notes = [], []

    for r in prohibited + high + transp + gpai:
        basis.append({
            "cite": r["cite"],
            "rule": r["id"],
            "why": r["why"],
            "quote": _quote(r["cite"], r["marker"]),
            "match": match_of.get(r["id"], "keyword"),
        })

    if prohibited:
        tier = "POSSIBLY PROHIBITED — urgent legal review"
        notes.append(
            "Prohibited practices (Article 5) carry the Act's highest penalties. "
            "Narrow exceptions exist; only counsel can confirm whether one applies."
        )
    elif high:
        points = ", ".join(
            sorted(
                {
                    r["id"][1:]
                    .replace("a", "(a)")
                    .replace("b", "(b)")
                    .replace("c", "(c)")
                    .replace("d", "(d)")
                    for r in high
                }
            )
        )
        tier = f"HIGH-RISK (Annex III point {points})"
    elif transp:
        tier = "TRANSPARENCY obligations likely (Article 50)"
    else:
        tier = "No Annex III / Article 5 trigger found by keyword rules — likely minimal risk, confirm"

    if high:
        basis.append({
            "cite": "Article 6",
            "rule": "6(2)",
            "why": (
                "Article 6(2): Annex III systems are high-risk. The Article 6(3) "
                "'not high-risk' derogation does not apply where the system performs "
                "profiling of natural persons."
            ),
            "quote": laws.quote_around("Article 6", "Notwithstanding the first subparagraph", 0, 181),
            "match": "keyword",
        })
        notes.append(
            "Ranking, scoring or predicting things about people generally counts as "
            "profiling, so do not rely on the Article 6(3) derogation without counsel."
        )
        notes.append(OMNIBUS_NOTE)
    ids = {r["id"] for r in hits}
    if "A1a" in ids and re.search(r"verif|unlock|authenticat|log.?in", description, re.I):
        notes.append(
            "Annex III 1(a) excludes biometric VERIFICATION whose sole purpose is "
            "confirming a person is who they claim to be. Confirm yours is verification only."
        )
    if "A5b" in ids and re.search(r"fraud", description, re.I):
        notes.append(
            "Annex III 5(b) excepts systems used to detect financial fraud. "
            "Credit scoring itself stays high-risk."
        )
    if high and transp:
        notes.append("Article 50 transparency duties apply in addition to the high-risk requirements.")
    if gpai:
        notes.append(
            "If you train a general-purpose AI model you may be a provider under Article 53. "
            "Using someone else's model makes you a downstream provider or deployer instead."
        )
    if any(match_of.get(i) == "semantic" for i in ids):
        notes.append(
            "Some flags came from semantic near-miss matching (unusual wording). "
            "Confirm the intended purpose against the quoted Annex / Article text."
        )
    elif near:
        notes.append(
            "Semantic near-misses (unusual wording to investigate, not yet charged): "
            + ", ".join(f"{n['rule']['id']} ({n['score']})" for n in near[:3])
            + "."
        )
    return {
        "tier": tier,
        "basis": basis,
        "notes": notes,
        "rule_ids": sorted(ids),
        "semantic_near": [{"rule": n["rule"]["id"], "score": n["score"]} for n in near],
        "disclaimer": (
            "Keyword first pass with semantic near-miss hints; verify the intended "
            "purpose against the Annex III / Article 5 wording."
        ),
    }

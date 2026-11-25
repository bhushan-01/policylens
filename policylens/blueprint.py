"""
Fix-first document blueprints for Missing / Partial obligations.

When gap analysis says "Missing", vendors still ask: "what do I write?"
This module turns each obligation into a concrete outline a buyer expects —
anchored to the real Article, never inventing that the vendor already has it.
"""

from __future__ import annotations

from policylens.obligations import OBLIGATIONS, BY_ID

# Outline sections a procurement team typically wants to see. Wording is ours;
# the Article text remains the authority.
BLUEPRINTS: dict[str, list[str]] = {
    "risk_mgmt": [
        "Scope and intended purpose of the AI system",
        "Foreseeable misuse scenarios and residual risks",
        "Risk acceptance criteria and update cadence",
        "Link to human oversight and post-market monitoring",
    ],
    "data_gov": [
        "Training / validation / test data provenance",
        "Bias examination method and findings",
        "Mitigations for detected bias",
        "Data retention and access controls",
    ],
    "tech_doc": [
        "System architecture and model description (Annex IV)",
        "Design specifications and development choices",
        "Change control for model / data updates",
        "Version history and responsible owners",
    ],
    "logging": [
        "Events logged automatically (inputs, outputs, overrides)",
        "Retention period and integrity controls",
        "Who can access logs and for what purpose",
        "How logs support post-market monitoring",
    ],
    "instructions": [
        "Capabilities and limitations for deployers",
        "Accuracy metrics and operating conditions",
        "Human oversight measures deployers must apply",
        "Contact path for serious incidents",
    ],
    "oversight": [
        "How a person can interpret system output",
        "Override / stop mechanisms",
        "When human review is mandatory",
        "Training for oversight staff",
    ],
    "accuracy": [
        "Declared accuracy / error metrics",
        "Robustness and adversarial testing",
        "Cybersecurity controls (e.g. access, encryption)",
        "Evaluation schedule",
    ],
    "qms": [
        "Design and testing process",
        "Change control and release gates",
        "Roles and accountability",
        "Document control",
    ],
    "conformity": [
        "Conformity assessment route chosen",
        "Status (planned / in progress / completed)",
        "Notified body involvement if any",
        "Declaration of conformity pointer",
    ],
    "registration": [
        "EU database registration status",
        "System identifier / registration number",
        "Responsible person for updates",
    ],
    "post_market": [
        "Performance signals collected after deployment",
        "Drift / override-rate monitoring",
        "Review cadence and owners",
        "Escalation into risk management",
    ],
    "incidents": [
        "Definition of a serious incident for this system",
        "Detection and investigation steps",
        "Notification timeline to authorities",
        "Remediation and customer communication",
    ],
    "literacy": [
        "Staff AI literacy training plan",
        "Deployer operator onboarding materials",
        "How literacy is verified / refreshed",
    ],
    "explanation": [
        "What an affected person can be told",
        "Which factors the system uses (at a usable level)",
        "How deployers generate an explanation",
        "Limits of the explanation",
    ],
}


def blueprint_for(obligation_id: str) -> dict | None:
    o = BY_ID.get(obligation_id)
    if not o:
        return None
    return {
        "id": o["id"],
        "article": o["article"],
        "topic": o["topic"],
        "ask": o["ask"],
        "sections": BLUEPRINTS.get(obligation_id, ["Describe current practice with evidence."]),
        "note": (
            f"[NEEDS INPUT] Draft this document from your real practice. "
            f"Do not claim {o['article']} compliance until the content exists."
        ),
    }


def blueprints_for_gaps(gaps: list[dict]) -> list[dict]:
    """Blueprints for every gap that is not fully Evidenced — fix-first order."""
    order = {"Missing": 0, "Partial": 1, "Evidenced": 2}
    todo = sorted(
        [g for g in gaps if g["status"] != "Evidenced"],
        key=lambda g: (order.get(g["status"], 9), g["article"]),
    )
    out = []
    for g in todo:
        bp = blueprint_for(g["id"])
        if bp:
            bp["status"] = g["status"]
            out.append(bp)
    return out


def all_obligation_ids() -> list[str]:
    return [o["id"] for o in OBLIGATIONS]

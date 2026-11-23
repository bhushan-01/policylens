"""
What a buyer's procurement team expects a *provider* of a high-risk AI system
(Annex III point 4: recruitment / worker management) to be able to evidence.

Each obligation is anchored to a real Article. `keywords` are used to look for
evidence in the vendor's own documents; `ask` is the plain-language evidence a
buyer will typically request (our wording — the Article text is the authority).
"""

from __future__ import annotations

OBLIGATIONS = [
    {"id": "risk_mgmt", "article": "Article 9", "topic": "Risk management system",
     "ask": "A documented, continuously updated risk management process covering foreseeable misuse and residual risk.",
     "keywords": ["risk management", "risk assessment", "risk register", "residual risk", "misuse"]},
    {"id": "data_gov", "article": "Article 10", "topic": "Data and data governance",
     "ask": "Training/validation/testing data provenance, bias examination and mitigation.",
     "keywords": ["training data", "data governance", "bias", "fairness", "data provenance", "representative"]},
    {"id": "tech_doc", "article": "Article 11", "topic": "Technical documentation (Annex IV)",
     "ask": "Technical documentation drawn up before market placement and kept up to date (Annex IV contents).",
     "keywords": ["technical documentation", "annex iv", "system architecture", "model card", "design specification"]},
    {"id": "logging", "article": "Article 12", "topic": "Record-keeping / automatic logging",
     "ask": "Automatic event logging over the system's lifetime, enabling traceability and monitoring.",
     "keywords": ["logging", "audit log", "audit trail", "event log", "log retention", "record-keeping"]},
    {"id": "instructions", "article": "Article 13", "topic": "Transparency and instructions for use",
     "ask": "Instructions for use giving deployers the system's capabilities, limits, accuracy and oversight measures.",
     "keywords": ["instructions for use", "user guide", "deployer", "limitations", "intended purpose"]},
    {"id": "oversight", "article": "Article 14", "topic": "Human oversight",
     "ask": "Design measures that let natural persons oversee, interpret, override or stop the system.",
     "keywords": ["human oversight", "human review", "override", "human-in-the-loop", "final decision"]},
    {"id": "accuracy", "article": "Article 15", "topic": "Accuracy, robustness, cybersecurity",
     "ask": "Declared accuracy metrics, robustness measures and cybersecurity controls.",
     "keywords": ["accuracy", "robustness", "cybersecurity", "penetration test", "soc 2", "iso 27001", "evaluation"]},
    {"id": "qms", "article": "Article 17", "topic": "Quality management system",
     "ask": "A written quality management system covering design, testing, change control and accountability.",
     "keywords": ["quality management", "qms", "change control", "iso 9001", "release process"]},
    {"id": "conformity", "article": "Article 43", "topic": "Conformity assessment",
     "ask": "Status of the conformity assessment procedure followed before placing the system on the market.",
     "keywords": ["conformity assessment", "conformity", "ce marking", "declaration of conformity", "notified body"]},
    {"id": "registration", "article": "Article 49", "topic": "Registration in the EU database",
     "ask": "Registration of the system in the EU database for high-risk systems.",
     "keywords": ["eu database", "registered", "registration"]},
    {"id": "post_market", "article": "Article 72", "topic": "Post-market monitoring",
     "ask": "A post-market monitoring plan that actively collects and analyses performance data over the lifetime.",
     "keywords": ["post-market", "monitoring plan", "drift", "override rate", "score distribution"]},
    {"id": "incidents", "article": "Article 73", "topic": "Serious incident reporting",
     "ask": "A procedure to detect, investigate and report serious incidents to market surveillance authorities.",
     "keywords": ["serious incident", "incident report", "incident response", "notify authorit"]},
    {"id": "literacy", "article": "Article 4", "topic": "AI literacy",
     "ask": "Measures ensuring staff and deployers' operators have sufficient AI literacy.",
     "keywords": ["ai literacy", "training for", "onboarding", "customer training"]},
    {"id": "explanation", "article": "Article 86", "topic": "Right to explanation of individual decisions",
     "ask": "Ability for deployers to give affected persons a clear explanation of the system's role in a decision.",
     "keywords": ["explanation", "explainab", "top factors", "feature importance", "explain a ", "explain to"]},
]

BY_ID = {o["id"]: o for o in OBLIGATIONS}

"""
Rule table for the first-pass risk classification, covering every Annex III area and every
Article 5 prohibition, plus Article 50 transparency cases.

Each rule points at an Article/Annex and a `marker`: verbatim text in the Act that gets quoted
back to the user. `evals/evidence.py` checks that every marker really appears in the law, so a
rule can never quote something the Act does not say.

Conservative by design: a match means "this needs a look", never "you are compliant".
"""

from __future__ import annotations

import re

R = re.compile
I = re.I

WORK_EDU = R(r"work|employee|staff|worker|student|school|classroom|university|interview|candidate|office|call.?cent", I)

# tier: P = prohibited (Art 5), H = high-risk (Annex III), T = transparency (Art 50)
RULES = [
    # ---- Article 5: prohibited practices
    dict(id="5a", tier="P", cite="Article 5", rx=R(r"subliminal|dark pattern|manipulat(e|es|ive|ing) (user|people|customer|behavio)", I),
         marker="deploys subliminal techniques", why="Possible manipulative/subliminal technique — Article 5(1)(a)."),
    dict(id="5b", tier="P", cite="Article 5", rx=R(r"exploit(s|ing)? (the )?(vulnerab|elderly|child|kids|disab)|target(s|ing)? (children|the elderly|vulnerable)", I),
         marker="exploits any of the vulnerabilities", why="Possible exploitation of vulnerabilities (age, disability, social/economic situation) — Article 5(1)(b)."),
    dict(id="5c", tier="P", cite="Article 5", rx=R(r"social scor|social credit|rate (citizens|people) (by|on) (their )?behaviou?r", I),
         marker="based on their social behaviour", why="Social scoring — Article 5(1)(c)."),
    dict(id="5d", tier="P", cite="Article 5", rx=R(r"predict\w*.{0,40}(commit|crime|criminal|re-?offend)|crime prediction|predictive policing|forecast\w*.{0,40}(offend|crime)|who will (commit|re-?offend)", I),
         marker="risk of a natural person committing a criminal offence", why="Predicting criminal offences from profiling — Article 5(1)(d).",
         intents=["predict who will commit a crime", "forecast reoffending risk"]),
    dict(id="5e", tier="P", cite="Article 5", rx=R(r"scrap\w*.{0,30}(face|facial|images|photos)|facial recognition database|face database", I),
         marker="untargeted scraping of facial images", why="Building facial-recognition databases by untargeted scraping — Article 5(1)(e)."),
    dict(id="5f", tier="P", cite="Article 5", rx=R(r"emotion|facial expression|stress level|mood", I), also=WORK_EDU,
         marker="to infer emotions", why="Inferring emotions in the workplace or education — prohibited by Article 5(1)(f), except for medical or safety reasons."),
    dict(id="5g", tier="P", cite="Article 5", rx=R(r"biometric categori[sz]|infer(s|ring)? (a person's |their )?(race|ethnic|religio|political|sexual orientation|trade union).{0,40}(face|voice|biometric)", I),
         marker="biometric categorisation systems that categorise", why="Biometric categorisation inferring sensitive traits — Article 5(1)(g)."),
    dict(id="5h", tier="P", cite="Article 5", rx=R(r"real.?time (remote )?(biometric|facial)|live (facial|face) recognition", I), also=R(r"police|law enforcement|public (space|area)", I),
         marker="real-time", why="Real-time remote biometric identification for law enforcement in public spaces is prohibited except in narrow cases — Article 5(1)(h)."),
    # ---- Annex III: high-risk areas
    dict(id="A1a", tier="H", cite="Annex III", rx=R(r"remote biometric|facial recognition|face recognition|identify (people|individuals|persons) (in|from|on) (cctv|camera|a crowd|video)", I),
         marker="remote biometric identification systems", why="Annex III point 1(a): remote biometric identification (verification-only is excluded)."),
    dict(id="A1b", tier="H", cite="Annex III", rx=R(r"biometric categori[sz]", I),
         marker="biometric categorisation, according to sensitive", why="Annex III point 1(b): biometric categorisation by sensitive attributes."),
    dict(id="A1c", tier="H", cite="Annex III", rx=R(r"\bemotion", I),
         marker="used for emotion recognition", why="Annex III point 1(c): emotion recognition systems are high-risk (and prohibited in work/education under Article 5(1)(f))."),
    dict(id="A2", tier="H", cite="Annex III", rx=R(r"(road traffic|traffic (control|management)|power grid|electricity grid|water supply|gas network|district heating|critical infrastructure)", I),
         marker="Critical infrastructure", why="Annex III point 2: safety components in critical infrastructure."),
    dict(id="A3a", tier="H", cite="Annex III", rx=R(r"(school|university|college|course|programme) (admission|enrol)|admission(s)? (decision|scor|rank)|assign(s|ing)? students", I),
         marker="determine access or admission", why="Annex III point 3(a): access/admission to education."),
    dict(id="A3b", tier="H", cite="Annex III", rx=R(r"(auto(mated|matic)?[- ])?grad(e|es|ing)( of)? (student|essay|exam|assignment|test)s?|learning outcome|score (student|essay|exam)s?|assess(es|ing)? student", I),
         marker="evaluate learning outcomes", why="Annex III point 3(b): evaluating learning outcomes."),
    dict(id="A3d", tier="H", cite="Annex III", rx=R(r"proctor|cheating (detection|during)|detect(s|ing)? cheating", I),
         marker="prohibited behaviour of students during tests", why="Annex III point 3(d): proctoring / detecting prohibited behaviour in tests."),
    dict(id="A4a", tier="H", cite="Annex III",
         rx=R(r"recruit|hiring|\bhire\b|candidate|applicant|\bcvs?\b|resume|résumé|job (ad|post|applic)|interview|talent (acquisition|screening|matching)|shortlist|applicant ranking|\bats\b|screen(s|ing)? (job )?applicants", I),
         marker="recruitment or selection of natural persons", why="Annex III point 4(a): recruitment and selection.",
         intents=["talent acquisition ranking", "applicant shortlisting for jobs", "CV parsing for recruiters"]),
    dict(id="A4b", tier="H", cite="Annex III",
         rx=R(r"promotion|terminat|performance (review|evaluation|monitor)|monitor(ing)? (employee|worker)|task allocation|workforce (monitor|analytics)|dismiss(al|ing)? (employee|staff|worker)|fire (employee|staff)", I),
         marker="decisions affecting terms of work-related relationships", why="Annex III point 4(b): decisions on work relationships, promotion, termination, monitoring.",
         intents=["employee promotion decisions", "workforce performance monitoring"]),
    dict(id="A5a", tier="H", cite="Annex III", rx=R(r"(benefit|welfare|social assistance|public (service|assistance)).{0,40}eligib|eligib.{0,40}(benefit|welfare|social assistance)", I),
         marker="eligibility of natural persons for essential public assistance", why="Annex III point 5(a): public benefits eligibility."),
    dict(id="A5b", tier="H", cite="Annex III", rx=R(r"credit ?scor|creditworth|loan (approval|decision|underwrit|eligib)|assess(es|ing)? credit", I),
         marker="evaluate the creditworthiness of natural persons", why="Annex III point 5(b): creditworthiness (fraud detection is excepted)."),
    dict(id="A5c", tier="H", cite="Annex III", rx=R(r"(life|health) insurance.{0,30}(pric|risk|premium)|(pric|risk|premium).{0,30}(life|health) insurance", I),
         marker="life and health insurance", why="Annex III point 5(c): life and health insurance risk/pricing."),
    dict(id="A5d", tier="H", cite="Annex III", rx=R(r"emergency call|dispatch(ing)? (of )?(emergency|ambulance|police|fire)|patient triage|triage", I),
         marker="emergency calls by natural persons", why="Annex III point 5(d): emergency call evaluation, dispatch and triage."),
    dict(id="A6", tier="H", cite="Annex III", rx=R(r"(police|law enforcement).{0,60}(risk|polygraph|evidence|profil|offend)|polygraph|lie detect", I),
         marker="Law enforcement", why="Annex III point 6: law-enforcement uses."),
    dict(id="A7", tier="H", cite="Annex III", rx=R(r"asylum|visa (application|decision)|border control|immigration|residence permit|irregular migration", I),
         marker="Migration, asylum and border control", why="Annex III point 7: migration, asylum and border control."),
    dict(id="A8", tier="H", cite="Annex III", rx=R(r"\bcourts?\b|judicial|\bjudges?\b|legal ruling|dispute resolution|\belections?\b|\bvoters?\b|voting behaviou?r", I),
         marker="Administration of justice and democratic processes", why="Annex III point 8: justice and democratic processes."),
    # ---- Article 50: transparency
    dict(id="T1", tier="T", cite="Article 50", rx=R(r"chatbot|virtual assistant|conversational|talks? to (users|customers)|customer support bot|ai (that )?chats? with|conversational agent", I),
         marker="informed that they are interacting", why="Interacts directly with people: Article 50(1) disclosure duty.",
         intents=["customer-facing AI chat assistant"]),
    dict(id="T2", tier="T", cite="Article 50", rx=R(r"deepfake|synthetic (image|video|audio|media)|generat(e|es|ed|ing) (image|video|audio)s?|text-to-(image|video|speech)|voice clon", I),
         marker="synthetic audio, image, video or text content", why="Generates synthetic media: Article 50(2) marking and Article 50(4) deepfake disclosure.",
         intents=["AI-generated deepfake video"]),
    # ---- General-purpose AI models
    dict(id="G1", tier="G", cite="Article 53", rx=R(r"foundation model|general-purpose ai model|train(s|ing)? (our own|a|an|its own)? ?(large language model|llm|foundation model)", I),
         marker="general-purpose AI model", why="Provider of a general-purpose AI model: Article 53 obligations may apply.",
         intents=["we train our own large language model"]),
]

# Short phrases used by the semantic near-miss layer (classification.py).
def rule_intents(rule: dict) -> list[str]:
    base = [rule["why"], rule["marker"]]
    return base + list(rule.get("intents") or [])

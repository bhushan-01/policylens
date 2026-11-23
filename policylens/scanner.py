"""
PolicyLens code scanner — flag EU AI Act gaps while you build (heuristic, evidence-linked).

  python -m policylens.scanner path/to/repo

Each finding names the file and line, the Article it relates to (checked to exist in the
Act), why it matters, and a concrete fix. This is a smoke detector, not an audit: it finds
patterns that deserve a human look. It never says a system is compliant.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from policylens import laws

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".next", "data"}
EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".md", ".txt"}
CODE_EXTS = EXTS - {".md", ".txt"}

AI_CALL = re.compile(r"openai|anthropic|chat\.completions|ChatCompletion|messages\.create|langchain|transformers|\.predict\(|model\.fit", re.I)
DISCLOSURE = re.compile(r"(you are|you're|you’re) (chatting|talking|speaking|interacting) with an? (ai|bot|virtual|assistant)|ai[- ](generated|assistant|powered)|powered by ai|i am an ai|i'm an ai", re.I)
LOGGING = re.compile(r"\blogging\b|\blogger\b|structlog|loguru|audit[_ ]?log|winston|log4j|slf4j", re.I)
AUTO_DECISION = re.compile(r"auto[_-]?(reject|decline|approve|hire|terminate)|reject_candidate|automatic(ally)? (reject|decline)", re.I)
HUMAN_STEP = re.compile(r"human[_-]?(review|in[_-]the[_-]loop|approval)|manual[_-]?review|recruiter[_-]?(confirm|approve)|require_?approval|override", re.I)
EMOTION_BIOMETRIC = re.compile(r"deepface|face_recognition|affectiva|emotion|facial[_ ]expression|voice[_ ]stress|\bfer\b|biometric", re.I)
HIRING = re.compile(r"resume|résumé|\bcv\b|candidate|applicant|recruit|hiring", re.I)
PROTECTED_FEATURE = re.compile(r"[\"'](gender|sex|ethnicity|race|religion|age|nationality|disability)[\"']", re.I)
INCIDENT = re.compile(r"incident", re.I)


def _files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in EXTS and not (set(p.relative_to(root).parts) & SKIP_DIRS):
            try:
                if p.stat().st_size < 300_000:
                    yield p, p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue


def _find(rx: re.Pattern, text: str):
    return [text.count("\n", 0, m.start()) + 1 for m in rx.finditer(text)]


def scan(path: str | Path) -> dict:
    root = Path(path).resolve()
    files = list(_files(root))
    findings: list[dict] = []

    def add(cite, severity, rule, file, line, why, fix):
        assert laws.exists(cite), cite  # never emit a citation that isn't in the Act
        findings.append({"cite": cite, "severity": severity, "rule": rule,
                         "where": f"{file}:{line}" if line else file, "why": why, "fix": fix})

    all_code = [(p, t) for p, t in files if p.suffix.lower() in CODE_EXTS]
    ai_files = [(p, t) for p, t in all_code if AI_CALL.search(t)]
    any_disclosure = any(DISCLOSURE.search(t) for _, t in files)
    any_logging = any(LOGGING.search(t) for _, t in all_code)
    any_human = any(HUMAN_STEP.search(t) for _, t in all_code)
    hiring_hits = [(p, _find(HIRING, t)) for p, t in all_code if HIRING.search(t)]
    rel = lambda p: str(p.relative_to(root))

    # Employment use case => high-risk signal (Annex III point 4)
    if hiring_hits and ai_files:
        p, lines = hiring_hits[0]
        add("Annex III", "high", "employment-use-case", rel(p), lines[0],
            "Code handles candidates/applicants and uses AI or scoring: recruitment/selection systems are listed in Annex III point 4(a), so Article 6(2) makes them high-risk.",
            "Treat as high-risk: write down intended purpose, then start technical documentation (Article 11) and a risk process (Article 9).")

    for p, t in all_code:
        for ln in _find(EMOTION_BIOMETRIC, t)[:1]:
            add("Article 5", "critical", "emotion-or-biometric", rel(p), ln,
                "Emotion or biometric analysis library/term found. Article 5(1)(f) prohibits inferring emotions in the workplace and education (narrow medical/safety exception); biometric identification and categorisation are restricted elsewhere in the Act.",
                "Remove it, or get legal review before any use on employees or candidates.")
        for ln in _find(AUTO_DECISION, t)[:1]:
            if not HUMAN_STEP.search(t):
                add("Article 14", "high", "automated-decision-no-human", rel(p), ln,
                    "Automatic reject/approve logic with no human review or override step nearby. High-risk systems must be designed so people can oversee, interpret and override the output.",
                    "Make the model advisory: require a named person to confirm any adverse decision and log who did.")
        for ln in _find(PROTECTED_FEATURE, t)[:1]:
            if re.search(r"feature|column|input|train|X\b", t, re.I):
                add("Article 10", "medium", "protected-attribute-as-feature", rel(p), ln,
                    "A protected attribute appears in feature or data code. Article 10 requires examining and mitigating bias in training and input data.",
                    "Remove it from model inputs, keep it only in a separate fairness-test set, and record the bias test.")

    # Chat interaction with no AI disclosure anywhere
    if ai_files and not any_disclosure:
        p, t = ai_files[0]
        add("Article 50", "medium", "no-ai-disclosure", rel(p), _find(AI_CALL, t)[0],
            "The app calls an AI model but nothing tells users they are talking to AI. Article 50(1) requires people to be informed when they interact with an AI system, unless obvious.",
            "Show a clear 'You are chatting with an AI assistant' notice in the UI before the first message.")

    # No logging around AI use
    if ai_files and not any_logging:
        p, t = ai_files[0]
        add("Article 12", "high" if hiring_hits else "low", "no-event-logging", rel(p), _find(AI_CALL, t)[0],
            "AI calls are made but no logging/audit-trail code exists. High-risk systems must technically allow automatic recording of events over their lifetime.",
            "Log each model call: timestamp, input reference, model version, output, and any human override. Decide a retention period.")

    # High-risk signal but no incident process in docs
    if hiring_hits and not any(INCIDENT.search(t) for _, t in files):
        add("Article 73", "medium", "no-incident-procedure", "(repo-wide)", 0,
            "No incident-handling mention in code or docs. Providers of high-risk systems must report serious incidents to authorities.",
            "Write a one-page incident procedure: who detects, who decides, how and when authorities and customers are notified.")

    if hiring_hits and not any_human and not any(f["rule"] == "automated-decision-no-human" for f in findings):
        add("Article 14", "low", "no-human-oversight-mechanism", "(repo-wide)", 0,
            "Hiring-related code with no visible review/override mechanism.",
            "Document or build how a recruiter reviews, overrides and can stop the system.")

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: order[f["severity"]])
    return {"root": str(root), "files_scanned": len(files), "findings": findings,
            "note": "Heuristic pattern scan. Absence of findings is not evidence of compliance. Not legal advice."}


def render(result: dict) -> str:
    L = [f"PolicyLens code scan — {result['files_scanned']} files, {len(result['findings'])} findings", ""]
    for f in result["findings"]:
        L += [f"[{f['severity'].upper()}] {f['cite']} — {f['rule']}  ({f['where']})",
              f"   why: {f['why']}", f"   fix: {f['fix']}", ""]
    L.append(result["note"])
    return "\n".join(L)


def main():
    target = next((a for a in sys.argv[1:] if not a.startswith("--")), ".")
    res = scan(target)
    print(json.dumps(res, indent=2) if "--json" in sys.argv else render(res))


if __name__ == "__main__":
    main()

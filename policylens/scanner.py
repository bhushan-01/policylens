"""
PolicyLens code scanner — flag EU AI Act gaps while you build (heuristic, evidence-linked).

  python -m policylens.scanner path/to/repo

Each finding names the file and line, the Article it relates to (checked to exist in the
Act), why it matters, and a concrete fix. This is a smoke detector, not an audit: it finds
patterns that deserve a human look. It never says a system is compliant.

Detectors look at what the code does (imports, names used in code; see `codefacts.py`),
so a comment or a string that merely mentions "emotion" is not a finding.
Silence one line with a comment:  # policylens: ignore[rule-name]
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import replace
from pathlib import Path

from policylens import laws
from policylens.codefacts import Facts, extract, imports_any, words

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".next", "data"}
EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".md", ".txt"}
CODE_EXTS = EXTS - {".md", ".txt"}

AI_LIBS = {"openai", "anthropic", "@anthropic-ai/sdk", "@ai-sdk", "ai", "langchain", "@langchain", "llama_index",
           "transformers", "litellm", "google.generativeai", "google.genai", "@google/generative-ai",
           "@google/genai", "mistralai", "cohere", "ollama", "sklearn", "torch", "tensorflow", "keras", "xgboost"}
EMOTION_LIBS = {"deepface", "fer", "affectiva", "hume", "@humeai", "hsemotion", "feat"}
BIOMETRIC_LIBS = {"face_recognition", "insightface", "face-api.js", "@vladmandic/face-api"}
LOGGING_LIBS = {"structlog", "loguru", "winston", "pino", "log4j", "org.slf4j", "org.apache.logging", "log/slog"}
LOG_CALL = re.compile(r"\b(?:logging|logger)\.(?:info|debug|warning|error|exception|critical)\b")

EMOTION_NAME = {"emotion", "emotions", "biometric", "biometrics"}
DISCLOSURE = re.compile(r"(you are|you're|you’re) (chatting|talking|speaking|interacting) with an? (ai|bot|virtual|assistant)|ai[- ](generated|assistant|powered)|powered by ai|i am an ai|i'm an ai", re.I)
LOG_NAME = re.compile(r"^(logger|audit_?log\w*|log_(event|decision|call))$", re.I)
AUTO_DECISION = re.compile(r"auto(matically)?_?(reject|decline|approve|hire|terminate)|^reject_?candidate", re.I)
HUMAN_STEP = re.compile(r"human_?(review|in_?the_?loop|approv)|manual_?review|(recruiter|reviewer)_?(confirm|approv|review)|require_?approval|\boverride\b", re.I)
STRONG_HIRING = {"applicant", "applicants", "recruit", "recruiter", "recruiters", "recruiting", "recruitment", "hiring", "jobseeker"}
SOFT_HIRING = {"resume", "resumes", "cv", "cvs", "candidate", "candidates"}  # also "resume session", "cv2", "cross-validation"
HIRING_CONTEXT = {"screen", "screening", "rank", "ranking", "parse", "parser", "shortlist", "score", "job"}
PROTECTED = {"gender", "sex", "ethnicity", "race", "religion", "age", "nationality", "disability"}
FEATURE_NAME = re.compile(r"feature|column|input|train|^x$|_x$", re.I)
INCIDENT = re.compile(
    r"serious incident|incident (response|report|procedure|handling|notification)|report(?:ing)? (an )?incident",
    re.I,
)
IGNORE = re.compile(r"policylens:\s*ignore(?:\[([\w, -]+)\])?")


def _files(root: Path):
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            p = Path(dirpath) / name
            # Symlinks are skipped: an untrusted repo must not make us read files outside it.
            if p.suffix.lower() not in EXTS or p.is_symlink() or not p.is_file():
                continue
            try:
                if p.stat().st_size < 300_000:
                    yield p, p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue


def _ignored(source_line: str, rule: str) -> bool:
    m = IGNORE.search(source_line)
    return bool(m and (not m[1] or rule in [r.strip() for r in m[1].split(",")]))


def _visible(facts: Facts, source: list[str], rule: str) -> Facts:
    """Facts without the lines silenced for `rule`, so a later unsilenced match is still found."""
    off = {n for n, text in enumerate(source, 1) if _ignored(text, rule)}
    if not off:
        return facts
    return replace(facts,
                   imports={m: n for m, n in facts.imports.items() if n not in off},
                   identifiers=[x for x in facts.identifiers if x[1] not in off],
                   assigned_strings=[x for x in facts.assigned_strings if x[2] not in off])


def _hiring_line(facts: Facts) -> int | None:
    for name, line in facts.identifiers:
        w = set(words(name))
        if w & STRONG_HIRING or (w & SOFT_HIRING and w & HIRING_CONTEXT):
            return line
    return None


def _named(facts: Facts, rx: re.Pattern) -> int | None:
    return next((line for name, line in facts.identifiers if rx.search(name)), None)


def _unreviewed_decision(facts: Facts) -> int | None:
    """First automatic reject/approve with no human step in the same function (else same file)."""
    for name, line in facts.identifiers:
        if not AUTO_DECISION.search(name):
            continue
        spans = [s for s in facts.functions if s[0] <= line <= s[1]]
        lo, hi = max(spans) if spans else (1, len(facts.code_lines))  # innermost function
        if not any(lo <= n <= hi and HUMAN_STEP.search(other) for other, n in facts.identifiers):
            return line
    return None


def scan(path: str | Path) -> dict:
    root = Path(path).resolve()
    files = list(_files(root))
    code = [(str(p.relative_to(root)), t, extract(t, p.suffix)) for p, t in files if p.suffix.lower() in CODE_EXTS]
    lines_of = {name: text.split("\n") for name, text, _ in code}
    findings: list[dict] = []

    def add(cite, severity, rule, file, line, why, fix):
        assert laws.exists(cite), cite  # never emit a citation that isn't in the Act
        snippet = ""
        if line:
            source_line = lines_of[file][line - 1]
            if _ignored(source_line, rule):  # covers repo-wide rules, which point at one example line
                return
            snippet = source_line.strip()[:200]
        findings.append({"cite": cite, "severity": severity, "rule": rule,
                         "where": f"{file}:{line}" if line else file, "file": file, "line": line,
                         "snippet": snippet, "why": why, "fix": fix})

    def seen(rule):
        return [(name, _visible(f, lines_of[name], rule)) for name, _, f in code]

    ai = []  # (file, line of the AI import)
    for name, _, f in code:
        hit = imports_any(f, AI_LIBS | EMOTION_LIBS | BIOMETRIC_LIBS)
        if hit:
            ai.append((name, hit[1]))
    hiring = [(name, line) for name, f in seen("employment-use-case") if (line := _hiring_line(f))]
    any_disclosure = any(DISCLOSURE.search(t) for _, t in files)
    any_logging = any(
        imports_any(f, LOGGING_LIBS)
        or any(LOG_NAME.search(n) and not n.isupper() for n, _ in f.identifiers)  # LOG_CALL = ... is not logging
        or LOG_CALL.search("\n".join(f.code_lines))
        for _, _, f in code
    )
    any_human = any(_named(f, HUMAN_STEP) for _, _, f in code)

    # Employment use case => high-risk signal (Annex III point 4)
    if hiring and ai:
        add("Annex III", "high", "employment-use-case", *hiring[0],
            "Code handles candidates/applicants and uses AI or scoring: recruitment/selection systems are listed in Annex III point 4(a), so Article 6(2) makes them high-risk.",
            "Treat as high-risk: write down intended purpose, then start technical documentation (Article 11) and a risk process (Article 9).")

    for name, _, facts in code:
        f = _visible(facts, lines_of[name], "emotion-or-biometric")
        emotion = imports_any(f, EMOTION_LIBS)
        biometric = imports_any(f, BIOMETRIC_LIBS)
        used = next((line for ident, line in f.identifiers if set(words(ident)) & EMOTION_NAME), None)
        if emotion:
            add("Article 5", "critical", "emotion-or-biometric", name, emotion[1],
                f"Imports the emotion-analysis library '{emotion[0]}'. Article 5(1)(f) prohibits inferring emotions in the workplace and education (narrow medical/safety exception).",
                "Remove it, or get legal review before any use on employees, candidates or students.")
        elif biometric:
            add("Article 5", "high", "emotion-or-biometric", name, biometric[1],
                f"Imports the face-analysis library '{biometric[0]}'. Some biometric uses are prohibited (Article 5) and others are high-risk (Annex III point 1).",
                "Write down what the library is used for and get legal review of that purpose.")
        elif used:
            add("Article 5", "medium", "emotion-or-biometric", name, used,
                "Code uses a name referring to emotions or biometrics. The name alone does not show what the code does; Article 5 and Annex III point 1 depend on the purpose.",
                "Check what this code infers and about whom.")

        line = _unreviewed_decision(_visible(facts, lines_of[name], "automated-decision-no-human"))
        if line:
            add("Article 14", "high", "automated-decision-no-human", name, line,
                "Automatic reject/approve logic with no human review or override step in the same code block. High-risk systems must be designed so people can oversee, interpret and override the output.",
                "Make the model advisory: require a named person to confirm any adverse decision and log who did.")

        f = _visible(facts, lines_of[name], "protected-attribute-as-feature")
        protected = next((ln for var, value, ln in f.assigned_strings
                          if FEATURE_NAME.search(var) and value.lower() in PROTECTED), None)
        if protected:
            add("Article 10", "medium", "protected-attribute-as-feature", name, protected,
                "A protected attribute appears in a feature or training-column list. Article 10 requires examining and mitigating bias in training and input data.",
                "Remove it from model inputs, keep it only in a separate fairness-test set, and record the bias test.")

    # People talking to a model, with no disclosure. Importing a library is not itself a chat UI.
    chatty = any(
        re.search(r"chat\.completions|ChatCompletion|messages\.(?:create|stream)|responses\.create|generate_?[Cc]ontent|\b(?:generate|stream)Text\b", "\n".join(f.code_lines))
        for _, _, f in code
    )
    if chatty and ai and not any_disclosure:
        add("Article 50", "medium", "no-ai-disclosure", *ai[0],
            "The app uses an AI library but nothing tells users they are talking to AI. Article 50(1) requires people to be informed when they interact with an AI system, unless obvious.",
            "If people interact with it, show a clear notice such as 'You are chatting with an AI assistant' before the first message.")

    # No logging around AI use
    if ai and not any_logging:
        add("Article 12", "high" if hiring else "low", "no-event-logging", *ai[0],
            "AI libraries are used but no logging/audit-trail code was found. High-risk systems must technically allow automatic recording of events over their lifetime.",
            "Log each model call: timestamp, input reference, model version, output, and any human override. Decide a retention period.")

    # High-risk signal but no incident process in docs
    if hiring and not any(INCIDENT.search(t) for _, t in files):
        add("Article 73", "medium", "no-incident-procedure", "(repo-wide)", 0,
            "No incident-handling mention in code or docs. Providers of high-risk systems must report serious incidents to authorities.",
            "Write a one-page incident procedure: who detects, who decides, how and when authorities and customers are notified.")

    if hiring and not any_human and not any(f["rule"] == "automated-decision-no-human" for f in findings):
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
        L += [f"[{f['severity'].upper()}] {f['cite']} — {f['rule']}  ({f['where']})"]
        if f["snippet"]:
            L.append(f"   code: {f['snippet']}")
        L += [f"   why: {f['why']}", f"   fix: {f['fix']}", ""]
    L.append(result["note"])
    return "\n".join(L)


def main():
    target = next((a for a in sys.argv[1:] if not a.startswith("--")), ".")
    res = scan(target)
    print(json.dumps(res, indent=2) if "--json" in sys.argv else render(res))


if __name__ == "__main__":
    main()

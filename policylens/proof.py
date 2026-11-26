"""
The proof gate: an AI agent may only report what it can show.

A claim is a statement plus two receipts: a quote from the scanned code (file and line) and
a quote from the Act. Deterministic code checks both. No model takes part in the check, so
a model cannot talk its way past it.

What GROUNDED means: both quotes exist where the claim says they do, and the statement
passes the wording rules below. What it does NOT mean: that the law applies to this code,
or that the statement follows from the quotes. A human still has to judge that.
"""

from __future__ import annotations

import re
from pathlib import Path

from policylens import laws
from policylens.codefacts import extract
from policylens.scanner import CODE_EXTS, SKIP_DIRS

FIELDS = ("statement", "file", "line", "code_quote", "cite", "law_quote")
MIN_CODE_QUOTE = 8   # non-space characters
MIN_CODE_CHARS = 4   # of those, how many must be real code rather than comment or string
MIN_LAW_QUOTE = 40   # characters; shorter fragments ("AI system") prove nothing

VERDICT_WORDS = re.compile(
    r"\b(compliant|compliance is (met|achieved)|complies|conforms|no (legal )?risk|fully (meets|satisfies)|"
    r"(is|are) (legal|illegal|lawful|unlawful)|violates|in breach)\b", re.I)
ABSENCE_WORDS = re.compile(
    r"\b(does not|do not|doesn't|don't|never|there is no|there are no|has no|have no|lacks?|without|missing|"
    r"absent|absence of|no (human|recruiter|reviewer|review|oversight|logging|logs|disclosure|notice|documentation))\b", re.I)


def _flat(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def read_source(root: str | Path, file: str) -> tuple[str | None, str]:
    """(text, error). Only source files inside `root`: no traversal, symlink escape, .env or vendored dirs."""
    base = Path(root).resolve()
    target = (base / file).resolve()
    if not target.is_relative_to(base):
        return None, "file is outside the repository"
    if set(target.relative_to(base).parts) & SKIP_DIRS:
        return None, "file is in a skipped directory"
    if target.suffix.lower() not in CODE_EXTS:
        return None, "not a source-code file"
    if not target.is_file():
        return None, "file does not exist"
    if target.stat().st_size >= 300_000:
        return None, "file is too large"
    return target.read_text(encoding="utf-8", errors="ignore"), ""


def _check_code(root, claim) -> list[str]:
    text, error = read_source(root, str(claim["file"]))
    if error:
        return [f"code: {error}"]
    quote = str(claim["code_quote"]).strip("\n")
    if len(re.sub(r"\s", "", quote)) < MIN_CODE_QUOTE:
        return [f"code: quote is too short (needs {MIN_CODE_QUOTE}+ non-space characters)"]
    try:
        line = int(claim["line"])
    except (TypeError, ValueError):
        return ["code: line must be a number"]
    source = text.split("\n")
    span = quote.count("\n") + 1
    if not 1 <= line <= len(source):
        return [f"code: line {line} is outside the file (1-{len(source)})"]
    block = "\n".join(source[line - 1: line - 1 + span])
    # Whitespace may differ; everything else must match. The quote must start on the cited line.
    pattern = r"\s+".join(re.escape(part) for part in quote.split())
    first_line = len(source[line - 1])
    matches = [m for m in re.finditer(pattern, block) if m.start() <= first_line]
    if not matches:
        return [f"code: quote is not at {claim['file']}:{line}"]
    # Same positions in the view with comments and strings blanked: is the quoted part itself code?
    visible = "\n".join(extract(text, Path(str(claim["file"])).suffix).code_lines[line - 1: line - 1 + span])
    if not any(len(re.sub(r"\s", "", visible[m.start():m.end()])) >= MIN_CODE_CHARS for m in matches):
        return ["code: quote is only a comment or string text, which shows nothing the code does"]
    return []


def _check_law(claim) -> list[str]:
    cite = str(claim["cite"]).strip()
    if not re.fullmatch(r"(Article \d+|Annex [IVX]+)", cite) or not laws.exists(cite):
        return [f"law: '{cite}' is not one Article or Annex of the Act (use 'Article 14' or 'Annex III')"]
    quote = _flat(str(claim["law_quote"]))
    if len(quote) < MIN_LAW_QUOTE:
        return [f"law: quote is too short (needs {MIN_LAW_QUOTE}+ characters)"]
    if quote not in _flat(laws.get(cite)["text"]):
        return [f"law: quote is not verbatim text of {cite}"]
    return []


def _check_statement(claim) -> list[str]:
    statement = str(claim["statement"]).strip()
    reasons = []
    extra = laws.extract_citations(statement) - {str(claim["cite"]).strip()}
    if extra:
        reasons.append(f"statement: also cites {', '.join(sorted(extra))} without a quote. One citation per claim")
    if m := VERDICT_WORDS.search(statement):
        reasons.append(f"statement: '{m[0]}' is a legal verdict, which a code quote cannot prove")
    if m := ABSENCE_WORDS.search(statement):
        reasons.append(f"statement: '{m[0]}' claims something is absent, which one quoted line cannot prove")
    if not 20 <= len(statement) <= 400:
        reasons.append("statement: must be 20-400 characters")
    return reasons


def verify_claim(root: str | Path, claim: dict) -> dict:
    """-> {"verdict": "GROUNDED" | "REJECTED", "reasons": [...], "claim": {...}}"""
    missing = [k for k in FIELDS if not str(claim.get(k, "")).strip()]
    reasons = [f"missing field: {k}" for k in missing] or (
        _check_code(root, claim) + _check_law(claim) + _check_statement(claim))
    return {"verdict": "REJECTED" if reasons else "GROUNDED", "reasons": reasons,
            "claim": {k: claim.get(k) for k in FIELDS}}

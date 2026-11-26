"""
Legal drift: did this change alter what the EU AI Act may ask of the product?

  python -m policylens.drift --base origin/main            # compare a git ref with the working tree
  python -m policylens.drift --base main --format sarif --out policylens.sarif

Linters report everything, so teams mute them. This reports only what a change adds.
Exit code 1 when it adds a finding at or above --fail-on (default: high), 2 on usage errors.

Findings are matched by rule, file and the text of the line, so moving code within a file
is not "new". Renaming a file shows up as one resolved and one new finding.
The scanned code is only read, never executed.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from policylens import laws, scanner

RANK = {"critical": 3, "high": 2, "medium": 1, "low": 0}
# Highest first. A flag for human review, never a determination.
EXPOSURE = [
    ("Article 5 review: possible prohibited practice", lambda f: f["rule"] == "emotion-or-biometric" and f["severity"] == "critical"),
    ("High-risk signal (Annex III)", lambda f: f["rule"] == "employment-use-case"),
    ("Biometric review", lambda f: f["rule"] == "emotion-or-biometric" and f["severity"] == "high"),
    ("Transparency review (Article 50)", lambda f: f["rule"] == "no-ai-disclosure"),
]
NO_SIGNAL = "No tracked signal"
# Rules about the whole repository: their file is just an example location.
REPO_WIDE = {"no-ai-disclosure", "no-event-logging", "no-incident-procedure", "no-human-oversight-mechanism",
             "employment-use-case"}


def exposure(findings: list[dict]) -> str:
    return next((label for label, match in EXPOSURE if any(match(f) for f in findings)), NO_SIGNAL)


def _key(f: dict) -> tuple:
    return (f["rule"],) if f["rule"] in REPO_WIDE else (f["rule"], f["file"], " ".join(f["snippet"].split()))


def compare(base: dict, head: dict) -> dict:
    """Two `scanner.scan` results -> what the change added and resolved."""
    before = {_key(f): f for f in base["findings"]}
    after = {_key(f): f for f in head["findings"]}
    added = [f for k, f in after.items() if k not in before or RANK[f["severity"]] > RANK[before[k]["severity"]]]
    resolved = [f for k, f in before.items() if k not in after]
    return {"added": added, "resolved": resolved,
            "exposure_before": exposure(base["findings"]), "exposure_after": exposure(head["findings"])}


def _git(repo: Path, *args: str) -> bytes:
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if run.returncode:
        raise ValueError(run.stderr.decode(errors="replace").strip() or f"git {args[0]} failed")
    return run.stdout


def scan_ref(repo: Path, ref: str) -> dict:
    """Scan `repo` as it was at git `ref`, without touching the working tree."""
    if ref.startswith("-"):
        raise ValueError(f"invalid git ref: {ref}")
    commit = _git(repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").decode().strip()
    # Run from `repo`, so a subdirectory path archives just that subdirectory.
    archive = _git(repo, "archive", "--format=tar", commit)
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                target = (Path(tmp) / member.name).resolve()
                if member.isfile() and target.is_relative_to(Path(tmp).resolve()):  # no links, no traversal
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(member).read())
        return scanner.scan(tmp)


def drift(repo: str | Path, base_ref: str) -> dict:
    repo = Path(repo).resolve()
    return compare(scan_ref(repo, base_ref), scanner.scan(repo))


def _cell(text: str) -> str:
    """Scanned code goes into a PR comment: keep it from breaking the markdown."""
    return text.replace("`", "'").replace("\n", " ")


def render_markdown(d: dict) -> str:
    before, after = d["exposure_before"], d["exposure_after"]
    L = ["## PolicyLens: EU AI Act drift", ""]
    L.append(f"**Exposure changed:** {before} → **{after}**" if before != after else f"**Exposure unchanged:** {after}")
    L.append("")
    if not d["added"]:
        L.append("This change adds no new findings.")
    for f in sorted(d["added"], key=lambda f: -RANK[f["severity"]]):
        L += [f"### {f['severity'].upper()}: {f['cite']} (`{_cell(f['where'])}`)"]
        if f["snippet"]:
            L += ["", f"`{_cell(f['snippet'])}`"]
        L += ["", f["why"], "", f"**Fix:** {f['fix']}", ""]
    if d["resolved"]:
        L += ["", f"**No longer detected:** " + ", ".join(sorted({f["rule"] for f in d["resolved"]}))]
    L += ["", "_Pattern-based flags for human review. No findings is not evidence of compliance. Not legal advice._"]
    return "\n".join(L)


def to_sarif(findings: list[dict], prefix: str = "") -> dict:
    """SARIF 2.1.0, so GitHub code scanning can show findings on the changed lines."""
    level = {"critical": "error", "high": "error", "medium": "warning", "low": "note"}
    rules, results = {}, []
    for f in findings:
        rules[f["rule"]] = {"id": f["rule"], "shortDescription": {"text": f"{f['cite']}: {f['rule']}"},
                            "help": {"text": f"{f['fix']}\n\n{laws.excerpt(f['cite'], 600)}"}}
        result = {"ruleId": f["rule"], "level": level[f["severity"]],
                  "message": {"text": f"{f['cite']}. {f['why']} Fix: {f['fix']}"}}
        if f["line"]:
            result["locations"] = [{"physicalLocation": {"artifactLocation": {"uri": prefix + Path(f["file"]).as_posix()},
                                                         "region": {"startLine": f["line"]}}}]
        results.append(result)
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "PolicyLens", "rules": list(rules.values()),
                                          "informationUri": "https://github.com/bhushan-01/policylens"}},
                      "results": results}]}


def main(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--base", required=True, help="git ref to compare against, e.g. origin/main")
    ap.add_argument("--format", choices=["markdown", "json", "sarif"], default="markdown")
    ap.add_argument("--out", help="write the report here instead of stdout")
    ap.add_argument("--fail-on", choices=[*RANK, "never"], default="high")
    a = ap.parse_args(argv)
    try:
        d = drift(a.path, a.base)
        top = _git(Path(a.path).resolve(), "rev-parse", "--show-prefix").decode().strip()
    except ValueError as e:
        print(f"policylens drift: {e}", file=sys.stderr)
        sys.exit(2)
    if a.format == "sarif":
        report = json.dumps(to_sarif(d["added"], top), indent=2)
    elif a.format == "json":
        report = json.dumps(d, indent=2)
    else:
        report = render_markdown(d)
    if a.out:
        Path(a.out).write_text(report + "\n", encoding="utf-8")
    else:
        print(report)
    if a.fail_on != "never" and any(RANK[f["severity"]] >= RANK[a.fail_on] for f in d["added"]):
        sys.exit(1)


if __name__ == "__main__":
    main()

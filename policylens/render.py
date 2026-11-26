"""Render an evidence pack to Markdown, HTML, JSON, CSV and a draft public position page."""

from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path

DISCLAIMER = ("Draft prepared from the vendor's own documents and the text of Regulation (EU) 2024/1689. "
              "Not legal advice. Have qualified counsel review before sending to a customer.")
STATUS_LABEL = {"ready": "READY", "needs_input": "NEEDS INPUT", "review": "CHECK CITATIONS"}


def render_markdown(pack: dict) -> str:
    c, gaps, answers = pack["classification"], pack["gaps"], pack["answers"]
    L = [f"# AI Act Evidence Pack — {pack['company']}", "", f"_Generated {pack['date']} · mode: {pack['mode']}_", "",
         f"> {DISCLAIMER}", "", "## 1. Risk classification", "", f"**{c['tier']}**", ""]
    for b in c["basis"]:
        L.append(f"- **{b['cite']}** — {b['why']}")
        if b["quote"]:
            L.append(f"  > “{b['quote']}”")
    for n in c["notes"]:
        if n.startswith("Semantic near-misses"):
            continue  # internal look-here hint; stays in the JSON, not in a buyer-facing pack
        L += ["", f"_{n}_"]
    L += ["", "## 2. Readiness against buyer-expected evidence", "",
          "| Obligation | Article | Status | Where we found it |", "|---|---|---|---|"]
    for g in gaps:
        L.append(f"| {g['topic']} | {g['article']} | {g['status']} | {', '.join(g['evidence']) or '—'} |")
    s = pack["summary"]
    L += ["", f"**{s['evidenced']} evidenced · {s['partial']} partial · {s['missing']} missing** of {s['total']} obligations. _Keyword triage of your documents to show where to look first — not a compliance determination._", "",
          "### Fix first", ""]
    for g in [g for g in gaps if g["status"] != "Evidenced"]:
        L.append(f"- **{g['article']} — {g['topic']}** ({g['status']}): {g['ask']}")
        near = g.get("semantic_near") or []
        if near and g["status"] == "Missing":
            L.append(
                f"  - _Semantic look-here (not evidence): "
                + ", ".join(f"{n['id']} ({n['score']})" for n in near[:2])
                + "_"
            )
    try:
        from policylens.blueprint import blueprints_for_gaps

        bps = blueprints_for_gaps(gaps)
        if bps:
            L += ["", "### Document blueprints (fix first)", ""]
            for bp in bps[:6]:
                L.append(f"**{bp['topic']}** ({bp['article']}) — {bp['status']}")
                L.append(f"_{bp['note']}_")
                for s in bp["sections"][:4]:
                    L.append(f"- {s}")
                L.append("")
    except Exception:
        pass
    L += ["", "## 3. Questionnaire answers", ""]
    for i, a in enumerate(answers, 1):
        v = a["verification"]
        L += [f"### Q{i}. {a['question']}", "", f"**[{STATUS_LABEL[a['status']]}]**", "", a["answer"], ""]
        if a["missing"]:
            L.append("Missing: " + "; ".join(a["missing"]) + "\n")
        if v["nonexistent"] or v["unsupported"] or v["bad_doc_refs"]:
            L.append(f"⚠ Citation check failed — nonexistent: {v['nonexistent']}, not in evidence: {v['unsupported']}, bad doc refs: {v['bad_doc_refs']}\n")
        for fl in a.get("claim_flags", []):
            L.append(f"⚠ {fl}\n")
        L.append(f"_Law consulted: {', '.join(a['law'])}. Company docs consulted: {', '.join(a['evidence']) or 'none'}._\n")
    return "\n".join(L)


def render_html(pack: dict) -> str:
    e = html.escape
    badge = {"Evidenced": "ok", "Partial": "warn", "Missing": "bad", "ready": "ok", "needs_input": "bad", "review": "warn"}
    rows = "".join(f"<tr><td>{e(g['topic'])}</td><td>{e(g['article'])}</td><td><span class='b {badge[g['status']]}'>{g['status']}</span></td><td>{e(', '.join(g['evidence']) or '—')}</td></tr>" for g in pack["gaps"])
    qa = ""
    for i, a in enumerate(pack["answers"], 1):
        ans = re.sub(r"\[NEEDS INPUT[^\]]*\]", lambda m: f"<mark>{m.group(0)}</mark>", e(a["answer"]))
        v = a.get("verification") or {}
        warns = ""
        if v.get("nonexistent") or v.get("unsupported") or v.get("bad_doc_refs"):
            warns += (
                f"<p class='warnline'>Citation check failed — nonexistent: {e(str(v.get('nonexistent')))}, "
                f"not in evidence: {e(str(v.get('unsupported')))}, "
                f"bad doc refs: {e(str(v.get('bad_doc_refs')))}</p>"
            )
        for fl in a.get("claim_flags") or []:
            warns += f"<p class='warnline'>{e(fl)}</p>"
        qa += (f"<section><h3>Q{i}. {e(a['question'])}</h3><span class='b {badge[a['status']]}'>{STATUS_LABEL[a['status']]}</span>"
               f"<p>{ans}</p>{warns}<small>Law: {e(', '.join(a['law']))} · Docs: {e(', '.join(a['evidence']) or 'none')}</small></section>")
    basis = "".join(f"<li><b>{e(b['cite'])}</b> — {e(b['why'])}<blockquote>{e(b['quote'])}</blockquote></li>" for b in pack["classification"]["basis"])
    s = pack["summary"]
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Act Evidence Pack — {e(pack['company'])}</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 16px;color:#1b1f24}}
table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left;font-size:14px}}
.b{{padding:2px 8px;border-radius:10px;font-size:12px;font-weight:600}}.ok{{background:#d8f3dc}}.warn{{background:#ffe8a3}}.bad{{background:#ffd0d0}}
blockquote{{margin:.4rem 0;padding-left:.8rem;border-left:3px solid #bbb;color:#444;font-size:14px}}section{{border-top:1px solid #eee;padding:.6rem 0}}
mark{{background:#ffd0d0}}small{{color:#666}}.warnline{{color:#8a1f1f;font-size:14px}}</style>
<h1>AI Act Evidence Pack — {e(pack['company'])}</h1><p><small>{pack['date']} · {e(DISCLAIMER)}</small></p>
<h2>Risk classification</h2><p><b>{e(pack['classification']['tier'])}</b></p><ul>{basis}</ul>
<h2>Readiness</h2><p>{s['evidenced']} evidenced · {s['partial']} partial · {s['missing']} missing of {s['total']}</p>
<table><tr><th>Obligation</th><th>Article</th><th>Status</th><th>Found in</th></tr>{rows}</table>
<h2>Questionnaire answers</h2>{qa}</html>"""


def position_page(pack: dict) -> str:
    """Public 'our AI Act position' draft built ONLY from classification + evidenced items."""
    ok = [g for g in pack["gaps"] if g["status"] == "Evidenced"]
    todo = [g for g in pack["gaps"] if g["status"] != "Evidenced"]
    L = [f"# {pack['company']} — EU AI Act position (DRAFT for counsel review)", "",
         f"**Classification:** {pack['classification']['tier']}", "",
         "## Topics your documents mention", "",
         "_Keyword hits only. This is not proof an obligation is met. Do not publish these as compliance claims._", ""]
    L += [f"- **{g['topic']}** ({g['article']}) — keyword hits in {', '.join(g['evidence'])}" for g in ok] or ["- _(nothing mentioned yet)_"]
    L += ["", "## Not mentioned yet", ""]
    L += [f"- {g['topic']} ({g['article']})" for g in todo]
    L += ["", "_Only publish statements you can back with documents. This page is generated from your own docs; edit before use._"]
    return "\n".join(L)


def write_outputs(pack: dict, out: str | Path) -> list[Path]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "evidence_pack.md": render_markdown(pack),
        "evidence_pack.html": render_html(pack),
        "evidence_pack.json": json.dumps(pack, indent=2, ensure_ascii=False),
        "ai_act_position.md": position_page(pack),
    }
    for name, content in files.items():
        (out / name).write_text(content, encoding="utf-8")
    with (out / "gaps.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["article", "topic", "status", "what_buyers_expect", "found_in"])
        for g in pack["gaps"]:
            w.writerow([g["article"], g["topic"], g["status"], g["ask"], "; ".join(g["evidence"])])
    return [out / n for n in [*files, "gaps.csv"]]

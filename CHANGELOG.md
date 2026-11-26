# Changelog

## Unreleased: agents with receipts
- **Proof gate** (`proof.py`, MCP `submit_claim`): agent findings need a real code quote and a real law quote.
- **Investigator agent** (`investigate.py`): explores a repo and can report only through the gate.
- **Legal drift** (`drift.py`, `action.yml`, MCP `legal_drift`): reports what a change adds; markdown, JSON, SARIF.
- **Scanner reads code, not words** (`codefacts.py`): scanning this repo went from 13 findings (10 CRITICAL, 9 of those
  false) to 6, all but one in the planted sample app. Findings now include the line of code. Inline ignore comments.
  Symlinks are skipped.
- CI workflow; offline evals.
- Gap keywords are whole words, and a negated sentence no longer counts as evidence.
- Classification no longer treats a denial ("we do not detect emotions"), "promotional email", "session termination", or "we court customers" as an Annex III or Article 5 hit. Training a foundation model is labeled GPAI.
- Citation checks are case-insensitive and catch every number in "Articles 9 and 999".
- The position page says which topics the documents mention. It does not say those obligations are already in place.

## 0.3.0 Evidence Tribunal + hardening
- Replaced the free-form tool-calling agent with an **Evidence Tribunal**
  (Prosecutor → Defense → Citation Auditor → proof ledger). `python -m policylens.agent`
  now redirects here; new CLI: `policylens-tribunal` / `make tribunal`.
- Classification: synonym expansions (talent acquisition, conversational agent, …) plus
  semantic near-miss hints; optional `--promote-semantic` in the tribunal.
- Gap analysis: keyword status unchanged, plus batched semantic look-here signals;
  fix-first **document blueprints** in pack render / UI.
- Web UI: Tribunal tab, fix-first blueprints, refreshed styling; static landing at `web/index.html`.
- Deploy: `Dockerfile` for the Gradio app; MCP tool `evidence_tribunal`.
- Evals extended for tribunal, synonyms, and blueprints.

## 0.2.0 Restructure
- Proper Python package `policylens/` (installable with `pip install -e .`, console scripts) replacing the flat `src/` scripts.
- Split the large evidence module into `classification.py`, `pack.py` and `render.py`; shared `paths.py`, `config.py`, `omnibus.py`.
- `evals/` for tests and fixtures; `examples/` for the fictional sample company, questionnaire, repo and output; `data/` now holds only the law.
- Removed throwaway demo scripts and the thin one-shot wrapper; study material moved to `docs/learning/`.
- Classification now ignores stated exclusions ("not intended for promotion decisions"). 83 evals.
- Verified the ingest scripts rebuild the committed law data byte-for-byte.

## Evidence Pack release
- Evidence Pack: classification, 14-obligation gap analysis, cited questionnaire drafting, verification guards.
- `risk_rules.py`: 27 rules covering all Annex III areas, Article 5 bans, Article 50, GPAI.
- Code scanner and MCP tools: `scan_codebase`, `evidence_gaps`, `verify_citations`.
- Web UI: Evidence Pack tab; classifier shows the rule-based first pass.
- 83 offline evals including adversarial model cases.
- Docs: architecture, user guide, safety and limits, customer discovery, outreach, `AGENTS.md`.
- Fix: classifier high-risk query no longer biased toward recruitment wording.

## Earlier
- Pipeline: extract, clean, chunk, split, embed, search.
- Checklist RAG entry point, tool-calling agent, MCP server, Gradio UI, retrieval and assertion evals.
- Learning docs: `LEARNING.md`, `KNOWLEDGE_BASE.md`, `WHAT_IS_THIS.md`.

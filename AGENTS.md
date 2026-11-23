# AGENTS.md — PolicyLens (instructions for Cursor / coding agents)

## What this project is
PolicyLens answers: "What does the EU AI Act say about *my* AI product, and where does it say it?"
Two products share one law index:
1. **Classifier**: describe a product, get a risk category with citations (`policylens/checklist.py`).
2. **Evidence Pack**: AI hiring/HR-tech vendors answer a buyer's AI Act questionnaire from their own
   documents (`policylens/pack.py`). This is the business direction. Classification alone is free
   elsewhere; the paid pain is the questionnaire.
Also: a code scanner (`policylens/scanner.py`) and an MCP server exposing both to editors.

## Golden rules (never break these)
- No claim without a citation. If evidence is weak, say "not sure" or `[NEEDS INPUT]`.
- Law facts come only from retrieved Article/Annex text. Company facts come only from the vendor's docs.
- Absence of evidence is not evidence of absence. Never write "we do not X" without proof.
- Every emitted citation must exist in the Act (`policylens/laws.py`). Run `python -m evals.evidence`
  before finishing any change. It must stay green.
- Not legal advice. Dates rely on the Omnibus note in `policylens/omnibus.py`; re-verify against the Official Journal.

## How to teach the owner (they want to learn, not just receive code)
- One small step at a time. Explain the idea in plain language first, then show code.
- Let the owner type the core logic. Offer hints before answers.
- Quiz at the end of each step (2-3 questions).
- Check expected numbers: 113 Articles, 13 Annexes, 126 chunks. If they differ, stop and find out why.
- Suggested reading order: `policylens/laws.py` -> `policylens/obligations.py` -> `policylens/pack.py`
  (focus on `draft_answer`) -> `policylens/scanner.py` -> `evals/evidence.py`.

## Map
| Area | Files |
|---|---|
| Paths / config | policylens/paths.py, config.py |
| Law data and lookup | policylens/ingest/*, search.py, laws.py (data in data/) |
| Classification | risk_rules.py, classification.py |
| Classifier product | checklist.py, answer.py, omnibus.py, ui.py |
| Evidence Pack | pack.py, render.py, company.py, obligations.py, llm.py |
| Code scanner | scanner.py |
| Agent / MCP | agent.py, mcp_server.py (tools: search_law, get_article, classify_product, scan_codebase, evidence_gaps, verify_citations) |
| Evals | evals/evidence.py (83 offline checks), evals/retrieval.py, evals/assertions.py; fixtures in evals/fixtures/ |
| Demo inputs | examples/sample_company, sample_questionnaire.md, sample_repo, sample_output |
| Business | docs/BUSINESS_PLAN.md, docs/CUSTOMER_DISCOVERY.md, docs/OUTREACH.md |

Conventions: import as `from policylens import laws`; never use relative paths to data (use `policylens.paths`);
run modules with `python -m policylens.<name>`; install once with `pip install -e . --no-deps`.

## Commands
`make test | demo | demo-offline | scan | ui | mcp` wrap these:
```bash
python -m policylens.pack --docs examples/sample_company --questionnaire examples/sample_questionnaire.md [--no-llm]
python -m policylens.scanner examples/sample_repo
python -m evals.evidence
python -m policylens.ui            # Gradio UI
python -m policylens.mcp_server     # MCP over stdio (see mcp_config.example.json)
```

## Status
- Done: ingest, split, embeddings, search, classifier, agent, MCP, evidence pack, code scanner, 83 evals.
- Known gaps: classification is keyword rules (27, all Annex III areas + Art. 5 + Art. 50), so unusual wording
  can be missed; gap status is keyword triage; no real customer has used it yet.
- Next (business, not code): run the interviews in docs/CUSTOMER_DISCOVERY.md. Stop rule: <5 of 15 faced a real questionnaire.
- Never commit `.env`. Do not send real customer documents to external APIs without consent.

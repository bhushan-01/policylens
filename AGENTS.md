# AGENTS.md — PolicyLens (instructions for Cursor / coding agents)

## What this project is
PolicyLens answers: "What does the EU AI Act say about *my* AI product, and where does it say it?"
Two products share one law index:
1. **Classifier**: describe a product, get a risk category with citations (`src/policylens.py`).
2. **Evidence Pack**: AI hiring/HR-tech vendors answer a buyer's AI Act questionnaire from their own
   documents (`src/evidence_pack.py`). This is the business direction. Classification alone is free
   elsewhere; the paid pain is the questionnaire.
Also: a code scanner (`src/code_scan.py`) and an MCP server exposing both to editors.

## Golden rules (never break these)
- No claim without a citation. If evidence is weak, say "not sure" or `[NEEDS INPUT]`.
- Law facts come only from retrieved Article/Annex text. Company facts come only from the vendor's docs.
- Absence of evidence is not evidence of absence. Never write "we do not X" without proof.
- Every emitted citation must exist in the Act (`src/laws.py`). Run `python src/eval_evidence.py`
  before finishing any change. It must stay green.
- Not legal advice. Dates rely on the Omnibus note in `src/answer.py`; re-verify against the Official Journal.

## How to teach the owner (they want to learn, not just receive code)
- One small step at a time. Explain the idea in plain language first, then show code.
- Let the owner type the core logic. Offer hints before answers.
- Quiz at the end of each step (2-3 questions).
- Check expected numbers: 113 Articles, 13 Annexes, 126 chunks. If they differ, stop and find out why.
- Suggested reading order: `src/laws.py` -> `src/obligations.py` -> `src/evidence_pack.py`
  (focus on `draft_answer`) -> `src/code_scan.py` -> `src/eval_evidence.py`.

## Map
| Area | Files |
|---|---|
| Ingest | extract_text.py, clean_text.py, chunk.py |
| Index/search | split_chunks.py, embed_chunks.py, search.py |
| Classifier | policylens.py, answer.py, classify.py, app.py |
| Evidence Pack | evidence_pack.py, company.py, obligations.py, laws.py, llm.py |
| Code scanner | code_scan.py |
| Agent / MCP | agent.py, mcp_server.py (tools: search_law, get_article, classify_product, scan_codebase, evidence_gaps, verify_citations) |
| Evals | eval_retrieval.py, eval_assertions.py, eval_evidence.py (39 checks, offline) |
| Business | docs/CUSTOMER_DISCOVERY.md, docs/OUTREACH.md |

## Commands
```bash
python src/evidence_pack.py --docs data/sample_company --questionnaire data/sample_questionnaire.md [--no-llm]
python src/code_scan.py data/sample_repo
python src/eval_evidence.py
python src/app.py            # Gradio UI
python src/mcp_server.py     # MCP over stdio (see mcp_config.example.json)
```

## Status
- Done: ingest, split, embeddings, search, classifier, agent, MCP, evidence pack, code scanner, 39 evals.
- Known gaps: classification keyword rules do not cover biometrics (Annex III point 1) or education/credit
  use cases; gap status is keyword triage; no real customer has used it yet.
- Next (business, not code): run the interviews in docs/CUSTOMER_DISCOVERY.md. Stop rule: <5 of 15 faced a real questionnaire.
- Never commit `.env`. Do not send real customer documents to external APIs without consent.

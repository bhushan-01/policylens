# PolicyLens architecture

This document explains how PolicyLens works end to end: the data, the modules, the flow of one
request, and the design decisions behind the trust features.

## 1. Two products on one law index

| Product | Question it answers | Entry point |
|---|---|---|
| Classifier | "What does the EU AI Act say about my AI product?" | `policylens/checklist.py`, web UI tab |
| Evidence Pack | "How do I answer my customer's AI Act questionnaire, with proof?" | `policylens/pack.py`, web UI tab |

Supporting tools: code scanner (`policylens/scanner.py`), MCP server (`policylens/mcp_server.py`),
Evidence Tribunal (`policylens/tribunal.py` — adversarial proof ledger; `agent.py` redirects here),
fix-first blueprints (`policylens/blueprint.py`).

Why the Evidence Pack exists: risk classification alone is already free (EU Commission checker,
Future of Life Institute, TÜV SÜD). The paid pain is the buyer questionnaire an AI vendor must answer
before an EU enterprise deal closes. The first target segment is AI hiring and HR-tech, because
Annex III point 4 is the clearest high-risk case.

## 2. Data layer (built once, committed)

```
data/eu_ai_act.pdf          source law, Regulation (EU) 2024/1689
data/ai_act_raw.txt         extracted text            (policylens/ingest/extract_text.py)
data/ai_act_clean.txt       headers/footers removed   (policylens/ingest/clean_text.py)
data/chunks.json            113 Articles + 13 Annexes (policylens/ingest/chunk.py)
data/chunks_split.json      pieces <= 512 tokens      (policylens/ingest/split_chunks.py)
data/embeddings.npy         one 384-d vector per piece (policylens/ingest/embed_chunks.py, BAAI/bge-small-en-v1.5)
```

Key facts that shaped the design:
- The embedding model reads about 512 tokens and silently truncates the rest. 52 of 126 parent chunks
  were longer, so they were split into pieces that keep the parent Article number for citation.
- After the Annexes start, lines such as "Article 49" inside tables are not real Articles. The chunker
  stops treating them as headings (the "fake Article 49" bug).
- Parent chunks (`chunks.json`) are used for exact lookups and quotes. Split pieces
  (`chunks_split.json`) are used for semantic search.

## 3. Module map

All code lives in the `policylens/` package. Run modules with `python -m policylens.<name>`.

| Module | Responsibility |
|---|---|
| `paths.py`, `config.py` | Project locations independent of the working directory; `.env` loading |
| `search.py` | Hybrid semantic search: embedding similarity plus a small keyword bonus, with parent diversification |
| `laws.py` | Exact Article/Annex lookup, verbatim quotes, citation extraction and verification |
| `risk_rules.py` | 27 classification rules: all Annex III areas, all Article 5 bans, Article 50, GPAI |
| `classification.py` | Applies the rules to a description, ignores stated exclusions, quotes the law, adds notes |
| `obligations.py` | 14 buyer-expected obligations, each tied to a real Article, with document keywords |
| `company.py` | Loads a vendor's `.md/.txt` documents as numbered passages; keyword and meaning search over them |
| `pack.py` | Evidence Pack pipeline: gap analysis, answer drafting, verification guards, CLI |
| `render.py` | Markdown, HTML, JSON, CSV and the draft public position page |
| `llm.py` | One wrapper for OpenRouter or Anthropic; JSON parsing tolerant of fences |
| `omnibus.py` | Post-2024 date note (Digital Omnibus). Re-verify against the Official Journal |
| `answer.py`, `checklist.py` | Classifier answer generation and its CLI (prohibited, high-risk, transparency checklist) |
| `scanner.py` | Heuristic scanner for AI Act red flags in a code repository |
| `mcp_server.py` | Exposes search, lookup, classify, scan, gaps and citation checks to editors |
| `ui.py` | Gradio UI with two tabs |
| `agent.py` | Tool-calling agent (learning exercise and hard cases) |
| `ingest/` | One-time PDF to chunks to embeddings pipeline, plus a token-limit check |

Tests live in `evals/` (`evidence.py` 96 offline checks, `retrieval.py`, `assertions.py`) with fixtures
in `evals/fixtures/`. Demo inputs and a sample output live in `examples/`.

## 4. Evidence Pack data flow

```
vendor docs/ ──► load_passages ──► passages [{id "file § n", title, heading, text}]
questionnaire ─► parse_questions ─► ["Q1", "Q2", ...]

passages ─► classify_product(description)        rule table -> tier + verbatim quotes
passages ─► gap_analysis                          per obligation: keyword hits -> Evidenced/Partial/Missing

for each question:
   match_obligation(question)        which of the 14 obligations is this about?
   company evidence                  obligation keyword hits first, then meaning search (max 4 passages)
   law context                       obligation Article first, then semantic search hits (max 7 excerpts)
   NOTICE if the obligation is Missing ("no company document covers X")
   LLM draft (JSON: answer, missing)      or offline template if no key
   guards + verification             see section 5
   status: ready | needs_input | review

render: evidence_pack.md / .html / .json, gaps.csv, ai_act_position.md
```

### Gap analysis rules
For each obligation, count distinct obligation keywords found across all passages (the file title and
heading are included in the searched text):

| Distinct keywords | Status |
|---|---|
| 2 or more | Evidenced |
| 1 | Partial |
| 0 | Missing |

This is keyword triage that shows where to look first. It is not a compliance finding, and the pack says so.

### Classification
`classification.classify_product` first removes sentences that state what the product is NOT for (for example "not intended for promotion decisions"), then runs every rule in `risk_rules.py`. A rule matches when its regex matches the
description (and its optional context regex, for example workplace words for the emotion ban).
Precedence: prohibited, then high-risk, then transparency, then none. High-risk results also quote
Article 6(2)/6(3) and the profiling caveat, plus the Omnibus date note. It flags and never clears.

## 5. Trust model: how fabrication is prevented

The model is treated as untrusted. Deterministic code checks its output.

1. **Grounded prompts.** Law facts only from supplied excerpts. Company facts only from supplied
   passages, each cited as `[doc: file § n]`. Missing facts become `[NEEDS INPUT: ...]`.
2. **No absence claims.** The prompt forbids "we do not X" and "we lack X".
3. **Missing-obligation guard.** If the matched obligation has no supporting document, the answer is
   forced to contain `[NEEDS INPUT ...]` and its status becomes `needs_input`, whatever the model said.
4. **Citation verification** (`laws.check_citations`):
   - `nonexistent`: cites an Article/Annex that is not in the Act (hallucination).
   - `unsupported`: real, but never shown to the model (ungrounded). Names mentioned inside shown
     excerpts and the date note count as shown.
5. **Document reference check.** Every `[doc: ...]` must be one of the passages supplied.
6. **Claim guards.** Negative claims ("we do not...") and forward commitments ("we will...") are flagged
   for human confirmation.
7. **Status resolution:** `needs_input` if input is missing, else `review` if any check failed or a
   claim was flagged or the model cited no company document, else `ready`.

Offline mode (no API key or `--no-llm`) never produces `ready`.

## 6. Code scanner

`scanner.scan(path)` walks source and docs (skipping `.git`, `.venv`, `node_modules`, `data`, etc.,
files under 300 KB) and applies regex rules. Each finding has: citation (asserted to exist in the Act),
severity (critical, high, medium, low), rule id, `file:line`, why, and fix.

| Rule | Article | Fires when |
|---|---|---|
| emotion-or-biometric | Art. 5 | emotion/biometric libraries or terms appear |
| employment-use-case | Annex III | candidate/applicant handling plus AI or scoring |
| automated-decision-no-human | Art. 14 | auto reject/approve with no human-review pattern in that file |
| protected-attribute-as-feature | Art. 10 | gender, age, race etc. in feature/data code |
| no-ai-disclosure | Art. 50 | AI calls exist but no "you are talking to AI" text anywhere |
| no-event-logging | Art. 12 | AI calls exist but no logging code anywhere |
| no-incident-procedure | Art. 73 | hiring signals but "incident" appears nowhere |
| no-human-oversight-mechanism | Art. 14 | hiring code with no review/override pattern repo-wide |

It is a smoke detector. Silence is not evidence of compliance.

## 7. MCP tools

Run `python -m policylens.mcp_server` (stdio, or `policylens-mcp` after `pip install -e .`). Config example: `mcp_config.example.json`.

| Tool | Input | Output |
|---|---|---|
| `search_law` | query, top_k | ranked excerpts with scores |
| `get_article` | parent id such as `art_5`, `annex_III` | full text |
| `classify_product` | description | cited answer or retrieval-only evidence |
| `scan_codebase` | repo path | findings JSON |
| `evidence_gaps` | docs folder | per-obligation status JSON |
| `verify_citations` | text | cited and nonexistent Articles |

## 8. Configuration

`.env` (never committed; template in `.env.example`):

| Variable | Meaning |
|---|---|
| `OPENROUTER_API_KEY` | preferred provider |
| `OPENROUTER_MODEL` | model slug, default `anthropic/claude-sonnet-4.5` |
| `ANTHROPIC_API_KEY` | alternative provider |
| `ANTHROPIC_MODEL` | default `claude-sonnet-4-5` |

With no key everything still runs in retrieval-only or offline mode.

## 9. Extending it

- **Add an obligation:** append to `OBLIGATIONS` in `obligations.py` with a real Article, a plain
  `ask`, and document `keywords`. Optionally add question phrases in `QUESTION_HINTS` in `pack.py`.
- **Add a classification rule:** append to `RULES` in `risk_rules.py` with `id`, `tier`, `cite`, `rx`,
  a verbatim `marker`, and `why`. The evals fail if the marker is not in the Act.
- **Add a scanner rule:** add a regex and a block in `scanner.scan` using `add(...)`, which asserts the citation exists.
- **Add an eval:** use `check(name, condition)` in `evals/evidence.py`.

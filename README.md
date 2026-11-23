# PolicyLens

AI governance copilot for the **EU AI Act** (Regulation (EU) 2024/1689).

Describe an AI product → get **risk category**, **citations**, and **when it applies** (including Digital Omnibus dates).

**Golden rule:** no claim without a citation. If evidence is weak, say “not sure.”

Repo: https://github.com/bhushan-01/policylens

---

## Pipeline

```text
PDF → clean text → Article/Annex chunks → split (≤512 tokens)
 → embeddings → search → answer / agent / MCP / web UI
```

Learning walkthrough: see **[LEARNING.md](LEARNING.md)**.

---

## Setup

```bash
cd ~/Documents/policylens
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# add OPENROUTER_API_KEY=...  (or ANTHROPIC_API_KEY)
```

On macOS, if `python` is missing, use `.venv/bin/python` or activate the venv first.

---

## What this project is (read this)

See **[WHAT_IS_THIS.md](WHAT_IS_THIS.md)**.

**Main command (recommended):**

```bash
python src/policylens.py "We build CV screening software for HR teams"
```

That runs a sensible checklist: prohibited → high-risk → transparency → cited answer.

## Commands

```bash
# Main product flow (use this)
python src/policylens.py "We build CV screening software for HR teams"

# Web UI (same idea, browser)
python src/app.py

# Search only
python src/search.py "Can I detect employees' emotions with AI?"

# Evals
python src/eval_retrieval.py
python src/eval_assertions.py
python src/eval_assertions.py --llm

# Older one-shot answer
python src/classify.py "We build CV screening software for HR teams"

# Tool-calling agent demo (learning / edge cases; not the main UX)
python src/agent.py "Facial recognition in a shopping mall"

# MCP server (stdio) — used by Cursor / Claude Desktop
python src/mcp_server.py
```

### Cursor MCP

Copy `mcp_config.example.json` into your Cursor MCP settings (update paths if needed). Tools:

- `search_law`
- `get_article`
- `classify_product`

---

## Rebuild data (only if PDF/chunking changes)

```bash
python src/extract_text.py
python src/clean_text.py
python src/chunk.py
python src/split_chunks.py
python src/embed_chunks.py
python src/token_check_split.py
```

---

## File map

### Data
| File | Role |
|---|---|
| `data/eu_ai_act.pdf` | Source law |
| `data/ai_act_raw.txt` / `ai_act_clean.txt` | Extracted / cleaned text |
| `data/chunks.json` | 126 Article/Annex chunks |
| `data/chunks_split.json` | 843 retrieval pieces |
| `data/embeddings.npy` | 843×384 vectors |
| `data/eval_questions.json` | Retrieval hit-rate set |
| `data/eval_assertions.json` | End-to-end assertion set |

### Code
| File | Role |
|---|---|
| `src/extract_text.py` … `chunk.py` | Ingest + structure |
| `src/split_chunks.py` / `embed_chunks.py` | Fit token limit + embed |
| `src/search.py` | Dense + keyword hybrid search |
| `src/answer.py` / `classify.py` | RAG answers (OpenRouter/Anthropic) |
| `src/agent.py` | Workflow / tool-calling agent |
| `src/mcp_server.py` | MCP tools for Cursor |
| `src/app.py` | Gradio web UI |
| `src/eval_retrieval.py` / `eval_assertions.py` | Quality checks |

---

## Known checks

| Check | Expected |
|---|---|
| Cleaner removed lines | 287 |
| Articles / Annexes | 113 / 13 |
| Split chunks >512 tokens | 0 |
| Retrieval hit @8 | 12/12 (100%) |

---

## Legal freshness

Injected Omnibus dates (not in 2024 PDF):

- Annex III / Art. 6(2): **2 December 2027**
- Annex I / Art. 6(1): **2 August 2028**

---

## Status

| Area | Status |
|---|---|
| RAG pipeline | ✅ |
| OpenRouter answers | ✅ |
| Agent | ✅ |
| MCP server | ✅ |
| Web UI | ✅ |
| Assertion evals | ✅ |
| Deeper LLM-as-judge / production hardening | Future |

## Evidence Pack (vendor product)

Risk classification is free elsewhere. The paid pain is the **buyer questionnaire**:
an AI vendor must answer a customer's EU AI Act due-diligence questions with evidence.
The Evidence Pack does that for AI hiring / HR-tech vendors (Annex III point 4).

```bash
python src/evidence_pack.py --docs data/sample_company --questionnaire data/sample_questionnaire.md
python src/evidence_pack.py ... --no-llm     # deterministic offline mode
python src/eval_evidence.py                  # 81 safety evals, no API key needed
python src/code_scan.py data/sample_repo     # scan a codebase for AI Act red flags
python src/app.py                            # web UI, "Evidence Pack" tab
```

Outputs (in `out/`): `evidence_pack.md|html|json`, `gaps.csv` (what to fix first), and
`ai_act_position.md` (public-page draft built only from evidenced facts).
A committed sample lives in `examples/` (fictional company).

What it does:
1. **Classifies** the product with 27 rules covering every Annex III area, all Article 5 bans and Article 50 cases, quoting verbatim law text (`src/risk_rules.py`).
2. **Gap analysis** against 14 buyer-expected obligations (Art. 4, 9-15, 17, 43, 49, 72, 73, 86):
   Evidenced / Partial / Missing, with the vendor document each one was found in.
3. **Drafts questionnaire answers**: law facts only from retrieved Articles, company facts only
   from the vendor's own docs, everything else becomes `[NEEDS INPUT: ...]`.
4. **Verifies every answer**: cited Articles must exist and have been shown to the model; document
   references must be real; negative claims and forward commitments are flagged for review.
   If an obligation has no supporting document, the answer is forced to NEEDS INPUT.

Limits to know: gap status is keyword triage, not a compliance finding; classification is a
keyword first pass on the intended-purpose text (it flags, never clears); dates rely on the Omnibus note in `src/answer.py`
and must be re-checked against the Official Journal. Not legal advice.

Business validation plan: [docs/CUSTOMER_DISCOVERY.md](docs/CUSTOMER_DISCOVERY.md).

## Code scanner and editor tools

`src/code_scan.py` scans a repository for patterns that deserve a human look: emotion/biometric
libraries (Art. 5), automated reject/approve with no human step (Art. 14), missing logging (Art. 12),
no AI disclosure (Art. 50), protected attributes as features (Art. 10), no incident procedure (Art. 73).
Each finding has file:line, a verified Article, why, and a fix. The MCP server exposes it as
`scan_codebase`, plus `evidence_gaps` and `verify_citations`, so Cursor or Claude Code can call them.

Outreach and interview material: [docs/OUTREACH.md](docs/OUTREACH.md). Cursor instructions: [AGENTS.md](AGENTS.md).

## Quick commands

`make test` (81 offline evals) · `make demo` / `make demo-offline` · `make scan` · `make ui` · `make mcp`

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

## Commands

```bash
# Search
python src/search.py "Can I detect employees' emotions with AI?"

# Retrieval eval (expect 12/12)
python src/eval_retrieval.py

# Assertion eval (fast / with LLM)
python src/eval_assertions.py
python src/eval_assertions.py --llm

# Full answer
python src/classify.py "We build CV screening software for HR teams"

# Agent (tool loop via OpenRouter if key set)
python src/agent.py "Facial recognition in a shopping mall"

# Web UI
python src/app.py

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

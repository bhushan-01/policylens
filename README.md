# PolicyLens

AI governance copilot for the **EU AI Act** (Regulation (EU) 2024/1689).

Describe an AI product → get risk category, citations, and (when relevant) updated application dates.

**Golden rule:** no claim without a citation. If retrieval is weak, say “not sure” instead of guessing.

## Pipeline

```text
PDF → clean text → Article/Annex chunks → split to ≤512 tokens
    → embeddings → search → answer (Claude) / agent workflow
```

## Setup

```bash
cd ~/Documents/policylens
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional (for generated answers / tool-calling agent):

```bash
cp .env.example .env
# put ANTHROPIC_API_KEY=... in .env
```

## Rebuild data (already done once)

```bash
python src/extract_text.py
python src/clean_text.py
python src/chunk.py
python src/split_chunks.py
python src/embed_chunks.py
```

## Use it

```bash
# Semantic search
python src/search.py "Can I detect employees' emotions with AI?"

# Retrieval eval (hit rate @5)
python src/eval_retrieval.py

# Classify / answer (needs Anthropic key for full text; else shows evidence)
python src/classify.py "We build CV screening software for HR teams"

# Simple agent workflow (tool loop if key set; else deterministic checklist)
python src/agent.py "Facial recognition camera in a shopping mall"
```

## Project layout

```text
data/
  eu_ai_act.pdf, ai_act_raw.txt, ai_act_clean.txt
  chunks.json, chunks_split.json
  embeddings.npy, embeddings_meta.json
  eval_questions.json
src/
  extract_text.py, clean_text.py, chunk.py
  split_chunks.py, embed_chunks.py
  search.py, eval_retrieval.py, answer.py, classify.py, agent.py
```

## Legal freshness note

The 2024 PDF does not include later **Digital Omnibus on AI** delays:

- Annex III / Article 6(2) high-risk: **2 December 2027**
- Annex I / Article 6(1) high-risk: **2 August 2028**

PolicyLens injects these dates in the answer prompt.

## Status

- Steps 1–9: extract → clean → chunk → split → embed → search → retrieval eval
- Step 10 / agent: wired; full LLM answers need `ANTHROPIC_API_KEY`
- MCP server: not built yet (Phase 4)

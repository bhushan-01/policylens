# PolicyLens

AI governance copilot for the **EU AI Act** (Regulation (EU) 2024/1689).

Describe an AI product in a few sentences. PolicyLens maps it to the Act and answers with:

- **Risk category:** Prohibited / High-risk / Transparency obligations / Minimal risk
- **Why:** with exact Article or Annex citations
- **When it applies:** including updated Digital Omnibus dates where relevant

**Golden rule:** no claim without a citation. If retrieval cannot find the relevant law text, PolicyLens says it is not sure instead of guessing.

## Pipeline (RAG)

```text
PDF → raw text → clean text → chunks (+ metadata) → embeddings → search → LLM answer with citations
```

## Project layout

```text
policylens/
├── data/
│   ├── eu_ai_act.pdf       # official AI Act PDF
│   ├── ai_act_raw.txt      # extracted text
│   ├── ai_act_clean.txt    # headers/footers removed
│   └── chunks.json         # Article / Annex chunks
└── src/
    ├── read_pdf.py
    ├── extract_text.py
    ├── clean_text.py
    ├── chunk.py
    ├── embed_demo.py
    └── token_check.py
```

## Setup

```bash
cd ~/Documents/policylens
python3 -m venv .venv
source .venv/bin/activate
pip install pypdf sentence-transformers
```

Run scripts from the project root:

```bash
python src/extract_text.py
python src/clean_text.py
python src/chunk.py
python src/embed_demo.py
python src/token_check.py
```

## Status

- Steps 1–6 done: extract, clean, chunk (113 Articles + 13 Annexes), embedding demos
- Next: split long chunks for the 512-token limit, embed the full corpus, then retrieval + generation

## Note on law freshness

The 2024 PDF does not include later Digital Omnibus delays for high-risk obligations. PolicyLens must account for those dates separately from the PDF text.

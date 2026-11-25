# PolicyLens — Whole Project Explained (Study Guide)

**Open this file when you want to understand or explain the project.**  
Written in simple English first. Technical terms are explained when they appear.

Related deeper docs:
- `docs/learning/WHAT_IS_THIS.md` — one-page product idea  
- `docs/learning/KNOWLEDGE_BASE.md` — concepts + glossary  
- `docs/learning/LEARNING.md` — file-by-file practice checklist  
- `docs/learning/MASTERY.md` — your progress tracker  
- `docs/ARCHITECTURE.md` — technical design + trust model  

---

## 0. One-sentence version

**PolicyLens finds the right pages of the EU AI Act, then explains how the law applies to an AI product — with citations it can check — and can draft buyer-questionnaire answers from a vendor’s own documents.**

---

## 1. What problem does this solve?

### Everyday explanation

Someone builds AI (CV screener, chatbot, face camera, emotion tool).

They ask:

> “Does the EU AI Act ban this, call it high-risk, or only require a disclosure — and **which Article** says so?”

If they only ask ChatGPT, it may:
- sound confident  
- cite the **wrong** Article  
- invent rules that are not in the law  

For law, that is dangerous.

### Who uses it

| Who | Why |
|---|---|
| AI vendors (especially hiring / HR-tech) | Answer a customer’s AI Act questionnaire with proof |
| Founders / PMs | Quickly classify a product idea |
| Engineers | Scan code for AI Act red flags |
| You in Cursor | Call law tools via MCP |

### What it is NOT

- Not a law firm  
- Not formal legal advice  
- Not a full compliance platform  
- Not “an agent just because agents are cool”

---

## 2. Interview pitches (memorize these)

### 30 seconds

> PolicyLens helps AI vendors map products to the EU AI Act with verified citations. Classification alone is free elsewhere. The paid pain is answering buyer due-diligence questionnaires from the vendor’s own docs without inventing law or company facts. We retrieve real Articles, draft answers, then machine-check every citation.

### 2 minutes

> EU buyers block deals until vendors answer AI Act questionnaires. Chatbots hallucinate Articles. We index Regulation (EU) 2024/1689 as 843 searchable pieces with embeddings, retrieve relevant law, and classify against Annex III / Article 5 / Article 50.  
> The Evidence Pack loads vendor docs, scores readiness against 14 obligations, drafts answers where law facts come only from retrieved text and company facts only from their docs, and forces `[NEEDS INPUT]` when evidence is missing. Citation verification catches nonexistent or ungrounded Articles. We also have a code scanner and MCP tools. Offline evals must stay green. Not legal advice.

---

## 3. The law mental model (no code yet)

### How the Act is organized

| Part | What it is | Example |
|---|---|---|
| Recitals | Background / “why” | Not the hard rules |
| **Articles** | The actual rules | Article 5 = prohibited practices |
| **Annexes** | Lists Articles point to | Annex III = many high-risk use cases |

### Risk ladder (always think in this order)

1. **Prohibited?** → mostly **Article 5**  
   Example: workplace emotion recognition  
2. **High-risk?** → **Article 6 + Annex III**  
   Example: CV screening / hiring AI  
3. **Transparency?** → **Article 50**  
   Example: many chatbots  
4. **Else** → minimal / unclear → say **not sure**

### Golden rules of PolicyLens

1. **No claim without a citation**  
2. **Law facts** only from retrieved Act text  
3. **Company facts** only from vendor docs  
4. Missing proof → **`[NEEDS INPUT]`**, never invent  
5. **Not legal advice**

### Dates note

The 2024 PDF is outdated on some deadlines. Code injects a Digital Omnibus note (`policylens/omnibus.py`):
- Stand-alone high-risk (Annex III / Art. 6(2)): **2 December 2027**  
- High-risk in regulated products (Annex I / Art. 6(1)): **2 August 2028**

---

## 4. The core technique: RAG

**RAG = Retrieval-Augmented Generation**

### Simple English

Like an **open-book exam**:
- Bad: answer from memory → invent  
- Good: find the page first → answer from that page → cite it  

### In PolicyLens

1. **Retrieve** relevant Articles/Annex pieces  
2. **Generate** an answer using only that evidence (+ Omnibus note)

### Why RAG here

- The full Act is huge  
- Most questions need only a few Articles  
- Citations become natural because the model is given the exact excerpts  

### YouTube (watch these for RAG)

| Video | Link | Why |
|---|---|---|
| IBM: What is RAG? | https://www.youtube.com/watch?v=T-D1OfcDW1M | Best short explanation |
| RAG for beginners | https://www.youtube.com/watch?v=GwEixEJX9F8 | Open-book analogy |
| Why LLMs hallucinate | https://www.youtube.com/watch?v=cfqtFvWOfg0 | Why golden rule exists |
| EU AI Act explained | https://www.youtube.com/watch?v=GELAXU9XReI | Risk ladder |

**Optional full course (embeddings + RAG + agents):**  
https://www.youtube.com/watch?v=WIW5hN-hApQ  

**Not first for PolicyLens:** Karpathy “Let’s build GPT”  
https://www.youtube.com/watch?v=kCc8FmEb1nY  
That teaches how GPT is *built*. PolicyLens *calls* a GPT via API. Watch later for depth.

---

## 5. End-to-end pipeline

```text
PDF (data/eu_ai_act.pdf)
  → extract text          (ingest/extract_text.py)  → ai_act_raw.txt
  → clean junk            (ingest/clean_text.py)    → ai_act_clean.txt
  → chunk by Article      (ingest/chunk.py)         → chunks.json (126)
  → split long pieces     (ingest/split_chunks.py)  → chunks_split.json (843)
  → embed                 (ingest/embed_chunks.py)  → embeddings.npy (843×384)
  → search by meaning     (search.py)
  → classify / checklist / evidence pack
  → LLM drafts answer (optional)
  → verify citations      (laws.py)
  → render outputs        (render.py) → out/
```

### Key numbers (if these change, stop and investigate)

| Thing | Expected |
|---|---|
| Articles | 113 |
| Annexes | 13 |
| Parent chunks | 126 |
| Split pieces | 843 |
| Embedding size | 843 × 384 |

### Why split chunks?

The embedding model only “reads” ~**512 tokens**. Longer text is silently cut off.  
So long Articles are split into smaller pieces, but each piece still knows its parent Article for citation.

---

## 6. Architecture (how pieces talk)

```text
                 DATA (built once, committed)
                 PDF → chunks → embeddings
                           │
                           ▼
              ┌────────────────────────┐
              │  search.py  (find law) │
              └────────────┬───────────┘
                           │ excerpts
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   checklist/answer   classification    pack.py
   (Classifier)       (rule first pass) (Evidence Pack)
         │                 │                 │
         └────────┬────────┴────────┬────────┘
                  ▼                 ▼
            laws.py (verify)   company.py + obligations.py
                  │
                  ▼
         CLI / ui.py / mcp_server.py / agent.py / scanner.py
                  │
                  ▼
               evals/  (prove it works)
```

**Mental model:** the LLM is a **writer**. Search + rules + verification are the **source of truth**.

---

## 7. Two products on one law index

### A) Classifier

**Question:** “How does the Act apply to my product?”

**Run:**
```bash
python -m policylens.checklist "We build CV screening software for HR teams"
```

**Flow:**
1. Rule-based first pass (`risk_rules.py` + `classification.py`)  
2. Checklist search: prohibited → high-risk → transparency (`checklist.py`)  
3. LLM writes cited answer (`answer.py`) if API key exists  

### B) Evidence Pack (business direction)

**Question:** “How do I answer my customer’s AI Act questionnaire, with proof?”

**Run:**
```bash
python -m policylens.pack --docs examples/sample_company --questionnaire examples/sample_questionnaire.md
# or offline:
python -m policylens.pack ... --no-llm
```

**Flow:**
1. Load vendor docs as passages (`company.py`)  
2. Classify product  
3. Gap analysis vs 14 obligations (`obligations.py`) → Evidenced / Partial / Missing  
4. Draft each answer (law from retrieval, company from docs)  
5. Guards + citation checks (`laws.py`)  
6. Render `evidence_pack.md/html/json`, `gaps.csv`, `ai_act_position.md` (`render.py`)

**Why this is the product:** classification checkers already exist for free. The paid pain is the **buyer questionnaire**.

---

## 8. Repository map (what to master)

### Tier 1 — Critical

| File | Responsibility |
|---|---|
| `policylens/search.py` | Find relevant law pieces (embeddings + keyword boost) |
| `policylens/laws.py` | Exact lookup, quotes, citation verification |
| `policylens/pack.py` | Evidence Pack pipeline |
| `policylens/risk_rules.py` | 27 classification rules |
| `policylens/classification.py` | Apply rules, quote law, never “clear” a product |
| `policylens/obligations.py` | 14 buyer-expected obligations |
| `evals/evidence.py` | Offline safety checks (must stay green) |
| `data/chunks_split.json` + `embeddings.npy` | The searchable law index |

### Tier 2 — Important

| File | Responsibility |
|---|---|
| `company.py` | Vendor docs → citable passages |
| `answer.py` / `checklist.py` | Classifier answer + CLI |
| `llm.py` | OpenRouter / Anthropic wrapper |
| `render.py` | Write pack outputs |
| `omnibus.py` | Date caveat |
| `scanner.py` | Code red-flag scanner |
| `ingest/*` | One-time PDF → embeddings pipeline |

### Tier 3 — Supporting

| File | Responsibility |
|---|---|
| `ui.py` | Gradio web UI |
| `mcp_server.py` | Cursor/Claude tools |
| `agent.py` | Free tool-calling agent (learning) |
| `paths.py` / `config.py` | Paths + `.env` |
| `examples/*` | Demo company, questionnaire, sample output |
| `docs/*` | Guides + business docs |

### Tier 4 — Don’t memorize

`.venv/`, `policylens.egg-info/`, `.env`, generated `out/`, every line of packaging configs.

**Not in this project:** React frontend, SQL database, auth system, cloud deploy config.  
The “database” is JSON files + a NumPy array.

---

## 9. Technology stack (simple table)

| Technology | Simple English | Where |
|---|---|---|
| Python | Language everything is written in | whole repo |
| pypdf | Pull text out of the PDF | `ingest/extract_text.py` |
| sentence-transformers + BGE-small | Turn text into meaning fingerprints (384 numbers) | `embed_chunks.py`, `search.py` |
| NumPy | Fast math on those number arrays | `search.py`, `embeddings.npy` |
| OpenRouter / Anthropic | Cloud LLM APIs for writing answers | `llm.py` |
| Gradio | Quick web UI | `ui.py` |
| MCP | Protocol so Cursor can call your tools | `mcp_server.py` |
| regex rules | Pattern matching for classification & scans | `risk_rules.py`, `scanner.py` |

---

## 10. Important concepts (with analogy)

### Embedding
- **Simple:** a fingerprint of meaning as a list of numbers  
- **Analogy:** GPS coordinates in “meaning space”  
- **In project:** each of 843 pieces → 384 numbers in `embeddings.npy`  
- **YouTube:** https://www.youtube.com/watch?v=OATCgQtNX2o  

### Cosine similarity
- **Simple:** score of how aligned two fingerprints are (near 1 = similar)  
- **In project:** query embedding vs all chunk embeddings → top matches  
- **YouTube:** https://www.youtube.com/watch?v=SyEILVYamlY  

### Hybrid search
- **Simple:** meaning search + keyword bonus  
- **Why:** legal phrases like “social scoring” / “emotion” sometimes need exact words  
- **In project:** `search.py` (`BOOST_PHRASES`)  

### Hallucination
- **Simple:** model invents confident nonsense  
- **In project:** blocked by retrieval + `laws.check_citations` + `[NEEDS INPUT]`  

### Agent vs checklist
- **Checklist (`checklist.py`):** fixed steps you wrote (better for compliance)  
- **Agent (`agent.py`):** model chooses tools in a loop (good for learning / hard cases)  

### MCP
- **Simple:** a standard plug so AI apps (Cursor) can use your tools  
- **In project:** `search_law`, `get_article`, `classify_product`, `scan_codebase`, `evidence_gaps`, `verify_citations`  
- **YouTube:** https://www.youtube.com/watch?v=PLyCki2K0Lg  

---

## 11. Trust model (why it’s safer than ChatGPT)

The LLM is treated as **untrusted**. Deterministic Python checks its output:

1. Law only from supplied excerpts  
2. Company only from supplied passages (`[doc: file § n]`)  
3. Missing obligation → force `[NEEDS INPUT]`  
4. Citation must **exist** in the Act  
5. Citation must have been **shown** to the model  
6. Negative claims / “we will…” flagged for human review  

Answer statuses: `ready` | `needs_input` | `review`  
Offline / `--no-llm` never produces `ready`.

---

## 12. How to run it

```bash
cd ~/Documents/policylens
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
cp .env.example .env   # optional API key

make test              # offline safety evals
make demo-offline      # evidence pack without LLM
make demo              # evidence pack with LLM if key set
make scan              # code scanner demo
make ui                # web UI
make mcp               # MCP server
```

Useful direct commands:
```bash
python -m policylens.checklist "CV screening for HR teams"
python -m policylens.search "employee emotion recognition"
python -m policylens.pack --docs examples/sample_company --questionnaire examples/sample_questionnaire.md
python -m evals.evidence
python -m evals.retrieval
```

---

## 13. Suggested study order (notes + YouTube)

| Day | Study this | Watch | Then open |
|---|---|---|---|
| 1 | Sections 0–3 of this file | IBM RAG + EU AI Act videos | `README.md`, `WHAT_IS_THIS.md` |
| 2 | Section 5 pipeline | embeddings video | `data/`, `ingest/` |
| 3 | Search | Hugging Face embeddings video | `search.py` |
| 4 | Classifier | — | `checklist.py`, `risk_rules.py` |
| 5 | Evidence Pack | — | `pack.py`, `obligations.py` |
| 6 | Trust + evals | hallucination video | `laws.py`, `evals/evidence.py` |
| 7 | Interfaces | MCP / tool-calling videos | `mcp_server.py`, `agent.py`, `ui.py` |

Track progress in `docs/learning/MASTERY.md`.

---

## 14. Note template (copy per topic)

```text
TOPIC: ____________________

1) In my own words:
________________________________

2) Analogy:
________________________________

3) Files in my project:
________________________________

4) What would break if I removed this?
________________________________

5) 30-second interview answer:
________________________________
```

---

## 15. Bottom line

PolicyLens is not “we have an agent.”

The real invention is:

> **structured law + meaning search + cited answers + checks that the citations are right.**

That is what you should be able to explain in interviews.

---

*Last aligned with package layout: `policylens/` package, `evals/`, `examples/`, `data/`.*

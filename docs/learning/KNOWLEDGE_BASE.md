# PolicyLens — Knowledge Base

Use this document to learn what the project is really about.  
You can study it offline or with another tutor. It is not a coding tutorial.

---

## 1. The real problem (why this exists)

People build AI products:

- CV / resume screening tools  
- chatbots  
- face cameras  
- emotion detection at work  
- credit / loan scoring helpers  

Then they ask:

> “How does the **EU AI Act** apply to my product?”

They need:

1. A **risk category** (banned / high-risk / transparency / probably fine)  
2. A **reason** grounded in the law  
3. The **Article or Annex** that supports that reason  
4. Preferably **when** the rule starts applying  

### Why a normal chatbot is not enough

A general chatbot (ChatGPT, Claude, etc.) may:

- sound confident  
- cite the wrong Article  
- mix up dates  
- invent rules that are not in the text  

For law-related answers, “sounds right” is dangerous.

### What PolicyLens is

**PolicyLens is an EU AI Act lookup + explanation system.**

You describe a product → it finds relevant parts of the real law → it explains with citations → if unsure, it should say so.

**One-sentence definition:**

> PolicyLens helps builders map an AI product to the EU AI Act using retrieved law text and citations, instead of guessing.

**What it is not:**

- not a law firm  
- not formal legal advice  
- not a full compliance checklist platform (v0)  
- not “agents for the sake of agents”

---

## 2. The law it uses

### Main document

- **EU AI Act** = Regulation (EU) 2024/1689  
- Stored in the project as `data/eu_ai_act.pdf` (144 pages)

### How the Act is organized (important mental model)

| Part | What it is | Example |
|---|---|---|
| Recitals | “Why” the law exists (background) | Not the hard rules |
| Articles | The actual rules | Article 5 = prohibited practices |
| Annexes | Lists / details that Articles point to | Annex III = many high-risk use cases |

### Risk ladder (the product logic)

When classifying a product, think in this order:

1. **Prohibited?** → mostly **Article 5**  
   Example: emotion recognition in the workplace (with narrow exceptions)

2. **High-risk?** → **Article 6** + **Annex I / Annex III**  
   Example: AI used to analyse and filter job applications (hiring)

3. **Transparency obligations?** → **Article 50** (and related)  
   Example: many chatbots that interact with people

4. **Otherwise** → often minimal / unclear → say **not sure** rather than inventing

### Golden rule of PolicyLens

> **No claim without a citation.**  
> If retrieval does not find good evidence, say “I’m not sure.”

### Important date update (not fully in the 2024 PDF)

Later EU updates (Digital Omnibus on AI) delayed some high-risk start dates:

- Stand-alone high-risk (Annex III / Art. 6(2)): **2 December 2027**  
- High-risk in regulated products (Annex I / Art. 6(1)): **2 August 2028**

PolicyLens must mention these when talking about “when it applies,” because the original PDF alone is outdated on those dates.

---

## 3. The core technique: RAG

**RAG = Retrieval-Augmented Generation**

Analogy: **open-book exam**

- Bad approach: force the student to memorize the whole textbook, then answer from memory  
- RAG approach: let the student look up the relevant pages, then answer from those pages  

### In PolicyLens

1. **Retrieve** the most relevant Articles/Annex pieces for the user’s product  
2. **Generate** an answer using only that evidence (+ known Omnibus date note)

### Why RAG fits this project

- The full Act is huge (~150k tokens of text)  
- Most questions need only a few Articles  
- Citations become natural because the model is given the exact excerpts  

---

## 4. End-to-end pipeline (what was built)

```text
PDF
 → extract text
 → clean page junk
 → chunk by Article/Annex
 → split long chunks (so embeddings can read them)
 → embed chunks into vectors
 → search by meaning
 → checklist (prohibited → high-risk → transparency)
 → LLM writes cited answer
```

### Stage A — Make the law machine-readable

| Step | Idea |
|---|---|
| Extract | PDF text is messy; pull it into plain text |
| Clean | Remove repeating headers/footers carefully |
| Chunk | One Article/Annex = one unit you can cite |

Key lesson from cleaning:  
Be precise. A lazy rule (“delete any line containing ELI”) can delete real law text.

Key lesson from chunking:  
Use the document’s own structure (Article, Annex, Chapter).  
Also: after Annexes start, stop treating “Article …” lines inside annex tables as real Articles (fake Article 49 bug).

### Stage B — Make the law searchable by meaning

| Concept | Meaning |
|---|---|
| Embedding | A list of numbers representing meaning (“GPS for text”) |
| Similar meaning | Vectors point in similar directions |
| Cosine similarity | Score of how aligned two vectors are (near 1 = similar) |

Example:

- User says: “software that screens CVs”  
- Law says: “analyse and filter job applications”  
- Few shared words, similar meaning → embeddings can still match them  

Token limit lesson:

- The embedding model only “reads” about **512 tokens**  
- Longer text is silently truncated  
- So long Articles must be split into smaller pieces while keeping the parent Article number for citation  

### Stage C — Answer

Recommended product flow (`policylens/checklist.py`):

1. Search for prohibited evidence  
2. Search for high-risk evidence  
3. Search for transparency evidence  
4. Merge best evidence  
5. Ask LLM to write: risk + why + citations + dates  

This checklist is more useful for governance than a fancy free-roaming agent.

---

## 5. Normal RAG vs Agent (clear distinction)

### Normal RAG answer (`checklist.py`)

Fixed plan written by you:

```text
search → (optional checklist searches) → write answer
```

The model mainly **writes**.

### Tool-calling agent (`agent.py`)

The model can choose actions:

```text
think → call search_law → read → call get_article → read → write answer
```

The model **investigates**, then writes.

### Honest judgment for PolicyLens

| Approach | Useful for this product? |
|---|---|
| Checklist RAG (`checklist.py`) | **Yes — main product** |
| One-shot RAG (`checklist.py`) | Yes — simple mode |
| Free tool-calling agent | Optional / learning / hard cases |
| MCP server | Useful if you want Cursor/Claude Desktop to call PolicyLens tools |
| Web UI | Same brain, nicer interface |

For learning AI systems, building an agent is valuable.  
For the actual EU AI Act product, **checklist + citations** is the sensible core.

---

## 6. What each major file is for (map)

### Data

| File | Role |
|---|---|
| `data/eu_ai_act.pdf` | Source law |
| `data/ai_act_raw.txt` | Extracted text |
| `data/ai_act_clean.txt` | Cleaned text |
| `data/chunks.json` | 113 Articles + 13 Annexes |
| `data/chunks_split.json` | Smaller retrieval pieces |
| `data/embeddings.npy` | Meaning vectors for search |
| `data/eval_*.json` | Test questions / assertions |

### Code (conceptual groups)

| Group | Files | Job |
|---|---|---|
| Ingest | `extract_text.py`, `clean_text.py`, `chunk.py` | Law → structured text |
| Index | `split_chunks.py`, `embed_chunks.py`, `search.py` | Make law searchable |
| Product answer | `checklist.py`, `answer.py`, `checklist.py`, `app.py` | User asks → cited answer |
| Agent/MCP | `agent.py`, `mcp_server.py` | Tool loop / external tool access |
| Quality | `eval_retrieval.py`, `eval_assertions.py` | Prove it finds/answers correctly |

### Main command to remember

```bash
python -m policylens.checklist "describe your AI product"
```

---

## 7. Quality / evals mindset

“It runs” ≠ “it works.”

PolicyLens uses known checks, for example:

- cleaning removed a known number of junk lines  
- there are 113 Articles and 13 Annexes  
- retrieval hit rate on a small question set  
- assertion checks: did the answer mention the expected Article / risk words / dates?

This is the seed of AI product evals:

> Decide the right answer in advance, then measure whether the system hits it.

---

## 8. Example mental walkthrough

### Input

> “We build CV screening software for HR teams”

### What should happen conceptually

1. High-risk search should surface **Annex III** employment / recruitment language  
2. Article 6 explains that Annex III systems are high-risk (with some nuances/exceptions)  
3. Answer should say **high-risk**, cite Annex III (and usually Art. 6), mention obligations timing (Omnibus date for Annex III stand-alone systems)

### Another input

> “AI that detects employees’ emotions at work”

1. Should surface **Article 5** prohibited practices  
2. Answer should usually say **prohibited** (with narrow medical/safety exceptions if relevant)

If the system answers “high-risk chatbot rules” for workplace emotion detection, that is a failure even if the text is fluent.

---

## 9. Vocabulary cheat sheet

| Term | Plain meaning |
|---|---|
| EU AI Act | EU law regulating AI systems/products |
| Citation | Pointing to Article/Annex as evidence |
| Chunk | One searchable piece of the law |
| Metadata | Labels on a chunk (id, title, chapter…) |
| Embedding | Numbers representing meaning |
| Retrieval | Finding relevant chunks |
| Generation | LLM writing the final answer |
| RAG | Retrieve then generate |
| Agent | System where the model can choose tools/steps |
| MCP | Protocol so apps like Cursor can call your tools |
| Eval | Test that checks correctness, not just “no crash” |
| Hallucination | Confident wrong statement with no real support |

---

## 10. What to learn next (outside this repo)

If you want deeper understanding elsewhere, study these topics in order:

1. What the EU AI Act risk categories are (prohibited / high-risk / transparency)  
2. What RAG is and why people use it for private/domain documents  
3. What text embeddings are  
4. Why chunking strategy matters  
5. What evals are for AI products  
6. (Optional) tool-calling agents  
7. (Optional) MCP  

Suggested mindset:

- First understand the **product problem**  
- Then understand **RAG**  
- Only then worry about agents/MCP  

---

## 11. Bottom line

PolicyLens exists to answer:

> “What does the EU AI Act say about *my* AI product — and where does it say that?”

The important invention in this project is not “we have an agent.”

The important invention is:

> **structured law + meaning search + cited answers + checks that the citations are right.**

That is what the project is really about.

# PolicyLens

EU AI Act tooling with **verified citations**. Regulation (EU) 2024/1689.

**Golden rule:** no claim without a citation. If evidence is weak it says so, and it never declares a product compliant.

Repo: https://github.com/bhushan-01/policylens

## What it does

| Tool | For | What you get |
|---|---|---|
| **Evidence Pack** | AI vendors (first target: hiring / HR-tech) answering a customer's AI Act questionnaire | Risk classification, gap analysis against 14 buyer-expected obligations, cited draft answers, a fix-first list |
| **Classifier** | Anyone asking "how does the Act apply to my product?" | Rule-based first pass with verbatim law quotes, then a cited answer |
| **Code scanner** | Engineers | Red flags in a repo (emotion/biometrics, automated decisions with no human, missing logging, no AI disclosure) with file:line, Article and fix |
| **MCP server** | Cursor / Claude Code / Claude Desktop | The above as editor tools: `search_law`, `get_article`, `classify_product`, `scan_codebase`, `evidence_gaps`, `verify_citations` |
| **Evidence Tribunal** | Anyone who distrusts a chatty agent | Adversarial proof ledger: charges → defense → citation audit → verdict |
| **Web UI** | Non-technical users | Evidence Pack, Tribunal, and Classifier tabs |

Why the Evidence Pack: classification alone is free elsewhere (EU Commission checker, FLI, TÜV SÜD). The paid pain is the buyer questionnaire that blocks an EU deal.

## Quick start

```bash
git clone https://github.com/bhushan-01/policylens.git && cd policylens
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e . --no-deps
cp .env.example .env          # optional: OPENROUTER_API_KEY or ANTHROPIC_API_KEY
make test                     # 92 offline safety evals, no API key needed
make demo-offline             # evidence pack on a fictional company, deterministic
```

No key? Everything runs offline. A key only improves the wording of drafted answers.

## Commands

| Command | Does |
|---|---|
| `make test` | 92 offline safety evals |
| `make test-all` | plus retrieval hit-rate and assertion evals |
| `make demo` / `make demo-offline` | Evidence pack on `examples/sample_company` |
| `make scan` | Code scan of `examples/sample_repo` |
| `make ui` | Web UI |
| `make tribunal` | Evidence Tribunal sample run |
| `make mcp` | MCP server over stdio |
| `make docker` | Build Gradio container |
| `make ingest` | Rebuild the law index from the PDF (data is committed already) |

Direct use (also installed as console scripts):

```bash
python -m policylens.pack --docs my_docs/ --questionnaire q.md [--no-llm] [--out out/]   # policylens-pack
python -m policylens.checklist "We build CV screening software for HR teams"             # policylens
python -m policylens.scanner path/to/repo [--json]                                        # policylens-scan
python -m policylens.ui                                                                   # policylens-ui
python -m policylens.mcp_server                                                           # policylens-mcp
python -m policylens.tribunal "Talent acquisition ranking for applicants"                 # policylens-tribunal
python -m policylens.search "Can I detect employees' emotions with AI?"
```

Static landing page: open [`web/index.html`](web/index.html). Container: `docker build -t policylens . && docker run -p 7860:7860 policylens`.


Cursor / Claude Code MCP: copy `mcp_config.example.json` into your MCP settings and set the absolute paths.

## Repository layout

```
policylens/                  the package
  paths.py  config.py        locations and .env loading
  laws.py                    exact Article/Annex lookup, quotes, citation verification
  search.py                  hybrid semantic search over the Act
  classification.py          first-pass risk classification (uses risk_rules.py)
  risk_rules.py              27 rules: every Annex III area, Article 5 bans, Article 50, GPAI
  obligations.py             14 buyer-expected obligations tied to real Articles
  company.py                 vendor documents as citable passages
  pack.py                    Evidence Pack pipeline: gaps, drafting, verification guards
  render.py                  Markdown / HTML / JSON / CSV / position page output
  answer.py  checklist.py    classifier answer generation and CLI
  llm.py  omnibus.py         LLM wrapper; post-2024 date note
  scanner.py                 code scanner
  tribunal.py  agent.py      Evidence Tribunal (agent.py redirects here)
  blueprint.py               fix-first document outlines for gaps
  mcp_server.py  ui.py       editor tools and web UI
web/                         static landing page
  ingest/                    one-time PDF -> chunks -> embeddings pipeline
evals/                       evidence (83), retrieval, assertions; fixtures/
examples/                    fictional sample company, questionnaire, repo, sample output
data/                        the Act: pdf, text, chunks, split chunks, embeddings
docs/                        guides; docs/learning/ holds the study material
```

## Documentation

| Doc | What it covers |
|---|---|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Setup, running every tool, reading outputs, troubleshooting |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Data layer, modules, data flow, trust model, MCP tools, extending |
| [docs/SAFETY_AND_LIMITS.md](docs/SAFETY_AND_LIMITS.md) | What is guaranteed, what is not, the evals, privacy |
| [docs/BUSINESS_PLAN.md](docs/BUSINESS_PLAN.md) | Market findings, directions A/B/C, what is built, risks, next steps |
| [docs/CUSTOMER_DISCOVERY.md](docs/CUSTOMER_DISCOVERY.md) | Interview script and stop rule for validating the business |
| [docs/OUTREACH.md](docs/OUTREACH.md) | Finding and contacting the first 15 interviewees |
| [docs/learning/](docs/learning/) | `LEARNING.md`, `KNOWLEDGE_BASE.md`, `WHAT_IS_THIS.md` |
| [AGENTS.md](AGENTS.md) | Instructions for Cursor and other coding agents |
| [CHANGELOG.md](CHANGELOG.md) | What changed |

## Limits (read before relying on output)

- Not legal advice. Have qualified counsel review drafts before sending them to customers.
- Gap status is keyword triage of your documents, not a compliance finding.
- Classification is a keyword first pass over the intended-purpose text. It flags and never clears.
- The Digital Omnibus delay dates (`policylens/omnibus.py`) are unverified against the Official Journal.
- The code scanner finds patterns, not behavior. Silence is not compliance.
- No real customer has used this yet. Validate demand first: [docs/CUSTOMER_DISCOVERY.md](docs/CUSTOMER_DISCOVERY.md).

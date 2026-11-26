# PolicyLens

**AI agents that have to show receipts.** EU AI Act (Regulation (EU) 2024/1689) checks for code, where an agent's finding is accepted only if its code quote and its law quote really exist.

## The problem

Ask a coding agent whether your repo touches the EU AI Act and you get a confident paragraph. It may quote code that isn't there or law that was never written. Word-matching scanners have the opposite problem: they flag a comment that says "emotion". This one did, with 10 CRITICAL findings on its own source, 9 of them false.

## The proof gate

An agent reports through one tool, `submit_claim`. Plain code, with no model involved, checks it:

```text
agent claim ──► code quote at that file:line, and really code (not a comment or string)?
                law quote verbatim, in the one Article/Annex cited?
                no compliance verdicts, no "the system does not…", no unquoted citations?
                        │
          GROUNDED ◄────┴────► REJECTED + reason (the agent can fix it or drop it)
```

**GROUNDED means the quotes exist. It does not mean the law applies.** That judgment stays with a human. What the gate removes is invented evidence.

| Use it with | How | API key |
|---|---|---|
| Your coding agent (Claude Code, Cursor) | MCP tool `submit_claim` | PolicyLens needs none |
| The built-in investigator | `python -m policylens.investigate path/to/repo --send-code` (sends source to your model provider) | Yes |

## Legal drift: review what a pull request changes

```bash
python -m policylens.drift --base origin/main
```

> **Exposure changed:** No tracked signal → **Article 5 review: possible prohibited practice**
> CRITICAL: Article 5 (`app.py:4`) `from deepface import DeepFace`

Only what the change adds is reported. As a GitHub Action (standard library only, no API key, code stays on the runner):

```yaml
on: pull_request
permissions:
  contents: read
jobs:
  ai-act-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: bhushan-01/policylens@main   # pin to a commit SHA for real use
```

The report goes to the job summary. For SARIF upload, pass the action's `sarif` output to `github/codeql-action/upload-sarif`.

Other projects also scan code for the AI Act in CI, for example [Systima Comply](https://github.com/systima-ai/comply) and [OpenComplAI](https://github.com/Opencomplai/opencomplai). PolicyLens focuses on checkable evidence: for its own findings and for any agent's.

Detectors read Python through its syntax tree, and JavaScript/TypeScript and other languages through a lightweight lexer. They are heuristics and will miss things. A line can be silenced with `# policylens: ignore[rule-name]`, so review those comments in pull requests.

Repo: https://github.com/bhushan-01/policylens

## What it does

| Tool | For | What you get |
|---|---|---|
| **Evidence Pack** | AI vendors (first target: hiring / HR-tech) answering a customer's AI Act questionnaire | Risk classification, gap analysis against 14 buyer-expected obligations, cited draft answers, a fix-first list |
| **Classifier** | Anyone asking "how does the Act apply to my product?" | Rule-based first pass with verbatim law quotes, then a cited answer |
| **Code scanner** | Engineers | Red flags in a repo (emotion/biometrics, automated decisions with no human, missing logging, no AI disclosure) with file:line, Article and fix |
| **MCP server** | Cursor / Claude Code / Claude Desktop | The above as editor tools: `search_law`, `get_article`, `classify_product`, `scan_codebase`, `evidence_gaps`, `verify_citations`, `submit_claim`, `legal_drift` |
| **Evidence Tribunal** | Anyone who distrusts a chatty agent | Adversarial proof ledger: charges → defense → citation audit → verdict |
| **Web UI** | Non-technical users | Evidence Pack, Tribunal, and Classifier tabs |

Why the Evidence Pack: classification alone is free elsewhere (EU Commission checker, FLI, TÜV SÜD). The paid pain is the buyer questionnaire that blocks an EU deal.

## Quick start

```bash
git clone https://github.com/bhushan-01/policylens.git && cd policylens
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e . --no-deps
cp .env.example .env          # optional: OPENROUTER_API_KEY or ANTHROPIC_API_KEY
make test                     # 162 offline safety evals, no API key needed
make demo-offline             # evidence pack on a fictional company, deterministic
```

No key? Everything runs offline. A key only improves the wording of drafted answers.

## Commands

| Command | Does |
|---|---|
| `make test` | 162 offline safety evals |
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
  scanner.py  codefacts.py   code scanner; reads imports and code, not comments or strings
  proof.py                   proof gate for agent claims
  investigate.py  drift.py   investigator agent; pull-request legal drift
  tribunal.py  agent.py      Evidence Tribunal (agent.py redirects here)
  blueprint.py               fix-first document outlines for gaps
  mcp_server.py  ui.py       editor tools and web UI
web/                         static landing page
  ingest/                    one-time PDF -> chunks -> embeddings pipeline
evals/                       evidence + gate (162), retrieval, assertions; fixtures/
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

## License

[Apache-2.0](LICENSE) for the code. The Act text in `data/` is EU legal text from the Official Journal and is not covered by this license. To contribute, see [CONTRIBUTING.md](CONTRIBUTING.md).

# PolicyLens user guide

## Setup (once)

```bash
cd ~/Documents/policylens
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # optional: add OPENROUTER_API_KEY or ANTHROPIC_API_KEY
pip install -e . --no-deps
make test                   # should print 83/83 passed
```

No key? Everything still works offline. A key only improves the wording of drafted answers.

## A. Answer a buyer questionnaire (Evidence Pack)

### 1. Prepare your documents
Put plain `.md` or `.txt` files in one folder. One topic per file works best, with headings.
Useful topics: product overview and intended purpose, human oversight, data governance and bias
testing, security and accuracy, logging, incident response, post-market monitoring, quality process.
Each heading section becomes a citable passage, shown as `file.md § 2`.

Rules of thumb:
- Write what is true and current. The tool cannot tell if a document is out of date.
- Name the thing a buyer will ask about, using its common words (for example "audit log", "serious
  incident", "human review"). Gap detection looks for those words.
- The first overview document is used to classify the product. Keep the "intended purpose" explicit,
  including what the product is not for.

### 2. Prepare the questionnaire
A numbered list in `.md` or `.txt`:

```
1. Is your AI system classified as high-risk under the EU AI Act?
2. How do you ensure human oversight?
```
or a `.csv` with a column whose name contains "question".

### 3. Run it

```bash
python -m policylens.pack --docs my_docs/ --questionnaire q.md --out out/
python -m policylens.pack --docs my_docs/ --questionnaire q.md --no-llm     # deterministic
python -m policylens.pack ... --product "override description for classification"
```
Or use the web UI: `make ui`, open the "Evidence Pack (for vendors)" tab, upload files.

### 4. Read the outputs (`out/`)

| File | Use |
|---|---|
| `evidence_pack.html` | Readable report to review |
| `evidence_pack.md` | Same, in Markdown |
| `evidence_pack.json` | Machine-readable, includes verification details per answer |
| `gaps.csv` | Your to-do list: obligation, status, what buyers expect, where found |
| `ai_act_position.md` | Draft public page built only from evidenced facts |

### 5. Answer statuses

| Status | Meaning | What you do |
|---|---|---|
| READY | Cited to your documents and real Articles, no flags | Still have counsel read it |
| NEEDS INPUT | A fact is missing from your documents | Fill the `[NEEDS INPUT ...]` gaps or write the missing document |
| CHECK CITATIONS | A citation failed a check, or the answer contains a negative claim, a forward commitment, or no company citation | Confirm each flagged point is true |

The "Fix first" list in the report shows Missing and Partial obligations in priority order.

### 6. Before you send anything to a customer
1. Resolve every `[NEEDS INPUT]`.
2. Confirm each flagged claim is true.
3. Check the Omnibus dates against the Official Journal.
4. Have qualified counsel review. This tool produces drafts, not legal advice.

## B. Classify a product

```bash
python -m policylens.checklist "We build CV screening software for HR teams"
```
Prints a rule-based first pass with verbatim law quotes, then the checklist retrieval, then a cited
LLM answer if a key is set. The web UI "Classify a product" tab shows the same.

## C. Scan a code repository

```bash
python -m policylens.scanner path/to/repo            # readable
python -m policylens.scanner path/to/repo --json     # for tooling
```
Fix `critical` and `high` findings first. A scan with no findings does not mean compliant.

## D. Use the tools inside Cursor or Claude Code

1. Copy `mcp_config.example.json` into your editor's MCP settings and fix the paths.
2. Ask the editor to run `scan_codebase` on your repo, or `evidence_gaps` on your docs folder.

## E. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `ModuleNotFoundError` | Activate the venv: `source .venv/bin/activate` |
| First run is slow | The embedding model loads once per run |
| "unauthenticated requests to the HF Hub" | Harmless. Set `HF_TOKEN` to silence it |
| Answers say `[DRAFT NEEDED]` | No API key or `--no-llm`. Add a key for drafted wording |
| `llm_error` in the JSON | Network or parse failure. The pack falls back to offline drafts for that answer |
| Gap says Missing but you wrote it | Use the buyer's vocabulary in your documents (see obligation keywords in `policylens/obligations.py`) |
| Classification says "No Annex III trigger" | Rules are keyword based. Describe the intended purpose plainly, or classify by reading Annex III |

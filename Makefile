PY=.venv/bin/python

.PHONY: install test test-all demo demo-offline scan ui mcp ingest

install:       ## editable install of the package
	$(PY) -m pip install -e . --no-deps

test:          ## 81 offline safety evals (no API key needed)
	$(PY) -m evals.evidence

test-all:      ## safety evals + retrieval and assertion evals
	$(PY) -m evals.evidence
	$(PY) -m evals.retrieval
	$(PY) -m evals.assertions

demo:          ## Evidence pack on the fictional sample company (uses an LLM if a key is set)
	$(PY) -m policylens.pack --docs examples/sample_company --questionnaire examples/sample_questionnaire.md

demo-offline:  ## Same, fully deterministic
	$(PY) -m policylens.pack --docs examples/sample_company --questionnaire examples/sample_questionnaire.md --no-llm

scan:          ## Code scanner on the fictional sample repo
	$(PY) -m policylens.scanner examples/sample_repo

ui:            ## Web UI (Evidence Pack tab + classifier)
	$(PY) -m policylens.ui

mcp:           ## MCP server over stdio
	$(PY) -m policylens.mcp_server

ingest:        ## Rebuild the law index from the PDF (slow; data/ is committed already)
	$(PY) -m policylens.ingest.extract_text
	$(PY) -m policylens.ingest.clean_text
	$(PY) -m policylens.ingest.chunk
	$(PY) -m policylens.ingest.split_chunks
	$(PY) -m policylens.ingest.embed_chunks
	$(PY) -m policylens.ingest.check_tokens

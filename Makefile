PY=.venv/bin/python

.PHONY: install test test-all demo demo-offline scan drift ui mcp tribunal ingest landing docker

install:       ## editable install of the package
	$(PY) -m pip install -e . --no-deps

test:          ## offline safety evals (no API key needed)
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

tribunal:      ## Evidence Tribunal on a sample hiring product
	$(PY) -m policylens.tribunal "CV screening software for HR teams"

drift:         ## What do uncommitted changes add compared with main?
	$(PY) -m policylens.drift --base main

ui:            ## Web UI (Evidence Pack + Tribunal + classifier)
	$(PY) -m policylens.ui

landing:       ## Open the static landing page
	@echo "Open web/index.html in a browser (file://$(CURDIR)/web/index.html)"

mcp:           ## MCP server over stdio
	$(PY) -m policylens.mcp_server

docker:        ## Build the Gradio container image
	docker build -t policylens:latest .

ingest:        ## Rebuild the law index from the PDF (slow; data/ is committed already)
	$(PY) -m policylens.ingest.extract_text
	$(PY) -m policylens.ingest.clean_text
	$(PY) -m policylens.ingest.chunk
	$(PY) -m policylens.ingest.split_chunks
	$(PY) -m policylens.ingest.embed_chunks
	$(PY) -m policylens.ingest.check_tokens

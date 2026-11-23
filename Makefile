PY=.venv/bin/python

.PHONY: test demo demo-offline scan ui mcp

test:          ## 81 offline safety evals (no API key needed)
	$(PY) src/eval_evidence.py

demo:          ## Evidence pack on the fictional sample company (uses LLM if a key is set)
	$(PY) src/evidence_pack.py --docs data/sample_company --questionnaire data/sample_questionnaire.md

demo-offline:  ## Same, fully deterministic
	$(PY) src/evidence_pack.py --docs data/sample_company --questionnaire data/sample_questionnaire.md --no-llm

scan:          ## Code scanner on the fictional sample repo
	$(PY) src/code_scan.py data/sample_repo

ui:            ## Web UI (Evidence Pack tab + classifier)
	$(PY) src/app.py

mcp:           ## MCP server over stdio
	$(PY) src/mcp_server.py

# PolicyLens mastery tracker

Goal: explain, debug, modify and rebuild every important part of this project without AI.
Rule: an area is "Mastered" only after you explain it without notes, answer follow-ups, and apply it to a new case.

## Roadmap (one lesson per session)

| # | Lesson | Files | Status |
|---|---|---|---|
| 1 | The trust core: finding and checking citations | `policylens/laws.py` | In progress |
| 2 | Cutting the law into chunks | `ingest/chunk.py`, `ingest/split_chunks.py` | Not started |
| 3 | Embeddings and semantic search | `ingest/embed_chunks.py`, `search.py` | Not started |
| 4 | Classification rules | `risk_rules.py`, `classification.py` | Not started |
| 5 | Vendor documents and gap analysis | `company.py`, `obligations.py`, `pack.py` (gap_analysis) | Not started |
| 6 | Drafting answers and the guards | `pack.py` (draft_answer), `llm.py` | Not started |
| 7 | Rendering the pack | `render.py` | Not started |
| 8 | Code scanner | `scanner.py` | Not started |
| 9 | MCP server and web UI | `mcp_server.py`, `ui.py` | Not started |
| 10 | Evals: how we know it works | `evals/evidence.py` | Not started |
| 11 | Agent (optional) | `agent.py` | Not started |
| 12 | Mock interviews and rebuild exercises | all | Not started |

## Scorecard

| Area | Status | Confidence (0-5) |
|---|---|---|
| Project overview | Learning | 1 |
| Architecture | Not started | 0 |
| Repository structure | Learning | 1 |
| Data layer (chunks, embeddings) | Not started | 0 |
| Search / retrieval | Not started | 0 |
| Classification | Not started | 0 |
| Evidence pack pipeline | Not started | 0 |
| Guards and verification | Not started | 0 |
| Code scanner | Not started | 0 |
| MCP and UI | Not started | 0 |
| Evals and debugging | Not started | 0 |
| Rebuilding without AI | Not started | 0 |
| Interview readiness | Not started | 0 |

Not in this project: a frontend framework, a database server, authentication, or deployment. The "database" is JSON files plus a numpy array.

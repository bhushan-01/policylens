# Safety, evals and limits

## What PolicyLens promises
- Every Article or Annex in an output exists in the Act.
- Every quoted law passage appears verbatim in the Act.
- Company facts are traceable to a named document passage, or marked `[NEEDS INPUT]`.
- It flags risk and gaps. It never declares a product compliant or not high-risk.

## What it does not promise
- Not legal advice. Have qualified counsel review drafts before sending them to customers.
- Gap status is keyword triage of your documents, not a compliance determination.
- Classification is a keyword first pass over the intended-purpose text. Unusual wording can be missed.
  It does not model every exception, delegated act or national rule.
- The code scanner finds patterns, not behavior. It cannot see runtime data or deployment.
- Dates: the Digital Omnibus delay dates come from the note in `policylens/omnibus.py`
  (Annex III stand-alone systems 2 December 2027; Annex I product systems 2 August 2028).
  They were not verified against the Official Journal. Re-check before relying on them.
- The law text is the 2024 PDF. Later amendments are not in the index.
- Sending a vendor's real documents to an external LLM provider shares them with that provider.
  Use `--no-llm` or get consent first.

## Proof gate, investigator and drift

- GROUNDED means the code quote is at that line and the law quote is in that Article/Annex. It does not check that the statement follows from them. A model can pair two real quotes badly.
- The wording rules (verdicts, absence claims) are pattern lists in English. Rephrasing can get past them.
- The investigator needs `--send-code` because file contents go to your model provider. It reads source-code files inside the given folder only (not `.env`, not symlinks). Secrets hard-coded in source would be sent.
- One live run on the fictional sample app (2026-11-26): 5 claims GROUNDED, 2 rejected. One accepted claim said a
  function "interacts with job applicants" when its quoted line only sends resume text to a model. Real quotes,
  unsupported statement: **read every GROUNDED statement against its quotes.** That is one run on a toy repo, not an evaluation.
- Repository text can try to instruct the agent (prompt injection). The gate limits what becomes a finding, but open questions are unchecked model text.
- Drift can be evaded: ignore comments, files over 300 KB, skipped folders, or code the patterns do not know.
- The GitHub Action has run on GitHub only on this repository's own pull request. It has not been tried from another repository.

## The 164 offline evals (`make test`)

No API key or network needed after the embedding model is cached.

| Group | Checks |
|---|---|
| Citation checker | flags nonexistent Articles, flags real-but-unshown ones, accepts shown ones |
| Rule markers | all 27 classification rules quote text that really exists in the Act |
| Classification | exclusions ignored on the sample; 19 products: hiring, promotion, emotion at work, mall face recognition, police live recognition, credit, proctoring, grading, emergency triage, visa scoring, crime prediction, social scoring, face scraping, synthetic video, chatbot, and negatives (weather, lunch menu, inventory) |
| Quotes and exceptions | mall camera quotes Annex III 1(a); verification exception note appears |
| Gap analysis | known Missing (Art. 9, 11, 12, 17, 43, 49, 73) and Evidenced (Art. 10, 14, 15) on the sample company |
| Offline pack | 14 questions parsed; nothing marked READY without an LLM; all consulted law exists |
| Adversarial model | a mocked model invents logging, cites Article 999, makes a negative claim, fabricates a document reference. Each is caught |
| Code scanner | detects all 7 planted problems; citations exist; critical sorted first; docs-only folder is clean |

Older retrieval and assertion evals: `evals/retrieval.py`, `evals/assertions.py` (run `make test-all`).

## Observed model failures that shaped the guards
On the first live run with a real model:
- It claimed technical documentation the sample company did not have.
- It stated "our system does not log events" with no support.
- It wrote "we do not infer emotions" when documents never said so.
- It made forward promises ("we will select the appropriate procedure").
Each now triggers a deterministic guard or a review flag.

## Privacy
- `.env` is git-ignored. Never commit keys.
- `out/` (generated packs) is git-ignored. `examples/` holds a pack for a fictional company only.

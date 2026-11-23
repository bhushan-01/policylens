# PolicyLens — Learning Walkthrough

Use this to explain the project out loud. If you can teach a step, you understand it.

## The one-sentence idea

PolicyLens does not memorize the whole EU AI Act in the LLM. It **finds the right pages first**, then asks the LLM to answer **only from those pages**, with citations.

## Pipeline map

```text
PDF → raw text → clean text → article chunks → split chunks
 → embeddings → search → LLM answer / agent / MCP / UI
```

## File-by-file “explain it back” checklist

### Data prep
- [ ] `extract_text.py` — Why can’t we search a PDF directly?
- [ ] `clean_text.py` — Why is a lazy “delete any line with ELI” dangerous?
- [ ] `chunk.py` — Why split by Article? What does `in_annexes` fix?
- [ ] `split_chunks.py` — Why does the 512-token limit matter silently?

### Meaning + search
- [ ] `embed_demo.py` — What does a high cosine score mean?
- [ ] `embed_chunks.py` — What is stored in `embeddings.npy`?
- [ ] `search.py` — How can “screens CVs” match “filter job applications”?
- [ ] `eval_retrieval.py` — What does hit rate @8 measure?

### Generation + product surfaces
- [ ] `answer.py` / `classify.py` — Golden rule: cite or say not sure
- [ ] `agent.py` — Workflow vs tool-calling agent
- [ ] `mcp_server.py` — What does MCP let Cursor/Claude Desktop do?
- [ ] `app.py` — Same brain, different interface (web UI)
- [ ] `eval_assertions.py` — Why “it runs” is not “it works”

## Mini quizzes

1. User asks about workplace emotion AI. Which Article should appear? Why might a long unsplit Article 5 miss point (f)?
2. What citation should the user see for chunk id `art_5_p7`?
3. Why do we inject Omnibus dates instead of trusting the 2024 PDF alone?
4. If retrieval returns pizza-chatbot chunks for a hiring question, should the LLM invent Annex III? What should it do?

## Suggested practice order

1. Run `python src/search.py "..."` and read the top 3 ids  
2. Run `python src/eval_retrieval.py`  
3. Run `python src/classify.py "..."` and underline every citation  
4. Open `chunks_split.json`, jump to that id, confirm the text supports the claim  
5. Explain the flow to a friend without looking at notes  

## Done means

You can rebuild from PDF → answer, explain each script’s job, and catch a wrong citation.

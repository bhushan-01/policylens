# PolicyLens business plan

Source: market research from an earlier chat. The competitor and funding claims below were not
re-verified when this file was written. Check them before quoting them to anyone.

## 1. Finding: classification alone is not a business
Free tools already classify AI systems under the EU AI Act:
- The European Commission's official checker.
- The Future of Life Institute's checker, free to embed.
- TÜV SÜD's free online risk classification tool.
- Smaller tools such as IsHighRiskAI, which also anchor answers to Articles.

Nobody pays for what the EU gives away. A classifier is a learning project, not a company.

## 2. Where the pain is: buyer questionnaires
When an AI vendor sells to a European business, the buyer's procurement team sends a due-diligence
questionnaire and the deal waits for the answers.
- Typical questions: risk classification, technical documentation (Article 11), human oversight
  (Article 14), conformity assessment status, serious incident reporting (Article 73).
- A delay in formal high-risk application does not pause procurement diligence. For many non-EU
  vendors the first real pressure is a customer evidence request.
- Even minimal-risk vendors struggle to state that confidently with a short supporting explanation.
- Typical story: a 40-question questionnaire arrives and question one is "Is your AI system
  classified as high-risk under the EU AI Act?"

## 3. The market is not empty
- Compliance platforms with AI Act and questionnaire features (for example Vanta).
- AI governance platforms for large enterprises (for example Credo AI, Trustible, Holistic AI,
  OneTrust, ServiceNow). One reported raise: Credo AI, about $21M in 2024.
- Smaller players writing about the questionnaire problem (for example Wolfia, Complizo).

A solo builder cannot beat them at broad AI governance. The way in is a narrow niche they serve badly.

## 4. Directions

| Direction | Who pays | What it does | Main risk |
|---|---|---|---|
| A. AI Act evidence pack | Founder or CTO of a 10-200 person AI company selling to EU customers | Reads the company's docs and the law, drafts questionnaire answers and a public position page, every answer cited | Vanta and Wolfia already automate questionnaires |
| B. Compliance in the code editor | Engineering teams | MCP tool that flags gaps while you build and records evidence | Teams may not feel the pain until a buyer asks |
| C. One vertical, deeply | AI hiring and HR-tech companies | A plus B, only for hiring software | Smaller market, must learn HR-tech buyers |

**Chosen: C, with A as the core feature.** Hiring AI is the clearest high-risk case (Annex III point 4).
The stand-alone high-risk date gives buyers a clock (2 December 2027 per the Omnibus note, unverified).
High-risk vendors carry more documentation work and more fear than minimal-risk SaaS. Large platforms
target broad enterprise compliance teams, not a 30-person HR-tech startup.

## 5. What is built against this plan

| Direction | Status | Where |
|---|---|---|
| A. Evidence pack | Built | `policylens/pack.py`, `render.py`, `obligations.py` |
| B. Editor tool | Built (scanner and MCP tools) | `policylens/scanner.py`, `mcp_server.py` |
| C. Hiring vertical | Built into rules, obligations and sample | `risk_rules.py` (Annex III 4), `examples/sample_company` |
| Customer interviews | Script ready, not run | `docs/CUSTOMER_DISCOVERY.md` |
| Outreach | Guide ready, list not built | `docs/OUTREACH.md` |

## 6. Risks specific to the founder
- **Distribution:** a US student with no EU buyer or HR-tech network. Finding the first 10 customers is the hard part, not the code.
- **Trust:** customers rely on it for legal risk. Position it as drafts for counsel review, never legal advice.
- **Law keeps changing:** the Digital Omnibus already moved dates. Staying current is work and also an edge.

## 7. Next steps, in order
1. Build the interview list ([OUTREACH.md](OUTREACH.md)).
2. Run 15 interviews about the past, not a pitch ([CUSTOMER_DISCOVERY.md](CUSTOMER_DISCOVERY.md)).
3. Apply the stop rule: fewer than 5 of 15 faced a real questionnaire, or nobody spent time or money, means stop.
4. If it passes: run the tool on a real questionnaire from a willing interviewee, with their written consent.
5. Then decide on pricing, a pilot and a landing page.

## 8. Open questions to answer from interviews
- Who owns the questionnaire: CTO, security lead, or founder?
- Do buyers accept a vendor-written answer, or demand certification?
- What do vendors pay for today and how much?
- Is "drafts for counsel" enough, or do vendors want counsel included?

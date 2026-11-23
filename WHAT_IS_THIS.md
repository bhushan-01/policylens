# What is PolicyLens, really?

## The human problem

Someone builds an AI product (CV screener, chatbot, camera, emotion tool…).

They ask:

> “Does the EU AI Act make this banned, high-risk, or mostly fine — and which Article says so?”

If they only ask a general chatbot, it may sound confident and still **cite the wrong Article** or invent rules.

## What PolicyLens does

PolicyLens is a **law lookup + explanation tool** for the EU AI Act.

1. It stores the real Act as searchable pieces  
2. It finds the pieces that match your product  
3. It answers **only using those pieces**, with citations  
4. If it can’t find good evidence, it should say **not sure**

That is the whole product.

## What it is NOT

- Not a law firm  
- Not a full compliance platform  
- Not “an agent for the sake of agents”  
- Not NIST / US frameworks (maybe later)

## The useful workflow (this matters more than “agent”)

For governance, a **checklist** is more sensible than free-form tool chatting:

1. **Prohibited?** (Article 5 — e.g. workplace emotion recognition)  
2. **High-risk?** (Article 6 + Annex III — e.g. hiring/CV screening)  
3. **Transparency only?** (Article 50 — e.g. many chatbots)  
4. **Else:** likely minimal / unclear → say not sure

Run that with:

```bash
python src/policylens.py "your product"
```

## Where “agent” fits

| Thing | Useful? | Why |
|---|---|---|
| Checklist workflow (`policylens.py`) | **Yes** | Matches how compliance questions are asked |
| One-shot RAG (`classify.py`) | Yes | Fast single answer |
| Free tool-calling agent (`agent.py`) | Sometimes | Good for learning / hard edge cases; often overkill |

For your demo and understanding, **`policylens.py` is the main product.**

## One sentence pitch

**PolicyLens helps builders map an AI product to the EU AI Act with real citations, instead of guessing.**

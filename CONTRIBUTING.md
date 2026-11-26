# Contributing

```bash
pip install -r requirements.txt && pip install -e . --no-deps
make test    # must stay green
```

## Good first contributions
1. **Report a false positive or a miss.** Send the smallest snippet that shows it. Each one becomes a test in `evals/gate.py`.
2. **Teach the scanner a library.** Add it to `AI_LIBS`, `EMOTION_LIBS`, `BIOMETRIC_LIBS` or `LOGGING_LIBS` in
   `policylens/scanner.py`, with a test that imports it.
3. **Break the proof gate.** Find a claim that gets GROUNDED but should not, and add it as a `rejected(...)` case.
4. **Better language support.** `policylens/codefacts.py` uses a simple lexer outside Python.

## Rules
- Every citation must exist in the Act, and a finding says "needs review", never "compliant" or "illegal".
- A new detector needs two tests: code that must be flagged, and a mention (comment or string) that must not be.
- `scanner.py`, `codefacts.py`, `proof.py` and `drift.py` use only the standard library.
- No model decides whether a claim is GROUNDED.

"""Check how many split chunks still exceed the model token limit."""

import json
from sentence_transformers import SentenceTransformer

from policylens.paths import DATA_DIR

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
print("Max tokens:", model.max_seq_length)

with open(DATA_DIR / "chunks_split.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

too_long = []
for c in chunks:
    n = len(model.tokenizer(c["text"], truncation=False)["input_ids"])
    if n > model.max_seq_length:
        too_long.append((c["id"], n, len(c["text"])))

print("Total split chunks:", len(chunks))
print("Still too long:", len(too_long))
if too_long:
    too_long.sort(key=lambda x: -x[1])
    print("Worst offenders:")
    for cid, n, chars in too_long[:10]:
        print(f"  {cid}: {n} tokens ({chars} chars)")

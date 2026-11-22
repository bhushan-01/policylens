import json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
print("Max tokens the model can read:", model.max_seq_length)

with open("data/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

too_long = 0
for c in chunks:
    n_tokens = len(model.tokenizer(c["text"])["input_ids"])
    if n_tokens > model.max_seq_length:
        too_long += 1

print("Total chunks:", len(chunks))
print("Chunks too long for the model:", too_long)
print()

by_id = {c["id"]: c for c in chunks}

for cid in ["art_3", "art_5", "art_6", "art_87"]:
    n_tokens = len(model.tokenizer(by_id[cid]["text"])["input_ids"])
    print(f"{cid}: {n_tokens} tokens")

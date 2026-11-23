import json
import re

with open("data/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

art5 = next(c for c in chunks if c["id"] == "art_5")

print("Looking for paragraph starts in Article 5:\n")

found = 0
for line in art5["text"].split("\n"):
    s = line.strip()
    m = re.match(r"^(\d+)\.\s", s)
    if m:
        found += 1
        print("Found paragraph", m.group(1) + ":")
        print(" ", s[:70])
        print()

print("Total paragraph starts found:", found)

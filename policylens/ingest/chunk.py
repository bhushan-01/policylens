"""Cut the cleaned text into one chunk per Article and per Annex, with chapter/section metadata."""

import re
import json

from policylens.paths import DATA_DIR


def main():
    with open(DATA_DIR / "ai_act_clean.txt", "r", encoding="utf-8") as f:
        lines = f.read().split("\n")

    chunks = []          # finished boxes go here
    current = None       # the box we are filling right now
    chapter = None       # bookmark: which chapter we are in
    section = None       # bookmark: which section we are in
    in_annexes = False   # switch: have we reached the annexes yet?
    skip_next = False    # switch: should we skip the next line (because it was a title)?

    for i, line in enumerate(lines):
        s = line.strip()

        if skip_next:
            skip_next = False
            continue

        # --- 1. Is this line an ANNEX heading? ---
        annex = re.fullmatch(r"ANNEX ([IVX]+)", s)
        if annex:
            in_annexes = True
            if current:
                chunks.append(current)
            number = annex.group(1)
            title = lines[i + 1].strip()
            current = {
                "id": f"annex_{number}",
                "type": "annex",
                "number": number,
                "title": title,
                "chapter": None,
                "section": None,
                "text": s + "\n" + title,
            }
            skip_next = True
            continue

        # --- 2. Before the annexes: look for chapters, sections and articles ---
        if not in_annexes:

            ch = re.fullmatch(r"CHAPTER ([IVX]+)", s)
            if ch:
                chapter = s + " - " + lines[i + 1].strip()
                section = None
                skip_next = True
                continue

            sec = re.fullmatch(r"SECTION (\d+)", s)
            if sec:
                section = s + " - " + lines[i + 1].strip()
                skip_next = True
                continue

            art = re.fullmatch(r"Article (\d+)", s)
            if art:
                if current:
                    chunks.append(current)
                number = art.group(1)
                title = lines[i + 1].strip()
                current = {
                    "id": f"art_{number}",
                    "type": "article",
                    "number": number,
                    "title": title,
                    "chapter": chapter,
                    "section": section,
                    "text": s + "\n" + title,
                }
                skip_next = True
                continue

        # --- 3. A normal line: add it to the box we are filling ---
        if current:
            current["text"] += "\n" + line

    # don't forget the very last box
    if current:
        chunks.append(current)

    # --- Checks ---
    articles = [c for c in chunks if c["type"] == "article"]
    annexes = [c for c in chunks if c["type"] == "annex"]

    print("Articles found:", len(articles), "(expected 113)")
    print("Annexes found:", len(annexes), "(expected 13)")

    numbers = [int(c["number"]) for c in articles]
    print("Articles in order 1 to 113:", numbers == list(range(1, 114)))

    print()
    print("Sample chunk:")
    sample = articles[4]
    print("  id:     ", sample["id"])
    print("  title:  ", sample["title"])
    print("  chapter:", sample["chapter"])
    print("  length: ", len(sample["text"]), "characters")

    with open(DATA_DIR / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print()
    print("Saved", len(chunks), "chunks to data/chunks.json")


if __name__ == "__main__":
    main()

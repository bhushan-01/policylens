"""
Step 7: split long Article/Annex chunks so each piece fits ~512 tokens.
Citations still use the parent Article/Annex (e.g. Article 5), even if id is art_5_p1.
"""

import json
import re

PARA = re.compile(r"^(\d+)\.\s")
DEFN = re.compile(r"^\((\d+)\)\s")
LETTER = re.compile(r"^\(([a-z])\)\s")

# ~4 chars/token → stay under ~450 tokens with margin
MAX_CHARS = 1600


from policylens.paths import DATA_DIR


def split_by_pattern(text: str, pattern: re.Pattern) -> list[tuple[str, str]]:
    lines = text.split("\n")
    pieces: list[tuple[str, list[str]]] = []
    intro: list[str] = []
    current_label = None
    current_lines: list[str] = []

    for line in lines:
        s = line.strip()
        m = pattern.match(s)
        if m:
            if current_label is not None:
                pieces.append((current_label, current_lines))
            current_label = m.group(1)
            current_lines = list(intro) + [line]
            intro = []
        else:
            if current_label is None:
                intro.append(line)
            else:
                current_lines.append(line)

    if current_label is not None:
        pieces.append((current_label, current_lines))
    elif intro:
        return [("full", "\n".join(intro))]

    return [(label, "\n".join(ls)) for label, ls in pieces]


def hard_split(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            cut = text.rfind("\n", start, end)
            if cut > start + max_chars // 2:
                end = cut
        part = text[start:end].strip()
        if part:
            parts.append(part)
        start = end if end > start else start + max_chars
    return parts


def refine_oversized(label: str, text: str) -> list[tuple[str, str]]:
    """If a piece is still too long, try lettered points, then hard-split."""
    if len(text) <= MAX_CHARS:
        return [(label, text)]

    letter_parts = split_by_pattern(text, LETTER)
    if len(letter_parts) > 1 and letter_parts[0][0] != "full":
        out = []
        for let, t in letter_parts:
            for k, sub in enumerate(hard_split(t), start=1):
                sub_label = f"{label}{let}" if k == 1 else f"{label}{let}_{k}"
                out.append((sub_label, sub))
        return out

    return [
        (f"{label}_{k}" if len(hard_split(text)) > 1 else label, sub)
        for k, sub in enumerate(hard_split(text), start=1)
    ]


def expand_chunk(chunk: dict) -> list[dict]:
    text = chunk["text"]

    parts = split_by_pattern(text, PARA)
    used = "para"

    if len(parts) == 1 and parts[0][0] == "full":
        parts = split_by_pattern(text, DEFN)
        used = "defn"

    if len(parts) == 1 and parts[0][0] == "full" and len(parts[0][1]) > MAX_CHARS:
        letter_parts = split_by_pattern(text, LETTER)
        if len(letter_parts) > 1:
            parts = letter_parts
            used = "letter"

    refined: list[tuple[str, str]] = []
    for label, piece_text in parts:
        refined.extend(refine_oversized(label, piece_text))

    final = []
    only_one = len(refined) == 1 and refined[0][0] == "full"

    for i, (label, sub) in enumerate(refined, start=1):
        if only_one:
            new_id = chunk["id"]
            split_by = None
        else:
            new_id = f"{chunk['id']}_p{i}"
            split_by = used

        final.append({
            "id": new_id,
            "type": chunk["type"],
            "number": chunk["number"],
            "title": chunk["title"],
            "chapter": chunk["chapter"],
            "section": chunk["section"],
            "parent_id": chunk["id"],
            "paragraph": None if label == "full" else label,
            "split_by": split_by,
            "text": sub,
        })

    return final


def main():
    with open(DATA_DIR / "chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    split_chunks = []
    for chunk in chunks:
        split_chunks.extend(expand_chunk(chunk))

    parents = {c["parent_id"] for c in split_chunks}
    print("Original chunks:", len(chunks))
    print("Split chunks:", len(split_chunks))
    print("Unique parents:", len(parents), "(expected 126)")

    art5 = [c for c in split_chunks if c["parent_id"] == "art_5"]
    print("\nArticle 5 pieces:", len(art5))
    for c in art5[:5]:
        print(f"  {c['id']}: {len(c['text'])} chars")

    art3 = [c for c in split_chunks if c["parent_id"] == "art_3"]
    print("Article 3 pieces:", len(art3))

    oversized = sum(1 for c in split_chunks if len(c["text"]) > MAX_CHARS)
    print("Pieces over", MAX_CHARS, "chars:", oversized)

    with open(DATA_DIR / "chunks_split.json", "w", encoding="utf-8") as f:
        json.dump(split_chunks, f, indent=2, ensure_ascii=False)

    print("Saved data/chunks_split.json")


if __name__ == "__main__":
    main()

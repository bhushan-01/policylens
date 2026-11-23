"""Extract plain text from the EU AI Act PDF."""

from pypdf import PdfReader

from policylens.paths import DATA_DIR


def main():
    reader = PdfReader(DATA_DIR / "eu_ai_act.pdf")

    all_pages = []

    for page in reader.pages:
        page_text = page.extract_text()
        all_pages.append(page_text)

    full_text = "\n".join(all_pages)

    print("Total pages:", len(all_pages))
    print("Total characters:", len(full_text))

    with open(DATA_DIR / "ai_act_raw.txt", "w", encoding="utf-8") as f:
        f.write(full_text)

    print("Saved to data/ai_act_raw.txt")


if __name__ == "__main__":
    main()

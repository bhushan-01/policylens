from pypdf import PdfReader

reader = PdfReader("data/eu_ai_act.pdf")

all_pages = []

for page in reader.pages:
    page_text = page.extract_text()
    all_pages.append(page_text)

full_text = "\n".join(all_pages)

print("Total pages:", len(all_pages))
print("Total characters:", len(full_text))

with open("data/ai_act_raw.txt", "w", encoding="utf-8") as f:
    f.write(full_text)

print("Saved to data/ai_act_raw.txt")
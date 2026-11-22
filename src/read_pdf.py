from pypdf import PdfReader
reader = PdfReader("data/eu_ai_act.pdf")
print("Total pages: ", len(reader.pages))
first_page = reader.pages[0]
text = first_page.extract_text()
print(text)
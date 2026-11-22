
FOOTER = "ELI: http://data.europa.eu/eli/reg/2024/1689/oj"
HEADERS = ["EN OJ L, 12.7.2024", "OJ L, 12.7.2024 EN"]

with open("data/ai_act_raw.txt", "r", encoding="utf-8") as f:
    text = f.read()

lines = text.split("\n")
print("Lines before cleaning:", len(lines))

clean_lines = []

for line in lines:
    stripped = line.strip()

    if stripped.startswith(FOOTER) or stripped.endswith(FOOTER):
        continue

    if stripped in HEADERS:
        continue

    clean_lines.append(line)

print("Lines after cleaning:", len(clean_lines))
print("Lines removed:", len(lines) - len(clean_lines))

clean_text = "\n".join(clean_lines)

with open("data/ai_act_clean.txt", "w", encoding="utf-8") as f:
    f.write(clean_text)

print("Saved to data/ai_act_clean.txt")

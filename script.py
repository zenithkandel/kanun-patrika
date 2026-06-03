import fitz
from preeti_unicode import convert_text

pdf = fitz.open("old.pdf")

text = ""

for page in pdf:
    text += page.get_text()

converted = convert_text(text)

with open("old_unicode.txt", "w", encoding="utf-8") as f:
    f.write(converted)

print("Done")
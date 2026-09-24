import re

content = open("src/main.jsx", "r", encoding="utf-8").read()

# Fix common mojibake
replacements = {
    "A,?? Select salesman A,??": "-- Select salesman --",
    "A,?? Select A,??": "-- Select --",
    "A,?? None A,??": "-- None --",
    "A,??": "-",
    "AE+?T": "-",
    "^'": "-",
    "?\"": "-",
    "A ": "-",
    "—": "-",
    "“": '"',
    "’": "'",
    "…": "..."
}

for bad, good in replacements.items():
    content = content.replace(bad, good)

# Also fix any stray unicode replacement characters
content = content.replace("\ufffd", "-")
content = re.sub(r'[^\x00-\x7F]+ Select salesman [^\x00-\x7F]+', '-- Select salesman --', content)
content = re.sub(r'[^\x00-\x7F]+ Select [^\x00-\x7F]+', '-- Select --', content)
content = re.sub(r'[^\x00-\x7F]+ None [^\x00-\x7F]+', '-- None --', content)

open("src/main.jsx", "w", encoding="utf-8").write(content)
print("Encoding fixed")

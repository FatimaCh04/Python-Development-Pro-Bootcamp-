import re

content = open("src/main.jsx", "r", encoding="utf-8").read()
content = content.replace("—", "-")
content = content.replace("·", "-")
content = content.replace("Â·", "-")
content = content.replace("â€”", "-")
content = content.replace("Â", "")
open("src/main.jsx", "w", encoding="utf-8").write(content)
print("Replaced utf-8 dashes in main.jsx")

db = open("src/lib/db.js", "r", encoding="utf-8").read()
db = db.replace("status: 'Pending'", "status: 'Approved'") # For submitSale
open("src/lib/db.js", "w", encoding="utf-8").write(db)
print("Updated submitSale to use Approved")

html = open("index.html", "r", encoding="utf-8").read()
html = html.replace('?"', '-')
open("index.html", "w", encoding="utf-8").write(html)
print("Fixed index.html title")

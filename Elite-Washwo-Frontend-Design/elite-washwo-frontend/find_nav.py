import re

content = open("src/main.jsx", "r", encoding="utf-8").read()

# Find exact visibleNav.map block using regex
pattern = r'\{visibleNav\.map\(section => \(.*?\)\)\}\s*\n\s*\<div className="sidebar-footer"'
match = re.search(pattern, content, re.DOTALL)
if match:
    found = match.group()
    print("Found via regex, length:", len(found))
    print(repr(found[:200]))
else:
    # Find it manually
    idx = content.find('visibleNav.map')
    end = content.find('sidebar-footer', idx)
    chunk = content[idx:end]
    print("Manual find chunk:")
    print(repr(chunk))

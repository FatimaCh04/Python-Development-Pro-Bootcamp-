import re

content = open("src/main.jsx", "r", encoding="utf-8").read()

# Find the nav block end
idx_start = content.find('{visibleNav.map(section =>')
idx_end = content.find('<div className="sidebar-footer"', idx_start)

nav_block = content[idx_start:idx_end]
print("Nav block found, len:", len(nav_block))
print(repr(nav_block[-100:]))  # show end of block

# Replace: wrap in sidebar-nav-scroll
new_block = '<div className="sidebar-nav-scroll">\n        ' + nav_block.strip() + '\n        </div>\n        '
content = content[:idx_start] + new_block + content[idx_end:]

open("src/main.jsx", "w", encoding="utf-8").write(content)
print("Done - nav wrapped in sidebar-nav-scroll")

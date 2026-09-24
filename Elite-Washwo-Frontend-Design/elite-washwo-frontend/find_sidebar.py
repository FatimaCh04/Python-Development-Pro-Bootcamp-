content = open("src/main.jsx", "r", encoding="utf-8").read()
idx = content.find('className="sidebar"')
print(repr(content[idx:idx+1500]))

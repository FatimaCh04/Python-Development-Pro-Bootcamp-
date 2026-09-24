content = open("src/main.jsx", "r", encoding="utf-8").read()
content = content.replace('<div className="brand-mark">EW</div>', '<img src="/elitewash-logo.jpg" className="brand-mark" style={{objectFit:"cover", background:"none"}} alt="EW" />')
open("src/main.jsx", "w", encoding="utf-8").write(content)
print("Logo replaced")

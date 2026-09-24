import re

content = open("src/components/Login.jsx", "r", encoding="utf-8").read()
content = content.replace('<div className="brand-mark">EW</div>', '<img src="/elitewash-logo.jpg" className="brand-mark" alt="Logo" style={{objectFit: "cover"}} />')
open("src/components/Login.jsx", "w", encoding="utf-8").write(content)
print("Login logo updated")

# Also check if it's anywhere else like the loading screen
main_content = open("src/main.jsx", "r", encoding="utf-8").read()
main_content = main_content.replace('<div className="brand-mark">EW</div>', '<img src="/elitewash-logo.jpg" className="brand-mark" alt="Logo" style={{objectFit: "cover"}} />')
open("src/main.jsx", "w", encoding="utf-8").write(main_content)
print("Main loading logo updated")

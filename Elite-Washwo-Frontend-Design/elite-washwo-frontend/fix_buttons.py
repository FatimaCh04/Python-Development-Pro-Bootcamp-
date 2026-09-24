import re

content = open("src/main.jsx", "r", encoding="utf-8").read()

content = content.replace(
    "<span className=\"link\" onClick={()=>setShowSale(s=>!s)}>{showSale?'Cancel Sale':'Create Sale'}</span>",
    "<button className={showSale ? 'btn ghost' : 'btn primary'} onClick={()=>setShowSale(s=>!s)}>{showSale?'Cancel Sale':'Create Sale'}</button>"
)

content = content.replace(
    "<span className=\"link\" onClick={()=>setShowAdd(s=>!s)}>{showAdd?'Cancel':'Add customer'}</span>",
    "<button className={showAdd ? 'btn ghost' : 'btn primary'} onClick={()=>setShowAdd(s=>!s)}>{showAdd?'Cancel':'Add customer'}</button>"
)

content = content.replace(
    "<span className=\"link\" onClick={() => setShowAdd(s => !s)}>{showAdd ? 'Cancel' : '+ Add Product'}</span>",
    "<button className={showAdd ? 'btn ghost' : 'btn primary'} onClick={() => setShowAdd(s => !s)}>{showAdd ? 'Cancel' : '+ Add Product'}</button>"
)

open("src/main.jsx", "w", encoding="utf-8").write(content)
print("Buttons updated")

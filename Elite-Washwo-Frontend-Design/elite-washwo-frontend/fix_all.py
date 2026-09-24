import re

# Fix main.jsx
content = open("src/main.jsx", "r", encoding="utf-8").read()

# Fix mojibake / non-ASCII
content = content.replace("\u2014", "--")   # em dash  —
content = content.replace("\u00b7", "\xb7") # middle dot keep as is (looks fine)
content = content.replace("\u2212", "-")    # minus sign
content = content.replace("\u2013", "-")    # en dash

# Fix option placeholders
content = re.sub(r'[^\x00-\x7F]+\s*Select salesman\s*[^\x00-\x7F]+', '-- Select salesman --', content)
content = re.sub(r'[^\x00-\x7F]+\s*Select\s*[^\x00-\x7F]+', '-- Select --', content)
content = re.sub(r'[^\x00-\x7F]+\s*None\s*[^\x00-\x7F]+', '-- None --', content)

# Fix recovery row which had unicode minus sign showing as garbage
content = re.sub(r'[\u2212\u2014\u2013\ufffd\u00ef]\s*Rs\.', '- Rs.', content)

open("src/main.jsx", "w", encoding="utf-8").write(content)
print("main.jsx encoding fixed, len:", len(content))

# Check db.js for addProduct
db_content = open("src/lib/db.js", "r", encoding="utf-8", errors="ignore").read()
if "addProduct" not in db_content:
    add_fn = '''
export async function addProduct({ name, code, packagingName, unitCost, salesPrice }) {
  // 1. Insert/find product
  let productId;
  const { data: existingProduct } = await supabase.from("products")
    .select("id").eq("code", code).maybeSingle();

  if (existingProduct) {
    productId = existingProduct.id;
  } else {
    const { data: newProd, error: prodErr } = await supabase.from("products")
      .insert({ name: name.trim(), code: code.trim() }).select("id").single();
    if (prodErr) throw prodErr;
    productId = newProd.id;
  }

  // 2. Insert product_packaging (variant/packaging)
  const { data: pkg, error: pkgErr } = await supabase.from("product_packaging")
    .insert({ product_id: productId, name: packagingName.trim() }).select("id").single();
  if (pkgErr) throw pkgErr;

  // 3. Insert product_prices
  const { error: priceErr } = await supabase.from("product_prices")
    .insert({ product_packaging_id: pkg.id, unit_cost: Number(unitCost), sales_price: Number(salesPrice) });
  if (priceErr) throw priceErr;

  return pkg;
}
'''
    db_content += add_fn
    open("src/lib/db.js", "w", encoding="utf-8").write(db_content)
    print("addProduct added to db.js")
else:
    print("addProduct already in db.js")

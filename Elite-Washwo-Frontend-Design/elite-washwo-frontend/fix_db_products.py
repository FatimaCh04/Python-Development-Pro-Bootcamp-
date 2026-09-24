import re

db_content = open("src/lib/db.js", "r", encoding="utf-8").read()

fns = """
export async function updateProduct({ pkgId, productId, priceId, name, code, packagingName, unitCost, salesPrice }) {
  const { error: e1 } = await supabase.from('products').update({ name, code }).eq('id', productId);
  if (e1) throw e1;
  
  const { error: e2 } = await supabase.from('product_packaging').update({ name: packagingName }).eq('id', pkgId);
  if (e2) throw e2;
  
  if (priceId) {
    const { error: e3 } = await supabase.from('product_prices').update({ unit_cost: Number(unitCost), sales_price: Number(salesPrice) }).eq('id', priceId);
    if (e3) throw e3;
  }
  return true;
}

export async function deleteProduct(pkgId, productId) {
  // Try deleting the packaging variant first
  const { error: e1 } = await supabase.from('product_packaging').delete().eq('id', pkgId);
  if (e1) {
    if (e1.code === '23503') throw new Error('Cannot delete: Product is being used in transactions.');
    throw e1;
  }
  
  // Clean up parent product if no variants left
  const { count } = await supabase.from('product_packaging').select('id', { count: 'exact', head: true }).eq('product_id', productId);
  if (count === 0) {
    await supabase.from('products').delete().eq('id', productId);
  }
  return true;
}
"""

if "updateProduct" not in db_content:
    db_content += fns
    open("src/lib/db.js", "w", encoding="utf-8").write(db_content)
    print("Added updateProduct and deleteProduct to db.js")
else:
    print("updateProduct already exists")


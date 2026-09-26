import sys

content = open('src/lib/db.js', 'r', encoding='utf-8').read()

old_block = """  if (priceId) {
    const { error: e3 } = await supabase.from('product_prices').update({ unit_cost: Number(unitCost), sales_price: Number(salesPrice) }).eq('id', priceId);
    if (e3) throw e3;
  }
  return true;"""

new_block = """  if (priceId) {
    const { error: e3 } = await supabase.from('product_prices').update({ unit_cost: Number(unitCost), sales_price: Number(salesPrice) }).eq('id', priceId);
    if (e3) throw e3;
  } else {
    const { error: e4 } = await supabase.from('product_prices').insert({
      packaging_id: pkgId,
      unit_cost: Number(unitCost),
      sales_price: Number(salesPrice)
    });
    if (e4) throw e4;
  }
  return true;"""

if old_block in content:
    content = content.replace(old_block, new_block)
    open('src/lib/db.js', 'w', encoding='utf-8').write(content)
    print("Fixed updateProduct priceId logic")
else:
    print("Could not find the block. Here's what's there:")
    idx = content.find('updateProduct')
    print(repr(content[idx:idx+400]))

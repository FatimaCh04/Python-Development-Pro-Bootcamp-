content = open('src/lib/db.js', 'r', encoding='utf-8').read()

# Find and fix the submitSale function precisely using character-by-character
idx = content.find('submitSale({ salesmanId')
end = content.find('if (orderErr) throw orderErr;', idx) + len('if (orderErr) throw orderErr;')

old_block = content[idx:end]
print("Found block:")
print(repr(old_block))

new_block = """submitSale({ salesmanId, customerId, items, totalAmount }) {
  const { data: order, error: orderErr } = await supabase.from('sales_orders').insert({
    salesman_id: salesmanId,
    customer_id: customerId,
    total_amount: totalAmount,
    sale_date: new Date().toISOString(),
    status: 'Approved'
  }).select().single();
  
  if (orderErr) throw orderErr;"""

content = content[:idx] + new_block + content[end:]
open('src/lib/db.js', 'w', encoding='utf-8').write(content)
print('Done - submitSale fixed')

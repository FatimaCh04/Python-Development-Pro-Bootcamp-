import sys

content = open('src/lib/db.js', 'r', encoding='utf-8').read()

old_block = """export async function submitSale({ salesmanId, customerId, items, totalAmount }) {
  const { data: order, error: orderErr } = await supabase.from('sales_orders').insert({
    salesman_id: salesmanId,
    customer_id: customerId,
    total_amount: totalAmount,
    sale_date: new Date().toISOString(),
    status: 'Approved'
  }).select().single();"""

new_block = """export async function submitSale({ salesmanId, customerId, items, totalAmount }) {
  const ref = refNum('SAL');
  const { data: order, error: orderErr } = await supabase.from('sales_orders').insert({
    reference_number: ref,
    salesman_id: salesmanId,
    customer_id: customerId,
    total_amount: totalAmount,
    sale_date: new Date().toISOString(),
    status: 'Approved'
  }).select().single();"""

if old_block in content:
    content = content.replace(old_block, new_block)
    open('src/lib/db.js', 'w', encoding='utf-8').write(content)
    print("Fixed submitSale with reference_number!")
else:
    print("Could not find the block. Here's what's there:")
    idx = content.find('submitSale')
    print(repr(content[idx:idx+300]))

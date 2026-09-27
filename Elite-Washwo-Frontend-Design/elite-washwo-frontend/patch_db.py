with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

# Update fetchBookings to include distributor join and filters
old = (
    "export async function fetchBookings() {\n"
    "  const { data, error } = await supabase\n"
    "    .from('sales_orders')\n"
    "    .select('id, reference_number, sale_date, total_amount, status, customer_id, salesman_id, customers(name), salesmen(profiles(full_name))')\n"
    "    .like('reference_number', 'BKG-%')\n"
    "    .order('sale_date', { ascending: false });"
)
new = (
    "export async function fetchBookings({ dateFrom, dateTo, distributorId } = {}) {\n"
    "  let q = supabase\n"
    "    .from('sales_orders')\n"
    "    .select('id, reference_number, sale_date, total_amount, status, customer_id, salesman_id, distributor_id, customers(name), salesmen(profiles(full_name)), distributors(id, code, name, id_card, phone)')\n"
    "    .like('reference_number', 'BKG-%')\n"
    "    .order('sale_date', { ascending: false });\n"
    "  if (dateFrom) q = q.gte('sale_date', dateFrom);\n"
    "  if (dateTo) q = q.lte('sale_date', dateTo);\n"
    "  if (distributorId) q = q.eq('distributor_id', distributorId);\n"
    "  const { data, error } = await q;"
)

if old in c:
    c = c.replace(old, new)
    print('fetchBookings updated')
else:
    print('ERROR: could not find fetchBookings to patch. Snippet found:')
    idx = c.find('export async function fetchBookings')
    print(repr(c[idx:idx+400]))

# Update submitBooking signature
c = c.replace(
    'export async function submitBooking({ salesmanId, customerId, items, totalAmount }) {',
    'export async function submitBooking({ salesmanId, customerId, distributorId, items, totalAmount }) {'
)

# Update submitBooking insert payload to add distributor_id
old3 = (
    "    reference_number: ref,\n"
    "    salesman_id: salesmanId,\n"
    "    customer_id: customerId,\n"
    "    total_amount: totalAmount,\n"
    "    sale_date: new Date().toISOString(),\n"
    "    status: 'Pending'\n"
    "  }).select().single();"
)
new3 = (
    "    reference_number: ref,\n"
    "    salesman_id: salesmanId || null,\n"
    "    customer_id: customerId || null,\n"
    "    distributor_id: distributorId || null,\n"
    "    total_amount: totalAmount,\n"
    "    sale_date: new Date().toISOString(),\n"
    "    status: 'Pending'\n"
    "  }).select().single();"
)
if old3 in c:
    c = c.replace(old3, new3)
    print('submitBooking updated')
else:
    print('ERROR: could not find submitBooking payload to patch')

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)
print('db.js write complete')

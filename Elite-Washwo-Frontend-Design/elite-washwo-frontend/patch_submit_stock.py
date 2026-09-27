import re

with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace submitStockReturn
old_code = """  const payload = {
    reference_number: refNum('RTN'),
    transaction_date: new Date().toISOString(),
    packaging_id: packagingId,
    category,
    transaction_type,
    quantity: Number(quantity),
    unit_cost: Number(unit_cost),
    total_cost: Number(quantity) * Number(unit_cost),
    salesman_id: salesmanId || null,
    distributor_id: distributorId || null,
    status: 'Pending',
    notes
  };"""

new_code = """  const payload = {
    reference_number: refNum('RTN'),
    transaction_date: new Date().toISOString(),
    packaging_id: packagingId,
    category,
    transaction_type,
    quantity: Number(quantity),
    unit_cost: Number(unit_cost),
    total_cost: Number(quantity) * Number(unit_cost),
    status: 'Pending',
    notes
  };
  if (salesmanId) payload.salesman_id = salesmanId;
  if (distributorId) payload.distributor_id = distributorId;"""

c = c.replace(old_code, new_code)

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('Patched submitStockReturn')

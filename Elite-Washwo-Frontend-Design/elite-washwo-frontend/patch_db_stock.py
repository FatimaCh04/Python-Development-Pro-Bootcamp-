with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

# Update submitStockReturn
old = "export async function submitStockReturn({salesmanId,packagingId,transaction_type,quantity,notes,unit_cost=0}) {"
new = "export async function submitStockReturn({salesmanId, distributorId, packagingId, transaction_type, quantity, notes, unit_cost=0}) {"
c = c.replace(old, new)

old_ins = "salesman_id:salesmanId,status:'Pending',notes});"
new_ins = "salesman_id:salesmanId || null, distributor_id: distributorId || null, status:'Pending',notes});"
c = c.replace(old_ins, new_ins)

# Update fetchInventoryTransactions to pull distributors as well
old_fetch = "export async function fetchInventoryTransactions() {\n  const {data,error}=await supabase.from('inventory_transactions').select('id, reference_number, transaction_date, packaging_id, category, transaction_type, quantity, unit_cost, total_cost, salesman_id, customer_id, status, notes, product_packaging(name, products(name)), salesmen(profiles(full_name)), customers(name)').order('transaction_date', {ascending:false});"
new_fetch = "export async function fetchInventoryTransactions() {\n  const {data,error}=await supabase.from('inventory_transactions').select('id, reference_number, transaction_date, packaging_id, category, transaction_type, quantity, unit_cost, total_cost, salesman_id, customer_id, distributor_id, status, notes, product_packaging(name, products(name)), salesmen(profiles(full_name)), customers(name), distributors(id, code, name)').order('transaction_date', {ascending:false});"
c = c.replace(old_fetch, new_fetch)

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated db.js')

with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

# I need to fix submitStockReturn category logic.
import re

# We will replace the entire submitStockReturn function.
new_func = """export async function submitStockReturn({salesmanId, distributorId, packagingId, transaction_type, quantity, notes, unit_cost=0}) {
  let category = 'Damaged Stock';
  if (transaction_type.includes('Good_Return')) category = 'Sellable Stock';
  
  const payload = {
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
  };

  const {error} = await supabase.from('inventory_transactions').insert(payload);
  if(error) throw error;
}"""

# Find the start and end of the existing submitStockReturn
match = re.search(r'export async function submitStockReturn\([^)]*\)\s*\{.*?(?=\nexport async function|\n// ---)', c, re.DOTALL)
if match:
    c = c.replace(match.group(0), new_func + "\n")
else:
    print("Could not find submitStockReturn with regex!")

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)
print("db.js updated with improved submitStockReturn")

import sys

content = open('src/lib/db.js', 'r', encoding='utf-8').read()

# Fix 1: Remove created_by from submitSale (column doesn't exist in DB)
old_sale = """      salesman_id: salesmanId,
      customer_id: customerId,
      total_amount: totalAmount,
      sale_date: new Date().toISOString(),
      status: 'Approved',
      created_by
    }).select().single();"""

new_sale = """      salesman_id: salesmanId,
      customer_id: customerId,
      total_amount: totalAmount,
      sale_date: new Date().toISOString(),
      status: 'Approved'
    }).select().single();"""

if old_sale in content:
    content = content.replace(old_sale, new_sale)
    print('Fixed submitSale - removed created_by')
else:
    print('Pattern not found for submitSale fix')

# Fix 2: Also remove the profile/created_by lookup lines that are now unused
old_lookup = """  const { data: user } = await supabase.auth.getUser();
    const { data: profile } = await supabase.from('profiles').select('full_name').eq('id', user.user?.id).single();
    const created_by = profile?.full_name || 'System';
  
    const { data: order"""

new_lookup = """  const { data: order"""

if old_lookup in content:
    content = content.replace(old_lookup, new_lookup)
    print('Removed unused created_by lookup')
else:
    print('Lookup pattern not found - skipping')

open('src/lib/db.js', 'w', encoding='utf-8').write(content)
print('db.js saved')

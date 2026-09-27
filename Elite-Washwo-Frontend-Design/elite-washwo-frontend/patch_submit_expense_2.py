with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

import re

old_submitExpense = re.search(r'export async function submitExpense\(\{.*?\}\s*\{\s*const payload = \{.*?\};\s*const \{error\} = await supabase\.from\(\'expenses\'\)\.insert\(payload\);\s*if\(error\) throw error;\s*\}', c, re.DOTALL).group(0)
new_submitExpense = """export async function submitExpense({ expenseType, distributorId, amount, accountDetail, tid, notes, head }) {
  const { data: smData } = await supabase.from('salesmen').select('id').limit(1);
  const fallbackSmId = smData && smData.length > 0 ? smData[0].id : null;

  const payload = {
    reference_number: refNum('EXP'),
    expense_date: new Date().toISOString(),
    category: expenseType, 
    amount: Number(amount),
    account_detail: accountDetail || null,
    tid: tid || null,
    description: notes || '', 
    head: head || null,
    distributor_id: expenseType === 'Distributor' ? distributorId : null,
    salesman_id: fallbackSmId, 
    status: 'Pending'
  };
  const {error} = await supabase.from('expenses').insert(payload);
  if(error) throw error;
}"""

c = c.replace(old_submitExpense, new_submitExpense)

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated submitExpense with salesman_id fallback properly')

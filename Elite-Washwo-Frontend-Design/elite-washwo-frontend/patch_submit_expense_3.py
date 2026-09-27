with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('export async function submitExpense({ expenseType')
end = c.find('export async function updateExpenseStatus')

old_func = c[idx:end]
new_func = """export async function submitExpense({ expenseType, distributorId, amount, accountDetail, tid, notes, head }) {
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
}

"""

c = c.replace(old_func, new_func)

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated submitExpense accurately')

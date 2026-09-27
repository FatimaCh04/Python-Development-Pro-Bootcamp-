with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('export async function submitExpense({ expenseType')
end = c.find('export async function updateExpenseStatus')

old_func = c[idx:end]
new_func = """export async function submitExpense({ expenseType, distributorId, amount, accountDetail, tid, notes, head }) {
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
    status: 'Pending'
  };
  const {error} = await supabase.from('expenses').insert(payload);
  if(error) {
    if (error.code === '23502' && error.message.includes('salesman_id')) {
      throw new Error("SCHEMA ERROR: Cannot save expense because the database still requires a salesman. Please run this SQL in Supabase: ALTER TABLE expenses ALTER COLUMN salesman_id DROP NOT NULL;");
    }
    throw error;
  }
}

"""

c = c.replace(old_func, new_func)

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated submitExpense accurately')

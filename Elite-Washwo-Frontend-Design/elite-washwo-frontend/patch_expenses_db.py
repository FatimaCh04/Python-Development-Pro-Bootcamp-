with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Update fetchExpenses
old_fetchExpenses = re.search(r'export async function fetchExpenses\(filters=\{\}\) \{.*?\n\}', c, re.DOTALL).group(0)
new_fetchExpenses = """export async function fetchExpenses(filters={}) {
  let q=supabase.from('expenses').select('*, salesmen(profiles(full_name)), distributors(name, code)').order('expense_date',{ascending:false}).limit(100);
  if(filters.distributor_id) q=q.eq('distributor_id',filters.distributor_id);
  if(filters.type && filters.type !== 'All') q=q.eq('category', filters.type);
  if(filters.status && filters.status !== 'All') q=q.eq('status',filters.status);
  const {data,error}=await q;
  if(error) throw error;
  return data||[];
}"""
c = c.replace(old_fetchExpenses, new_fetchExpenses)

# Update submitExpense
old_submitExpense = re.search(r'export async function submitExpense\(.*?\) \{.*?\n\}', c, re.DOTALL).group(0)
new_submitExpense = """export async function submitExpense({ expenseType, distributorId, amount, accountDetail, tid, notes, head }) {
  const payload = {
    reference_number: refNum('EXP'),
    expense_date: new Date().toISOString(),
    category: expenseType, // Store Expense Type in category
    amount: Number(amount),
    account_detail: accountDetail || null,
    tid: tid || null,
    description: notes || '', // Map Notes to existing description field
    head: head || null,
    distributor_id: expenseType === 'Distributor' ? distributorId : null,
    status: 'Pending'
  };
  const {error} = await supabase.from('expenses').insert(payload);
  if(error) throw error;
}"""
c = c.replace(old_submitExpense, new_submitExpense)

# Update fetchExpenseSummary
old_fetchExpenseSummary = re.search(r'export async function fetchExpenseSummary\(\) \{.*?return \{.*?\};\n\}', c, re.DOTALL).group(0)
new_fetchExpenseSummary = """export async function fetchExpenseSummary() {
  const monthStart=new Date();monthStart.setDate(1);monthStart.setHours(0,0,0,0);
  const {data}=await supabase.from('expenses').select('amount,status,category').gte('expense_date',monthStart.toISOString());
  const total=(data||[]).reduce((s,r)=>s+Number(r.amount),0);
  
  let distributor = 0;
  let company = 0;
  let office = 0;
  let others = 0;
  
  (data||[]).forEach(r => {
    const amt = Number(r.amount);
    if (r.category === 'Distributor') distributor += amt;
    else if (r.category === 'Company') company += amt;
    else if (r.category === 'Office') office += amt;
    else if (r.category === 'Others') others += amt;
    // Historical categories will just not add to these specific buckets, but are included in total
  });
  
  return {total, distributor, company, office, others};
}"""
c = c.replace(old_fetchExpenseSummary, new_fetchExpenseSummary)

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated db.js expense functions')

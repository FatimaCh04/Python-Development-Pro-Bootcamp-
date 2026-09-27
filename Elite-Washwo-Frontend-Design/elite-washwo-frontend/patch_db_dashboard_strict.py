with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Remove the previously added fetchDashboardMetrics if it exists
match = re.search(r'export async function fetchDashboardMetrics\([^)]*\)\s*\{.*?\n}\n?', c, re.DOTALL)
if match:
    c = c.replace(match.group(0), '')

new_func = """export async function fetchDashboardMetrics(selectedDateStr) {
  const dateObj = selectedDateStr ? new Date(selectedDateStr + 'T00:00:00') : new Date();
  
  const endOfDay = new Date(dateObj);
  endOfDay.setHours(23,59,59,999);
  const eodIso = endOfDay.toISOString();
  
  const startOfDay = new Date(dateObj);
  startOfDay.setHours(0,0,0,0);
  const sodIso = startOfDay.toISOString();

  // 1. INVENTORY TRANSACTIONS (Cumulative up to EOD)
  const { data: invRows } = await supabase
    .from('inventory_transactions')
    .select('transaction_type, quantity, distributor_id, salesman_id')
    .in('status', ['Approved', 'Posted'])
    .lte('transaction_date', eodIso);

  let companyStock = 0;
  let distReturnStock = 0;
  let damageReturnStock = 0;

  (invRows || []).forEach(r => {
    const qty = Number(r.quantity) || 0;
    const isGoodReturn = ['Salesman_Good_Return', 'Customer_Good_Return'].includes(r.transaction_type);
    const isDamagedReturn = ['Salesman_Damaged_Return', 'Customer_Damaged_Return'].includes(r.transaction_type);
    
    // Company Saleable Stock (Cumulative)
    if (['Production', 'Purchase'].includes(r.transaction_type) || isGoodReturn) {
       companyStock += qty;
    }
    if (['Salesman_Issue', 'Distributor_Issue'].includes(r.transaction_type)) {
       companyStock -= qty;
    }
    if (['Adjustment', 'Damage', 'Expiry'].includes(r.transaction_type)) {
       // Assuming these are direct company stock adjustments if no SM/Dist is assigned
       if (!r.salesman_id && !r.distributor_id) {
         companyStock -= qty;
       }
    }

    // Distributor Return Stock (Cumulative) - explicitly identified by distributor_id
    if (r.distributor_id && (isGoodReturn || isDamagedReturn)) {
       distReturnStock += qty;
    }
    
    // Damage Return Stock (Cumulative) - all approved damaged returns
    if (isDamagedReturn) {
       damageReturnStock += qty;
    }
  });

  // 2. GLOBAL SETTINGS
  const { data: gs } = await supabase.from('global_settings').select('*').limit(1).single();
  const advOpening = Number(gs?.advertisement_opening_balance) || 0;
  const welfOpening = Number(gs?.welfare_opening_balance) || 0;

  // 3. SALES & SALE ITEMS (Cumulative & Selected Date)
  const { data: allSales } = await supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, distributor_id, distributors(commission), sale_items(quantity)')
    .like('reference_number', 'SAL-%')
    .in('status', ['Approved', 'Posted'])
    .lte('sale_date', eodIso);

  let salesSelectedDateAmount = 0;
  let commissionSelectedDate = 0;
  let cumulativeDistSalesAmount = 0;
  let cumulativePkts = 0;

  (allSales || []).forEach(sale => {
    const isSelectedDate = sale.sale_date >= sodIso && sale.sale_date <= eodIso;
    const pkts = (sale.sale_items || []).reduce((a, item) => a + Number(item.quantity || 0), 0);
    const amt = Number(sale.total_amount) || 0;
    
    cumulativePkts += pkts;
    
    if (sale.distributor_id) {
       cumulativeDistSalesAmount += amt;
    }

    if (isSelectedDate) {
      salesSelectedDateAmount += amt;
      const commRate = Number(sale.distributors?.commission) || 30;
      commissionSelectedDate += (pkts * commRate);
    }
  });

  // 4. RECOVERIES (Cumulative for Outstanding)
  // FIXED: Only include 'Approved', 'Posted' statuses.
  const { data: allRecs } = await supabase
    .from('recoveries')
    .select('amount, distributor_id')
    .in('status', ['Approved', 'Posted'])
    .lte('recovery_date', eodIso);
    
  let cumulativeDistRecAmount = 0;
  (allRecs || []).forEach(r => {
    if (r.distributor_id) {
       cumulativeDistRecAmount += Number(r.amount || 0);
    }
  });
  
  const distributorsOutstanding = Math.max(0, cumulativeDistSalesAmount - cumulativeDistRecAmount);

  // 5. EXPENSES (Cumulative & Selected Date)
  const { data: allExps } = await supabase
    .from('expenses')
    .select('amount, expense_date, head, category')
    .in('status', ['Approved', 'Posted'])
    .lte('expense_date', eodIso);

  let expensesSelectedDate = 0;
  let cumulativeAdvExp = 0;
  let cumulativeWelfExp = 0;

  (allExps || []).forEach(exp => {
    const amt = Number(exp.amount) || 0;
    const isSelectedDate = exp.expense_date >= sodIso && exp.expense_date <= eodIso;
    
    if (isSelectedDate) {
       expensesSelectedDate += amt;
    }
    
    if (exp.head === 'Advertisement' || exp.category === 'Advertisement') {
       cumulativeAdvExp += amt;
    }
    if (exp.head === 'Welfare' || exp.category === 'Welfare') {
       cumulativeWelfExp += amt;
    }
  });

  const advertisementBalance = advOpening + (cumulativePkts * 20) - cumulativeAdvExp;
  const welfareBalance = welfOpening + (cumulativePkts * 10) - cumulativeWelfExp;

  return {
    companyStock,
    salesAmount: salesSelectedDateAmount,
    distributorsOutstanding,
    expensesAmount: expensesSelectedDate,
    advertisementBalance,
    welfareBalance,
    commissionAmount: commissionSelectedDate,
    distReturnStock,
    damageReturnStock
  };
}
"""

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c + '\n' + new_func)

print('Updated fetchDashboardMetrics in db.js')

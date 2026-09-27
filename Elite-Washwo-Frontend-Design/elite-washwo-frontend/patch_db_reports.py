with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Remove any existing fetchReportsMetrics if I created one previously (unlikely, but safe)
match = re.search(r'export async function fetchReportsMetrics\([^)]*\)\s*\{.*?\n}\n?', c, re.DOTALL)
if match:
    c = c.replace(match.group(0), '')

new_func = """export async function fetchReportsMetrics(selectedDateStr) {
  const dateObj = selectedDateStr ? new Date(selectedDateStr + 'T00:00:00') : new Date();
  
  const endOfDay = new Date(dateObj);
  endOfDay.setHours(23,59,59,999);
  const eodIso = endOfDay.toISOString();
  
  const startOfDay = new Date(dateObj);
  startOfDay.setHours(0,0,0,0);
  const sodIso = startOfDay.toISOString();

  // 1. GLOBAL SETTINGS
  const { data: gs } = await supabase.from('global_settings').select('*').limit(1).single();
  const advOpening = Number(gs?.advertisement_opening_balance) || 0;
  const welfOpening = Number(gs?.welfare_opening_balance) || 0;

  // 2. BOOKINGS (Selected Date)
  const { data: bookingsData } = await supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, status, distributor_id, distributors(name, code), sale_items(quantity)')
    .like('reference_number', 'BKG-%')
    .eq('status', 'Pending')
    .gte('sale_date', sodIso)
    .lte('sale_date', eodIso);
    
  const bookings = (bookingsData || []).map(b => {
    const packets = (b.sale_items || []).reduce((acc, item) => acc + Number(item.quantity || 0), 0);
    return { ...b, packets };
  });

  // 3. SALES (Cumulative for Adv/Welf, Selected Date for Commission)
  const { data: allSales } = await supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, distributor_id, distributors(commission), sale_items(quantity)')
    .like('reference_number', 'SAL-%')
    .in('status', ['Approved', 'Posted'])
    .lte('sale_date', eodIso);
    
  let cumulativeSalePackets = 0;
  let selectedDateCommission = 0;
  
  (allSales || []).forEach(sale => {
    const isSelectedDate = sale.sale_date >= sodIso && sale.sale_date <= eodIso;
    const pkts = (sale.sale_items || []).reduce((a, item) => a + Number(item.quantity || 0), 0);
    cumulativeSalePackets += pkts;
    
    if (isSelectedDate) {
      const commRate = Number(sale.distributors?.commission) || 0;
      selectedDateCommission += (pkts * commRate);
    }
  });

  // 4. EXPENSES (Cumulative & Selected Date)
  const { data: allExps } = await supabase
    .from('expenses')
    .select('amount, expense_date, category, status, account_detail, tid, description, head, distributor_id, distributors(name, code)')
    .in('status', ['Approved', 'Posted'])
    .lte('expense_date', eodIso);
    
  let cumCompanyOfficeExp = 0;
  let cumOthersExp = 0;
  let selectedDateDistExp = 0;
  const selectedDateExpenses = [];
  
  (allExps || []).forEach(exp => {
    const amt = Number(exp.amount) || 0;
    const isSelectedDate = exp.expense_date >= sodIso && exp.expense_date <= eodIso;
    
    if (isSelectedDate) {
      selectedDateExpenses.push(exp);
    }
    
    // Categorize for cumulative accounts
    if (exp.category === 'Company' || exp.category === 'Office') {
      cumCompanyOfficeExp += amt;
    } else if (exp.category === 'Others') {
      cumOthersExp += amt;
    }
    
    // Distributor expense for selected date
    if (isSelectedDate && exp.category === 'Distributor' && exp.distributor_id) {
      selectedDateDistExp += amt;
    }
  });

  // 5. RECOVERIES (Selected Date)
  const { data: recoveriesData } = await supabase
    .from('recoveries')
    .select('amount, recovery_date, status, account_detail, tid, notes, distributor_id, distributors(name, code)')
    .in('status', ['Approved', 'Posted'])
    .gte('recovery_date', sodIso)
    .lte('recovery_date', eodIso);

  // 6. RETURNS (Selected Date)
  const { data: returnsData } = await supabase
    .from('inventory_transactions')
    .select('id, reference_number, transaction_type, quantity, status, transaction_date, notes, distributor_id, distributors(name, code)')
    .in('status', ['Approved'])
    .not('distributor_id', 'is', null)
    .gte('transaction_date', sodIso)
    .lte('transaction_date', eodIso);
    
  const returns = (returnsData || []).filter(r => 
    r.transaction_type === 'Salesman_Good_Return' || r.transaction_type === 'Salesman_Damaged_Return'
  );

  // 7. STOCK (Cumulative up to EOD)
  const { data: invAll } = await supabase
    .from('inventory_transactions')
    .select('transaction_type, quantity, distributor_id, salesman_id')
    .in('status', ['Approved', 'Posted'])
    .lte('transaction_date', eodIso);
    
  let stockSellable = 0;
  let stockDamaged = 0;
  
  (invAll || []).forEach(r => {
    const qty = Number(r.quantity) || 0;
    const isGoodReturn = ['Salesman_Good_Return', 'Customer_Good_Return'].includes(r.transaction_type);
    const isDamagedReturn = ['Salesman_Damaged_Return', 'Customer_Damaged_Return'].includes(r.transaction_type);
    
    if (['Production', 'Purchase'].includes(r.transaction_type) || isGoodReturn) {
       stockSellable += qty;
    }
    if (['Salesman_Issue', 'Distributor_Issue'].includes(r.transaction_type)) {
       stockSellable -= qty;
    }
    if (['Adjustment', 'Damage', 'Expiry'].includes(r.transaction_type) && !r.salesman_id && !r.distributor_id) {
       stockSellable -= qty;
       if (r.transaction_type === 'Damage') stockDamaged += qty;
    }
    if (isDamagedReturn) {
       stockDamaged += qty;
    }
  });

  // Calculate Balances
  const distributorCommissionBalance = Math.max(0, selectedDateCommission - selectedDateDistExp);
  const advAllocation = cumulativeSalePackets * 20;
  const advertisementBalance = advOpening + advAllocation - cumCompanyOfficeExp;
  
  const welfAllocation = cumulativeSalePackets * 10;
  const welfareBalance = welfOpening + welfAllocation - cumOthersExp;

  return {
    booking: {
      records: bookings
    },
    recovery: {
      records: recoveriesData || []
    },
    expense: {
      records: selectedDateExpenses
    },
    returns: {
      records: returns
    },
    stock: {
      sellable: stockSellable,
      damaged: stockDamaged
    },
    distributorCommission: {
      allocation: selectedDateCommission,
      expenses: selectedDateDistExp,
      balance: distributorCommissionBalance
    },
    advertisement: {
      opening: advOpening,
      allocation: advAllocation,
      expenses: cumCompanyOfficeExp,
      balance: advertisementBalance
    },
    welfare: {
      opening: welfOpening,
      allocation: welfAllocation,
      expenses: cumOthersExp,
      balance: welfareBalance
    }
  };
}
"""

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c + '\n' + new_func)

print('Appended fetchReportsMetrics to db.js')

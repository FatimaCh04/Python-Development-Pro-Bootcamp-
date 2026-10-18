/**
 * Elite Washwo  Database Service Layer
 * All Supabase queries centralized here.
 */
import { supabase } from './supabase';

const refNum = (prefix) => `${prefix}-${Date.now().toString(36).toUpperCase()}`;

// --- OVERVIEW ----------------------------------------------------------------
export async function fetchOverviewStats() {
  const { data: invRows } = await supabase
    .from('inventory_transactions')
    .select('transaction_type, quantity, status, salesman_id')
    .in('status', ['Approved', 'Posted']);

  let sellable = 0;
  (invRows || []).forEach(r => {
    if (r.salesman_id) return;
    if (['Production','Purchase','Salesman_Good_Return','Customer_Good_Return'].includes(r.transaction_type)) sellable += r.quantity;
    if (['Salesman_Issue','Adjustment','Damage','Expiry'].includes(r.transaction_type)) sellable -= r.quantity;
  });

  const monthStart = new Date(); monthStart.setDate(1); monthStart.setHours(0,0,0,0);
  const { data: salesRows } = await supabase.from('sales_orders').select('total_amount').in('status',['Approved','Posted']).not('reference_number', 'like', 'BKG-%').gte('sale_date', monthStart.toISOString());
  const salesTotal = (salesRows||[]).reduce((s,r)=>s+Number(r.total_amount),0);

  const todayStart = new Date(); todayStart.setHours(0,0,0,0);
  const { data: recRows } = await supabase.from('recoveries').select('amount').in('status',['Approved','Posted']).gte('recovery_date', todayStart.toISOString());
  const recoveryToday = (recRows||[]).reduce((s,r)=>s+Number(r.amount),0);

  const { data: allSales } = await supabase.from('sales_orders').select('total_amount').in('status',['Approved','Posted']).not('reference_number', 'like', 'BKG-%');
  const { data: allRec }   = await supabase.from('recoveries').select('amount').in('status',['Approved','Posted']);
  const outstanding = Math.max(0,(allSales||[]).reduce((s,r)=>s+Number(r.total_amount),0)-(allRec||[]).reduce((s,r)=>s+Number(r.amount),0));

  const { data: damRows } = await supabase.from('inventory_transactions').select('quantity').eq('transaction_type','Damage').in('status',['Approved','Posted']);
  const damaged = (damRows||[]).reduce((s,r)=>s+r.quantity,0);

  const { data: pendExp } = await supabase.from('expenses').select('amount').in('status',['Pending','Submitted']);
  const pendingReimb = (pendExp||[]).reduce((s,r)=>s+Number(r.amount),0);

  return { sellable, salesTotal, recoveryToday, outstanding, damaged, pendingReimb };
}

export async function fetchRecentAuditLogs(limit = 6) {
  const { data } = await supabase.from('audit_logs').select('*, profiles(full_name)').order('created_at',{ascending:false}).limit(limit);
  return data || [];
}

export async function fetchSalesmenSnapshot() {
  const { data: salesmen } = await supabase.from('salesmen').select('id, code, route, profiles(full_name)');
  const { data: invRows }  = await supabase.from('inventory_transactions').select('salesman_id, transaction_type, quantity').in('status',['Approved','Posted']).not('salesman_id','is',null);
  const { data: salesRows }= await supabase.from('sales_orders').select('salesman_id, total_amount').in('status',['Approved','Posted']);
  const { data: recRows }  = await supabase.from('recoveries').select('salesman_id, amount').in('status',['Approved','Posted']);

  const stockMap={}, salesMap={}, recMap={};
  (invRows||[]).forEach(r=>{
    if(!stockMap[r.salesman_id]) stockMap[r.salesman_id]=0;
    if(r.transaction_type==='Salesman_Issue') stockMap[r.salesman_id]+=r.quantity;
    if(['Sale','Salesman_Good_Return','Salesman_Damaged_Return'].includes(r.transaction_type)) stockMap[r.salesman_id]-=r.quantity;
  });
  (salesRows||[]).forEach(r=>{salesMap[r.salesman_id]=(salesMap[r.salesman_id]||0)+Number(r.total_amount);});
  (recRows||[]).forEach(r=>{recMap[r.salesman_id]=(recMap[r.salesman_id]||0)+Number(r.amount);});

  return (salesmen||[]).map(s=>({id:s.id,name:s.profiles?.full_name||s.code,stock:stockMap[s.id]||0,outstanding:Math.max(0,(salesMap[s.id]||0)-(recMap[s.id]||0)),route:s.route}));
}

export async function fetchChartData() {
  const days = Array.from({length:7},(_,i)=>{const d=new Date();d.setDate(d.getDate()-6+i);return d.toISOString().slice(0,10);});
  const from=days[0]; const to=days[6];
  const {data:salesRows}=await supabase.from('sales_orders').select('sale_date,total_amount').in('status',['Approved','Posted']).gte('sale_date',from).lte('sale_date',to+'T23:59:59');
  const {data:recRows}=await supabase.from('recoveries').select('recovery_date,amount').in('status',['Approved','Posted']).gte('recovery_date',from).lte('recovery_date',to+'T23:59:59');
  const sbd={},rbd={};
  days.forEach(d=>{sbd[d]=0;rbd[d]=0;});
  (salesRows||[]).forEach(r=>{const d=r.sale_date.slice(0,10);if(sbd[d]!==undefined)sbd[d]+=Number(r.total_amount);});
  (recRows||[]).forEach(r=>{const d=r.recovery_date.slice(0,10);if(rbd[d]!==undefined)rbd[d]+=Number(r.amount);});
  return {labels:days.map(d=>{const dt=new Date(d);return dt.toLocaleDateString('en',{day:'numeric',month:'short'});}),sales:days.map(d=>sbd[d]),recovery:days.map(d=>rbd[d])};
}

// --- SALESMEN -----------------------------------------------------------------
export async function fetchSalesmen() {
  const {data,error}=await supabase.from('salesmen').select('*, profiles(full_name, is_active)').order('code');
  if(error) throw error;
  return data||[];
}

export async function fetchSalesmanStats(salesmanId) {
  const {data:inv}=await supabase.from('inventory_transactions').select('transaction_type,quantity').eq('salesman_id',salesmanId).in('status',['Approved','Posted']);
  let stock=0;
  (inv||[]).forEach(r=>{if(r.transaction_type==='Salesman_Issue')stock+=r.quantity;if(['Sale','Salesman_Good_Return','Salesman_Damaged_Return'].includes(r.transaction_type))stock-=r.quantity;});
  const todayStart=new Date();todayStart.setHours(0,0,0,0);
  const {data:ts}=await supabase.from('sales_orders').select('total_amount').eq('salesman_id',salesmanId).in('status',['Approved','Posted']).gte('sale_date',todayStart.toISOString());
  const todaySalesAmt=(ts||[]).reduce((s,r)=>s+Number(r.total_amount),0);
  const {data:as}=await supabase.from('sales_orders').select('total_amount').eq('salesman_id',salesmanId).in('status',['Approved','Posted']);
  const {data:ar}=await supabase.from('recoveries').select('amount').eq('salesman_id',salesmanId).in('status',['Approved','Posted']);
  const outstanding=Math.max(0,(as||[]).reduce((s,r)=>s+Number(r.total_amount),0)-(ar||[]).reduce((s,r)=>s+Number(r.amount),0));
  const {data:pe}=await supabase.from('expenses').select('amount').eq('salesman_id',salesmanId).in('status',['Pending','Submitted']);
  const pendingReimb=(pe||[]).reduce((s,r)=>s+Number(r.amount),0);
  return {stock,todaySalesAmt,outstanding,pendingReimb};
}

export async function fetchSalesmanStockLedger(salesmanId) {
  const {data,error}=await supabase.from('inventory_transactions').select('*, product_packaging(name, products(name))').eq('salesman_id',salesmanId).order('transaction_date',{ascending:false});
  if(error) throw error;
  return data||[];
}

export async function fetchSalesmanFinLedger(salesmanId) {
  const {data:sales}=await supabase.from('sales_orders').select('reference_number,sale_date,total_amount,status').eq('salesman_id',salesmanId).order('sale_date',{ascending:false});
  const {data:recs}=await supabase.from('recoveries').select('reference_number,recovery_date,amount,payment_method,status').eq('salesman_id',salesmanId).order('recovery_date',{ascending:false});
  const rows=[];
  (sales||[]).forEach(r=>rows.push({date:r.sale_date,type:'Sale (credit)',ref:r.reference_number,debit:r.total_amount,credit:null,status:r.status}));
  (recs||[]).forEach(r=>rows.push({date:r.recovery_date,type:`Recovery  ${r.payment_method}`,ref:r.reference_number,debit:null,credit:r.amount,status:r.status}));
  rows.sort((a,b)=>new Date(a.date)-new Date(b.date));
  let bal=0;
  const withBal=rows.map(r=>{if(r.debit)bal+=Number(r.debit);if(r.credit)bal-=Number(r.credit);return{...r,balance:bal};});
  return withBal.reverse();
}

export async function fetchSalesmanExpLedger(salesmanId) {
  const {data,error}=await supabase.from('expenses').select('*').eq('salesman_id',salesmanId).order('expense_date',{ascending:false});
  if(error) throw error;
  return data||[];
}

// --- STOCK / RETURNS ----------------------------------------------------------
export async function fetchInventoryTransactions(filters={}) {
  let q=supabase.from('inventory_transactions').select('*, salesmen(profiles(full_name)), distributors(name, code, phone), product_packaging(name, products(name))').order('transaction_date',{ascending:false}).limit(200);
  if(filters.salesman_id) q=q.eq('salesman_id',filters.salesman_id);
  if(filters.distributor_id) q=q.eq('distributor_id',filters.distributor_id);
  if(filters.transaction_type && filters.transaction_type !== 'All') q=q.eq('transaction_type',filters.transaction_type);
  if(filters.status && filters.status !== 'All') q=q.eq('status',filters.status);
  const {data,error}=await q;
  if(error) throw error;
  return data||[];
}

export async function fetchStockBalances(asOfDate = null) {
  let q = supabase
    .from('inventory_transactions')
    .select('transaction_type, quantity, status, distributor_id, salesman_id, category, transaction_date')
    .in('status', ['Approved', 'Posted']);

  if (asOfDate) {
    const d = new Date(asOfDate);
    d.setHours(23, 59, 59, 999);
    q = q.lte('transaction_date', d.toISOString());
  }

  const { data, error } = await q;
  if (error) throw error;

  let saleableStock = 0;
  let issuedStock = 0;
  let goodReturns = 0;
  let damagedStock = 0;
  let productionPurchases = 0;
  let adjustments = 0;

  (data || []).forEach(r => {
    const qty = Number(r.quantity) || 0;
    const isGoodReturn = ['Salesman_Good_Return', 'Customer_Good_Return', 'Distributor_Good_Return'].includes(r.transaction_type);
    const isDamagedReturn = ['Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Distributor_Damaged_Return', 'Damage', 'Expiry'].includes(r.transaction_type);

    if (['Production', 'Purchase'].includes(r.transaction_type)) {
      productionPurchases += qty;
      saleableStock += qty;
    } else if (['Salesman_Issue', 'Distributor_Issue'].includes(r.transaction_type)) {
      saleableStock -= qty;
      issuedStock += qty;
    } else if (isGoodReturn) {
      goodReturns += qty;
      saleableStock += qty; // Good returns enter company saleable stock after approval
      if (r.distributor_id || r.salesman_id) {
        issuedStock = Math.max(0, issuedStock - qty);
      }
    } else if (isDamagedReturn) {
      damagedStock += qty; // Damaged returns enter damaged stock, NOT saleable stock
      if (r.distributor_id || r.salesman_id) {
        issuedStock = Math.max(0, issuedStock - qty);
      }
    } else if (r.transaction_type === 'Adjustment') {
      adjustments += qty;
      saleableStock += qty;
    } else if (r.transaction_type === 'Sale') {
      if (r.distributor_id || r.salesman_id) {
        issuedStock = Math.max(0, issuedStock - qty);
      }
    }
  });

  return {
    saleableStock,
    issuedStock,
    goodReturns,
    damagedStock,
    productionPurchases,
    adjustments
  };
}

export async function submitStockReturn({salesmanId, distributorId, packagingId, transaction_type, quantity, notes, unit_cost=0}) {
  const qty = Number(quantity);
  if (!qty || qty <= 0) throw new Error('Return quantity must be greater than zero.');
  if (!packagingId) throw new Error('Product packaging variant is required.');
  if (!distributorId && !salesmanId) throw new Error('Distributor or Salesman selection is required.');

  let category = 'Damaged Stock';
  if (transaction_type.includes('Good_Return')) category = 'Sellable Stock';
  
  const payload = {
    reference_number: refNum('RTN'),
    transaction_date: new Date().toISOString(),
    packaging_id: packagingId,
    category,
    transaction_type,
    quantity: qty,
    unit_cost: Number(unit_cost) || 0,
    total_cost: qty * (Number(unit_cost) || 0),
    status: 'Pending',
    notes: notes || ''
  };
  if (salesmanId) payload.salesman_id = salesmanId;
  if (distributorId) payload.distributor_id = distributorId;

  const {data, error} = await supabase.from('inventory_transactions').insert(payload).select().single();
  if(error) throw error;
  return data;
}

export async function submitInventoryMovement({
  transaction_type,
  packagingId,
  quantity,
  distributorId = null,
  salesmanId = null,
  unit_cost = 0,
  notes = '',
  status = 'Approved',
  isAuthorizedAdjustment = false
}) {
  const qty = Number(quantity);
  if (!qty || qty <= 0) throw new Error('Quantity must be greater than zero.');
  if (!packagingId) throw new Error('Product packaging variant is required.');

  // Prevent negative stock for physical stock issuance unless explicitly authorized
  if (transaction_type === 'Distributor_Issue' || transaction_type === 'Salesman_Issue') {
    if (!distributorId && !salesmanId) throw new Error('Distributor selection is required to issue stock.');
    const balances = await fetchStockBalances();
    if (balances.saleableStock < qty && !isAuthorizedAdjustment) {
      throw new Error(`Insufficient saleable stock. Available: ${balances.saleableStock.toLocaleString()} pkts, Requested: ${qty.toLocaleString()} pkts. Negative stock is strictly prevented unless explicitly authorized.`);
    }
  }

  let prefix = 'TRX';
  let category = 'Sellable Stock';
  if (transaction_type === 'Distributor_Issue' || transaction_type === 'Salesman_Issue') {
    prefix = 'ISS';
  } else if (transaction_type === 'Production') {
    prefix = 'PRD';
  } else if (transaction_type === 'Purchase') {
    prefix = 'PUR';
  } else if (transaction_type === 'Adjustment') {
    prefix = 'ADJ';
    category = 'Adjustment';
  }

  const payload = {
    reference_number: refNum(prefix),
    transaction_date: new Date().toISOString(),
    packaging_id: packagingId,
    category,
    transaction_type,
    quantity: qty,
    unit_cost: Number(unit_cost) || 0,
    total_cost: qty * (Number(unit_cost) || 0),
    status,
    notes: notes || ''
  };

  if (distributorId) payload.distributor_id = distributorId;
  if (salesmanId) payload.salesman_id = salesmanId;

  const { data, error } = await supabase.from('inventory_transactions').insert(payload).select().single();
  if (error) throw error;
  return data;
}

export async function approveTransaction(id) {
  const {error}=await supabase.from('inventory_transactions').update({status:'Approved', updated_at: new Date().toISOString()}).eq('id',id);
  if(error) throw error;
}

export async function cancelTransaction(id, reason = '') {
  const {error}=await supabase.from('inventory_transactions').update({
    status: 'Cancelled',
    notes: reason ? `[Cancelled: ${reason}]` : '[Cancelled]',
    updated_at: new Date().toISOString()
  }).eq('id', id);
  if(error) throw error;
}

// --- EXPENSES -----------------------------------------------------------------
export async function fetchExpenses(filters={}) {
  let q=supabase.from('expenses').select('*, salesmen(profiles(full_name)), distributors(name, code), persons(name, code, category)').order('expense_date',{ascending:false}).limit(200);
  if(filters.distributor_id) q=q.eq('distributor_id',filters.distributor_id);
  if(filters.person_id) q=q.eq('person_id',filters.person_id);
  if(filters.type && filters.type !== 'All') q=q.eq('category', filters.type);
  if(filters.status && filters.status !== 'All') q=q.eq('status',filters.status);
  const {data,error}=await q;
  if(error) throw error;
  return data||[];
}

export async function submitExpense({
  expenseType,
  distributorId,
  personId,
  amount,
  expenseDate,
  paymentMethod = 'Cash',
  accountDetail,
  tid,
  notes,
  head
}) {
  const amt = Number(amount);
  if (!amt || amt <= 0) throw new Error('Expense amount must be greater than zero.');
  if (expenseType === 'Distributor' && !distributorId) throw new Error('Distributor is required for Distributor expenses.');

  const payload = {
    reference_number: refNum('EXP'),
    expense_date: expenseDate ? new Date(expenseDate).toISOString() : new Date().toISOString(),
    category: expenseType, 
    amount: amt,
    payment_method: paymentMethod || 'Cash',
    account_detail: accountDetail || null,
    tid: tid || null,
    description: notes || '', 
    head: head || null,
    distributor_id: expenseType === 'Distributor' ? distributorId : null,
    person_id: personId || null,
    salesman_id: null,
    status: 'Pending'
  };
  const {data, error} = await supabase.from('expenses').insert(payload).select().single();
  if(error) {
    if (error.code === '23502' && error.message.includes('salesman_id')) {
      throw new Error("SCHEMA ERROR: Cannot save expense because the database still requires a salesman. Please run phase2_person_payments.sql in Supabase: ALTER TABLE expenses ALTER COLUMN salesman_id DROP NOT NULL;");
    }
    throw error;
  }
  return data;
}

export async function updateExpenseStatus(id, status) {
  // Guard against mutating expenses created atomically from person ledger
  const { data: existing, error: fetchErr } = await supabase
    .from('expenses')
    .select('id, status, originating_ledger_entry_id, reference_number')
    .eq('id', id)
    .single();

  if (fetchErr) throw fetchErr;

  if (existing?.originating_ledger_entry_id) {
    throw new Error(`Expense ${existing.reference_number} was automatically generated from Person Payments. Please approve or cancel via the Person Payments ledger to maintain financial integrity.`);
  }

  const {error}=await supabase.from('expenses').update({status, updated_at: new Date().toISOString()}).eq('id',id);
  if(error) throw error;
}

export async function fetchExpenseSummary() {
  const monthStart=new Date();monthStart.setDate(1);monthStart.setHours(0,0,0,0);
  const {data, error}=await supabase.from('expenses').select('amount,status,category,head').gte('expense_date',monthStart.toISOString());
  if(error) throw error;

  let total = 0; // ONLY Approved & Posted
  let pendingTotal = 0;
  let distributor = 0;
  let company = 0;
  let office = 0;
  let advertisement = 0;
  let welfare = 0;
  let others = 0;
  
  (data||[]).forEach(r => {
    const amt = Number(r.amount) || 0;
    if (['Approved', 'Posted'].includes(r.status)) {
      total += amt;
      if (r.category === 'Distributor') distributor += amt;
      else if (r.category === 'Company') company += amt;
      else if (r.category === 'Office') office += amt;
      else if (r.category === 'Advertisement' || r.head === 'Advertisement') advertisement += amt;
      else if (r.category === 'Welfare' || r.head === 'Welfare') welfare += amt;
      else others += amt;
    } else if (['Pending', 'Submitted'].includes(r.status)) {
      pendingTotal += amt;
    }
  });
  
  return {total, approvedTotal: total, pendingTotal, distributor, company, office, advertisement, welfare, others};
}

// --- CUSTOMERS ----------------------------------------------------------------
export async function fetchCustomers() {
  const {data,error}=await supabase.from('customers').select('*, salesmen(profiles(full_name))').order('name');
  if(error) throw error;
  const {data:ledger}=await supabase.from('customer_ledger').select('*');
  const lm={};
  (ledger||[]).forEach(l=>{lm[l.customer_id]=l.outstanding_balance;});
  return (data||[]).map(c=>({...c,outstanding:lm[c.id]||0}));
}

export async function addCustomer({code,name,phone,address,default_salesman_id}) {
  const {error}=await supabase.from('customers').insert({code,name,phone,address,default_salesman_id:default_salesman_id||null});
  if(error) throw error;
}

export async function fetchCustomerReturns() {
  const {data,error}=await supabase.from('inventory_transactions').select('*, customers(name), salesmen(profiles(full_name)), product_packaging(name)').in('transaction_type',['Customer_Good_Return','Customer_Damaged_Return']).order('transaction_date',{ascending:false}).limit(50);
  if(error) throw error;
  return data||[];
}

// --- PRODUCTS -----------------------------------------------------------------
export async function fetchProducts() {
  const {data,error}=await supabase.from('products').select('*, product_packaging(*, product_prices(*))').order('name');
  if(error) throw error;
  return data||[];
}

export async function fetchProductMovement() {
  const {data,error}=await supabase.from('inventory_transactions').select('transaction_type,quantity').in('status',['Approved','Posted']);
  if(error) throw error;
  const s={production:0,salesman_issues:0,salesman_returns:0,customer_returns:0,damaged:0,adjustments:0};
  (data||[]).forEach(r=>{
    const qty = Number(r.quantity) || 0;
    if(['Production','Purchase'].includes(r.transaction_type)) s.production += qty;
    // Stock issued — both legacy salesman and current distributor
    if(['Salesman_Issue','Distributor_Issue'].includes(r.transaction_type)) s.salesman_issues += qty;
    // Good returns only (restocked into company saleable stock upon approval)
    if(['Salesman_Good_Return','Distributor_Good_Return'].includes(r.transaction_type)) s.salesman_returns += qty;
    // Legacy customer returns (good condition)
    if(r.transaction_type === 'Customer_Good_Return') s.customer_returns += qty;
    // Damaged returns and damaged stock (isolated in quarantine, NEVER counted as saleable)
    if(['Salesman_Damaged_Return','Distributor_Damaged_Return','Customer_Damaged_Return','Damage','Expiry'].includes(r.transaction_type)) {
      s.damaged += qty;
    }
    if(r.transaction_type === 'Adjustment') s.adjustments += qty;
  });
  // Saleable closing stock: Damaged stock is segregated and NEVER counted as saleable
  s.closing = s.production - s.salesman_issues + s.salesman_returns + s.customer_returns + s.adjustments;
  return s;
}

export async function fetchPackagings() {
  const {data,error}=await supabase.from('product_packaging').select('*, products(name), product_prices(unit_cost, sales_price)').order('name');
  if(error) throw error;
  return data||[];
}

// --- SETTLEMENT ---------------------------------------------------------------
export async function fetchSalesmanSettlement(salesmanId) {
  const {data:sales}=await supabase.from('sales_orders').select('total_amount').eq('salesman_id',salesmanId).in('status',['Approved','Posted']);
  const {data:recs}=await supabase.from('recoveries').select('amount').eq('salesman_id',salesmanId).in('status',['Approved','Posted']);
  const {data:exps}=await supabase.from('expenses').select('amount,paid_by').eq('salesman_id',salesmanId).eq('status','Approved');
  const netSales=(sales||[]).reduce((s,r)=>s+Number(r.total_amount),0);
  const recovery=(recs||[]).reduce((s,r)=>s+Number(r.amount),0);
  const reimbursable=(exps||[]).filter(e=>e.paid_by==='Salesman').reduce((s,r)=>s+Number(r.amount),0);
  const outstanding=Math.max(0,netSales-recovery);
  const net=outstanding-reimbursable;
  return {netSales,recovery,outstanding,reimbursable,net};
}

// --- AUDIT --------------------------------------------------------------------
export async function fetchAuditLogs(limit=100) {
  const {data,error}=await supabase.from('audit_logs').select('*, profiles(full_name)').order('created_at',{ascending:false}).limit(limit);
  if(error) throw error;
  return data||[];
}

// --- Staff Management ---
export async function invokeCreateUser(payload) {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error('Not logged in');

  const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/create-user`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Failed to create user');
  return data;
}

// --- STAGE 5: REPORTS & CLOSING ---

export async function closeTodayLedger({ closingDate = new Date().toISOString().split('T')[0] } = {}) {
  const [{ data: salesmen }, { data: distributors }] = await Promise.all([
    supabase.from('salesmen').select('id, code, profiles(full_name)'),
    supabase.from('distributors').select('id, code, name').eq('is_active', true)
  ]);

  const results = [];
  const startOfDay = `${closingDate}T00:00:00.000Z`;
  const endOfDay = `${closingDate}T23:59:59.999Z`;

  // 1. Process Distributors
  for (const dist of (distributors || [])) {
    const { data: ts } = await supabase.from('sales_orders')
      .select('total_amount')
      .eq('distributor_id', dist.id)
      .in('status', ['Approved', 'Posted'])
      .gte('sale_date', startOfDay)
      .lte('sale_date', endOfDay);
    const salesAmt = (ts || []).reduce((s, r) => s + Number(r.total_amount), 0);

    const { data: tr } = await supabase.from('recoveries')
      .select('amount')
      .eq('distributor_id', dist.id)
      .in('status', ['Approved', 'Posted'])
      .gte('recovery_date', startOfDay)
      .lte('recovery_date', endOfDay);
    const recAmt = (tr || []).reduce((s, r) => s + Number(r.amount), 0);

    const { data: stockRows } = await supabase.from('inventory_transactions')
      .select('quantity, transaction_type')
      .eq('distributor_id', dist.id)
      .in('status', ['Approved', 'Posted'])
      .lte('transaction_date', endOfDay);
    let distStock = 0;
    (stockRows || []).forEach(r => {
      if (r.transaction_type === 'Distributor_Issue') distStock += Number(r.quantity || 0);
      if (['Distributor_Good_Return', 'Distributor_Damaged_Return', 'Salesman_Good_Return', 'Salesman_Damaged_Return'].includes(r.transaction_type)) {
        distStock -= Number(r.quantity || 0);
      }
    });

    // Daily closing initial tally: expected is calculated from transactions, submitted is unset, status is Pending
    const { data: closing, error: cErr } = await supabase.from('daily_closings').upsert({
      closing_date: closingDate,
      distributor_id: dist.id,
      salesman_id: null,
      expected_cash: recAmt,
      submitted_cash: null,
      expected_stock: { packets: distStock, sales: salesAmt },
      submitted_stock: null,
      status: 'Pending'
    }, { onConflict: 'closing_date,distributor_id' }).select().single();

    if (cErr) console.warn('Distributor closing notice for ' + dist.code, cErr);
    else results.push(closing);
  }

  // 2. Process Historical Salesmen (if present)
  for (const sm of (salesmen || [])) {
    const { data: ts } = await supabase.from('sales_orders')
      .select('total_amount')
      .eq('salesman_id', sm.id)
      .in('status', ['Approved', 'Posted'])
      .gte('sale_date', startOfDay)
      .lte('sale_date', endOfDay);
    const salesAmt = (ts || []).reduce((s, r) => s + Number(r.total_amount), 0);

    const { data: tr } = await supabase.from('recoveries')
      .select('amount')
      .eq('salesman_id', sm.id)
      .in('status', ['Approved', 'Posted'])
      .gte('recovery_date', startOfDay)
      .lte('recovery_date', endOfDay);
    const recAmt = (tr || []).reduce((s, r) => s + Number(r.amount), 0);

    const { data: stockRows } = await supabase.from('inventory_transactions')
      .select('quantity, transaction_type')
      .eq('salesman_id', sm.id)
      .in('status', ['Approved', 'Posted'])
      .lte('transaction_date', endOfDay);
    let currentStock = 0;
    (stockRows || []).forEach(r => {
      if (r.transaction_type === 'Salesman_Issue') currentStock += Number(r.quantity || 0);
      if (['Sale', 'Salesman_Good_Return', 'Salesman_Damaged_Return'].includes(r.transaction_type)) {
        currentStock -= Number(r.quantity || 0);
      }
    });

    const { data: closing, error: cErr } = await supabase.from('daily_closings').upsert({
      closing_date: closingDate,
      salesman_id: sm.id,
      expected_cash: recAmt,
      submitted_cash: null,
      expected_stock: { packets: currentStock, sales: salesAmt },
      submitted_stock: null,
      status: 'Pending'
    }, { onConflict: 'closing_date,salesman_id' }).select().single();

    if (cErr) console.warn('Closing notice for ' + sm.code, cErr);
    else results.push(closing);
  }

  return { success: true, count: results.length };
}

export async function reconcileDailyClosing({ closingId, submittedCash, submittedStockPackets, notes = '' }) {
  const { data: closing, error: fetchErr } = await supabase
    .from('daily_closings')
    .select('*')
    .eq('id', closingId)
    .single();

  if (fetchErr) throw fetchErr;

  const numSubmittedCash = Number(submittedCash) || 0;
  const numExpectedCash = Number(closing.expected_cash) || 0;
  const cashVariance = numSubmittedCash - numExpectedCash;

  const expectedStockPackets = typeof closing.expected_stock === 'object' && closing.expected_stock !== null
    ? Number(closing.expected_stock.packets || 0)
    : Number(closing.expected_stock || 0);
  const numSubmittedStock = Number(submittedStockPackets) || 0;
  const stockVariance = numSubmittedStock - expectedStockPackets;

  const hasVariance = cashVariance !== 0 || stockVariance !== 0;

  // Record variance in variances table if discrepancy exists
  if (hasVariance) {
    try {
      await supabase.from('variances').insert({
        closing_id: closingId,
        salesman_id: closing.salesman_id,
        distributor_id: closing.distributor_id,
        cash_variance: cashVariance,
        stock_variance: stockVariance,
        notes: notes || 'Variance recorded during daily closing reconciliation',
        status: 'Pending'
      });
    } catch (vErr) {
      console.warn('Variance recording notice:', vErr.message);
    }
  }

  const { data, error } = await supabase
    .from('daily_closings')
    .update({
      submitted_cash: numSubmittedCash,
      submitted_stock: { packets: numSubmittedStock, expected_sales: closing.expected_stock?.sales || 0 },
      notes: notes || closing.notes || '',
      status: hasVariance ? 'Variance_Flagged' : 'Pending_Approval'
    })
    .eq('id', closingId)
    .select()
    .single();

  if (error) throw error;
  return data;
}

export async function approveDailyClosing(closingId) {
  const { data: { session } } = await supabase.auth.getSession();
  const userId = session?.user?.id || null;

  const { data, error } = await supabase
    .from('daily_closings')
    .update({
      status: 'Approved',
      approved_by: userId,
      approved_at: new Date().toISOString()
    })
    .eq('id', closingId)
    .select()
    .single();

  if (error) throw error;
  return data;
}


export async function fetchDailyClosingReport(filters = {}) {
  let q = supabase.from('daily_closings').select('*, salesmen(code, route, profiles(full_name)), distributors(code, name)').order('closing_date', { ascending: false });
  if (filters.startDate) q = q.gte('closing_date', filters.startDate);
  if (filters.endDate) q = q.lte('closing_date', filters.endDate);
  if (filters.salesmanId) q = q.eq('salesman_id', filters.salesmanId);
  if (filters.distributorId) q = q.eq('distributor_id', filters.distributorId);
  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

export async function fetchProfitabilityReport(filters = {}) {
  let sq = supabase.from('sales_orders').select('sale_date, total_amount, sale_items(quantity, unit_price, product_packaging(product_prices(unit_cost)))').in('status', ['Approved', 'Posted']);
  let eq = supabase.from('expenses').select('amount, expense_date').eq('status', 'Approved');

  if (filters.startDate) {
    sq = sq.gte('sale_date', filters.startDate);
    eq = eq.gte('expense_date', filters.startDate);
  }
  if (filters.endDate) {
    sq = sq.lte('sale_date', filters.endDate);
    eq = eq.lte('expense_date', filters.endDate);
  }

  const [{ data: sales }, { data: expenses }] = await Promise.all([sq, eq]);

  let revenue = 0;
  let cogs = 0;

  (sales || []).forEach(order => {
    revenue += Number(order.total_amount || 0);
    (order.sale_items || []).forEach(item => {
      const cost = item.product_packaging?.product_prices?.[0]?.unit_cost || 0;
      cogs += Number(item.quantity || 0) * Number(cost);
    });
  });

  const totalExpenses = (expenses || []).reduce((s, e) => s + Number(e.amount || 0), 0);
  const grossProfit = revenue - cogs;
  const netProfit = grossProfit - totalExpenses;
  const marginPct = revenue > 0 ? ((netProfit / revenue) * 100).toFixed(1) : 0;

  return {
    revenue,
    cogs,
    grossProfit,
    expenses: totalExpenses,
    netProfit,
    marginPct,
    salesCount: (sales || []).length,
    expensesCount: (expenses || []).length
  };
}

export async function fetchVarianceReport(filters = {}) {
  let q = supabase.from('variances').select('*, daily_closings(closing_date, salesmen(code, profiles(full_name)))').order('created_at', { ascending: false });
  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

export async function approveSettlement(salesmanId) {
  const { data: { session } } = await supabase.auth.getSession();
  const userId = session?.user?.id || null;
  const { error } = await supabase.from('audit_logs').insert({
    table_name: 'settlement',
    record_id: salesmanId,
    action: 'APPROVE_SETTLEMENT',
    new_data: { salesman_id: salesmanId, approved_at: new Date().toISOString() },
    performed_by: userId
  });
  if (error) console.warn('Settlement audit error:', error);
  return { success: true };
}

export async function submitSale({ salesmanId, customerId, distributorId, items, totalAmount }) {
  if (!distributorId) throw new Error('Distributor is required for sale creation.');
  if (!items || items.length === 0) throw new Error('At least one sale item is required.');

  const ref = refNum('SAL');

  // Attempt atomic creation via SECURITY DEFINER RPC (Phase 2 migration required)
  try {
    const { data: rpcRes, error: rpcErr } = await supabase.rpc('create_sales_order_with_items', {
      p_reference_number: ref,
      p_distributor_id: distributorId,
      p_salesman_id: salesmanId || null,
      p_customer_id: customerId || null,
      p_total_amount: Number(totalAmount) || 0,
      p_sale_date: new Date().toISOString(),
      p_status: 'Approved',
      p_items: items.map(item => ({
        packagingId: item.packagingId,
        quantity: Number(item.quantity) || 0,
        price: Number(item.price) || 0,
        subtotal: (Number(item.quantity) || 0) * (Number(item.price) || 0)
      }))
    });

    if (!rpcErr && rpcRes) return rpcRes;
    if (rpcErr && rpcErr.code !== 'PGRST202') throw rpcErr;
  } catch (err) {
    if (err.code !== 'PGRST202') throw err;
  }

  // Fallback if RPC is not deployed: snapshot distributor rates and insert atomically into tables
  const { data: distData } = await supabase.from('distributors').select('commission').eq('id', distributorId).maybeSingle();
  const commSnapshot = distData?.commission != null ? Number(distData.commission) : 30;

  const { data: order, error: orderErr } = await supabase.from('sales_orders').insert({
    reference_number: ref,
    salesman_id: salesmanId || null,
    customer_id: customerId || null,
    distributor_id: distributorId,
    total_amount: Number(totalAmount) || 0,
    commission_rate_snapshot: commSnapshot,
    advertisement_rate_snapshot: 20,
    welfare_rate_snapshot: 10,
    sale_date: new Date().toISOString(),
    status: 'Approved'
  }).select().single();
  
  if (orderErr) throw orderErr;

  const saleItems = items.map(item => ({
    sale_order_id: order.id,
    packaging_id: item.packagingId,
    quantity: Number(item.quantity) || 0,
    unit_price: Number(item.price) || 0,
    subtotal: (Number(item.quantity) || 0) * (Number(item.price) || 0)
  }));

  const { error: itemsErr } = await supabase.from('sale_items').insert(saleItems);
  if (itemsErr) throw itemsErr;
  
  return order;
}

export async function addProduct({ name, code, packagingName, unitCost, salesPrice }) {
  // 1. Insert/find product
  let productId;
  const { data: existingProduct } = await supabase.from("products")
    .select("id").eq("code", code).maybeSingle();

  if (existingProduct) {
    productId = existingProduct.id;
  } else {
    const { data: newProd, error: prodErr } = await supabase.from("products")
      .insert({ name: name.trim(), code: code.trim() }).select("id").single();
    if (prodErr) throw prodErr;
    productId = newProd.id;
  }

  // 2. Insert product_packaging (variant/packaging)
  const { data: pkg, error: pkgErr } = await supabase.from("product_packaging")
    .insert({ product_id: productId, name: packagingName.trim() }).select("id").single();
  if (pkgErr) throw pkgErr;

  // 3. Insert product_prices
  const { error: priceErr } = await supabase.from("product_prices")
    .insert({ packaging_id: pkg.id, unit_cost: Number(unitCost), sales_price: Number(salesPrice) });
  if (priceErr) throw priceErr;

  return pkg;
}

export async function updateProduct({ pkgId, productId, priceId, name, code, packagingName, unitCost, salesPrice }) {
  const { error: e1 } = await supabase.from('products').update({ name, code }).eq('id', productId);
  if (e1) throw e1;
  
  const { error: e2 } = await supabase.from('product_packaging').update({ name: packagingName }).eq('id', pkgId);
  if (e2) throw e2;
  
  if (priceId) {
    const { error: e3 } = await supabase.from('product_prices').update({ unit_cost: Number(unitCost), sales_price: Number(salesPrice) }).eq('id', priceId);
    if (e3) throw e3;
  } else {
    const { error: e4 } = await supabase.from('product_prices').insert({
      packaging_id: pkgId,
      unit_cost: Number(unitCost),
      sales_price: Number(salesPrice)
    });
    if (e4) throw e4;
  }
  return true;
}

export async function deleteProduct(pkgId, productId) {
  // Try deleting the packaging variant first
  const { error: e1 } = await supabase.from('product_packaging').delete().eq('id', pkgId);
  if (e1) {
    if (e1.code === '23503') throw new Error('Cannot delete: Product is being used in transactions.');
    throw e1;
  }
  
  // Clean up parent product if no variants left
  const { count } = await supabase.from('product_packaging').select('id', { count: 'exact', head: true }).eq('product_id', productId);
  if (count === 0) {
    await supabase.from('products').delete().eq('id', productId);
  }
  return true;
}


export async function submitBooking({ salesmanId, customerId, distributorId, items, totalAmount }) {
  const ref = refNum('BKG');

  // Attempt atomic creation RPC first
  try {
    const { data: rpcRes, error: rpcErr } = await supabase.rpc('create_sales_order_with_items', {
      p_reference_number: ref,
      p_distributor_id: distributorId || null,
      p_salesman_id: salesmanId || null,
      p_customer_id: customerId || null,
      p_total_amount: Number(totalAmount) || 0,
      p_sale_date: new Date().toISOString(),
      p_status: 'Pending',
      p_items: (items || []).map(item => ({
        packagingId: item.packagingId,
        quantity: Number(item.quantity) || 0,
        price: Number(item.price) || 0,
        subtotal: (Number(item.quantity) || 0) * (Number(item.price) || 0)
      }))
    });

    if (!rpcErr && rpcRes) {
      return rpcRes;
    }
    if (rpcErr && rpcErr.code !== 'PGRST202') {
      throw rpcErr;
    }
  } catch (err) {
    if (err.code !== 'PGRST202') throw err;
  }

  // Fallback for non-migrated environment:
  const { data: order, error: orderErr } = await supabase.from('sales_orders').insert({
    reference_number: ref,
    salesman_id: salesmanId || null,
    customer_id: customerId || null,
    distributor_id: distributorId || null,
    total_amount: totalAmount,
    sale_date: new Date().toISOString(),
    status: 'Pending'
  }).select().single();
  
  if (orderErr) throw orderErr;

  const saleItems = items.map(item => ({
    sale_order_id: order.id,
    packaging_id: item.packagingId,
    quantity: item.quantity,
    unit_price: item.price,
    subtotal: item.quantity * item.price
  }));

  const { error: itemsErr } = await supabase.from('sale_items').insert(saleItems);
  if (itemsErr) throw itemsErr;
  
  return order;
}

export async function fetchBookings({ dateFrom, dateTo, distributorId } = {}) {
  let q = supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, status, customer_id, salesman_id, distributor_id, customers(name), salesmen(profiles(full_name)), distributors(id, code, name, id_card, phone), sale_items(*, product_packaging(name, products(name)))')
    .like('reference_number', 'BKG-%')
    .order('sale_date', { ascending: false });
  if (dateFrom) q = q.gte('sale_date', dateFrom);
  if (dateTo) q = q.lte('sale_date', dateTo);
  if (distributorId) q = q.eq('distributor_id', distributorId);
  const { data, error } = await q;
  if (error) throw error;

  // Stable sequential numbering across all bookings chronologically
  const { data: allBookings } = await supabase
    .from('sales_orders')
    .select('id, sale_date')
    .like('reference_number', 'BKG-%')
    .order('sale_date', { ascending: true });

  const sortedBookings = (allBookings || []).slice().sort((a, b) => {
    const tA = new Date(a.sale_date).getTime() || 0;
    const tB = new Date(b.sale_date).getTime() || 0;
    if (tA !== tB) return tA - tB;
    return String(a.id).localeCompare(String(b.id));
  });

  const seqMap = new Map();
  sortedBookings.forEach((b, idx) => {
    seqMap.set(b.id, idx + 1);
  });

  const { data: recs, error: rErr } = await supabase
    .from('recoveries')
    .select('amount, reference_number')
    .like('reference_number', '%|%');
    
  if (rErr) throw rErr;

  return (data || []).map(b => {
    const bookingRecs = (recs || []).filter(r => 
      r.reference_number && (
        r.reference_number.endsWith('|' + b.id) || 
        (b.reference_number && r.reference_number.endsWith('|' + b.reference_number))
      )
    );
    const totalRecovered = bookingRecs.reduce((sum, r) => sum + Number(r.amount), 0);
    const seq = seqMap.get(b.id) || 1;
    return {
      ...b,
      sequential_no: seq,
      formattedBillNo: String(seq).padStart(2, '0'),
      total_recovered: totalRecovered,
      remaining_balance: Math.max(0, Number(b.total_amount) - totalRecovered)
    };
  });
}

export async function addBookingRecovery({ bookingId, bookingRef, customerId, salesmanId, distributorId, amount, paymentMethod }) {
  const identifier = bookingRef || bookingId;
  const ref = refNum('REC') + '|' + identifier;
  const payload = {
    reference_number: ref,
    amount: Number(amount),
    payment_method: paymentMethod || 'Cash',
    recovery_date: new Date().toISOString(),
    status: 'Approved',
    notes: `Advance payment on booking ${identifier}`
  };
  if (distributorId) payload.distributor_id = distributorId;
  if (salesmanId) payload.salesman_id = salesmanId;
  if (customerId) payload.customer_id = customerId;

  const { data, error } = await supabase.from('recoveries').insert(payload).select().single();
  if (error) throw error;
  return data;
}

export async function addDistributorRecovery({ distributorId, amount, paymentMethod = 'Cash', recoveryDate, notes }) {
  if (!distributorId) throw new Error('Distributor is required for recovery.');
  const amt = Number(amount);
  if (!amt || amt <= 0) throw new Error('Recovery amount must be greater than zero.');

  const ref = refNum('REC');
  const payload = {
    reference_number: ref,
    distributor_id: distributorId,
    amount: amt,
    payment_method: paymentMethod || 'Cash',
    recovery_date: recoveryDate ? new Date(recoveryDate).toISOString() : new Date().toISOString(),
    status: 'Approved',
    notes: notes || ''
  };
  const { data, error } = await supabase.from('recoveries').insert(payload).select().single();
  if (error) throw error;
  return data;
}

export async function fetchRecoveries({ dateFrom, dateTo, distributorId, status, limit = 200 } = {}) {
  let directQ = supabase
    .from('recoveries')
    .select('*, distributors(id, name, code, phone), salesmen(profiles(full_name)), customers(name)')
    .order('recovery_date', { ascending: false })
    .limit(limit);
  if (distributorId) directQ = directQ.eq('distributor_id', distributorId);
  if (status && status !== 'All') directQ = directQ.eq('status', status);
  if (dateFrom) directQ = directQ.gte('recovery_date', dateFrom);
  if (dateTo) directQ = directQ.lte('recovery_date', dateTo);

  let unassignedQ = null;
  if (distributorId) {
    unassignedQ = supabase
      .from('recoveries')
      .select('*, distributors(id, name, code, phone), salesmen(profiles(full_name)), customers(name)')
      .is('distributor_id', null)
      .like('reference_number', '%|%')
      .order('recovery_date', { ascending: false })
      .limit(limit);
    if (status && status !== 'All') unassignedQ = unassignedQ.eq('status', status);
    if (dateFrom) unassignedQ = unassignedQ.gte('recovery_date', dateFrom);
    if (dateTo) unassignedQ = unassignedQ.lte('recovery_date', dateTo);
  }

  const [directRes, unassignedRes] = await Promise.all([
    directQ,
    unassignedQ ? unassignedQ : Promise.resolve({ data: [] })
  ]);
  if (directRes.error) throw directRes.error;
  if (unassignedRes && unassignedRes.error) throw unassignedRes.error;

  const rawList = [...(directRes.data || []), ...(unassignedRes?.data || [])];
  const uuidSet = new Set();
  const refSet = new Set();

  rawList.forEach(r => {
    if (r.reference_number && r.reference_number.includes('|')) {
      const target = r.reference_number.split('|')[1]?.trim();
      if (target) {
        if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(target)) {
          uuidSet.add(target);
        } else {
          refSet.add(target);
        }
      }
    }
  });

  const orderById = new Map();
  const orderByRef = new Map();

  const fetchPromises = [];
  if (uuidSet.size > 0) {
    fetchPromises.push(
      supabase
        .from('sales_orders')
        .select('id, reference_number, distributor_id, distributors(id, name, code, phone)')
        .in('id', Array.from(uuidSet))
        .then(res => {
          (res.data || []).forEach(o => {
            orderById.set(o.id, o);
            if (o.reference_number) orderByRef.set(o.reference_number, o);
          });
        })
    );
  }
  if (refSet.size > 0) {
    fetchPromises.push(
      supabase
        .from('sales_orders')
        .select('id, reference_number, distributor_id, distributors(id, name, code, phone)')
        .in('reference_number', Array.from(refSet))
        .then(res => {
          (res.data || []).forEach(o => {
            orderById.set(o.id, o);
            if (o.reference_number) orderByRef.set(o.reference_number, o);
          });
        })
    );
  }

  if (fetchPromises.length > 0) {
    try {
      await Promise.all(fetchPromises);
    } catch (lookupErr) {
      console.warn('Could not resolve linked orders in fetchRecoveries:', lookupErr);
    }
  }

  const mapped = [];
  const seenIds = new Set();

  rawList.forEach(r => {
    if (seenIds.has(r.id)) return;
    seenIds.add(r.id);

    if (r.reference_number && r.reference_number.includes('|')) {
      const parts = r.reference_number.split('|');
      const cleanRef = parts[0];
      const target = parts[1]?.trim() || '';
      const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(target);
      let linkedRef = null;
      let linkedDist = null;

      if (orderById.has(target)) {
        const ord = orderById.get(target);
        linkedRef = ord.reference_number;
        linkedDist = ord.distributors;
      } else if (orderByRef.has(target)) {
        const ord = orderByRef.get(target);
        linkedRef = ord.reference_number;
        linkedDist = ord.distributors;
      } else if (!isUuid && target) {
        linkedRef = target;
      }

      // If filtering by distributor, verify that this unassigned recovery's order belongs to distributorId
      if (distributorId && !r.distributor_id) {
        const orderDistId = linkedDist?.id || (orderById.get(target)?.distributor_id) || (orderByRef.get(target)?.distributor_id);
        if (orderDistId !== distributorId) {
          return; // Exclude unassigned recovery linked to a different distributor
        }
      }

      mapped.push({
        ...r,
        clean_recovery_ref: cleanRef,
        raw_linked_id: target,
        linked_order_ref: linkedRef,
        booking_distributor: linkedDist || null,
        distributors: r.distributors || linkedDist || null,
        is_linked_uuid: isUuid
      });
    } else {
      mapped.push({
        ...r,
        clean_recovery_ref: r.reference_number,
        raw_linked_id: null,
        linked_order_ref: null,
        booking_distributor: null,
        is_linked_uuid: false
      });
    }
  });

  return mapped;
}


// ── Distributors ─────────────────────────────────────────────────────────────
export async function fetchDistributors() {
  const { data, error } = await supabase.from('distributors').select('*').order('created_at', { ascending: false });
  if (error) throw error;
  return data;
}

export async function addDistributor({ code, name, id_card, phone, commission, is_active }) {
  const { data, error } = await supabase.from('distributors').insert({
    code, name, id_card: id_card || null, phone, commission: Number(commission), is_active
  }).select().single();
  if (error) throw error;
  return data;
}

export async function updateDistributor(id, { code, name, id_card, phone, commission, is_active }) {
  const { data, error } = await supabase.from('distributors').update({
    code, name, id_card: id_card || null, phone, commission: Number(commission), is_active, updated_at: new Date().toISOString()
  }).eq('id', id).select().single();
  if (error) throw error;
  return data;
}

export async function deleteDistributor(id) {
  const { error } = await supabase.from('distributors').delete().eq('id', id);
  if (error) throw error;
}


// ── Sales (SAL- records) with distributor + filters ──────────────────────────
export async function fetchSales({ dateFrom, dateTo, distributorId } = {}) {
  let q = supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, status, customer_id, salesman_id, distributor_id, customers(name, code), salesmen(profiles(full_name)), distributors(id, code, name, id_card, phone), sale_items(quantity, unit_price, subtotal)')
    .like('reference_number', 'SAL-%')
    .order('sale_date', { ascending: false });
  if (dateFrom) q = q.gte('sale_date', dateFrom);
  if (dateTo)   q = q.lte('sale_date', dateTo);
  if (distributorId) q = q.eq('distributor_id', distributorId);
  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

// ── Shared Distributor Recoveries Resolution Helper ────────────────────────
/**
 * Resolves all recoveries attributed to a specific distributor.
 *
 * Attribution Rules:
 * 1. Direct recoveries: recovery record has `distributor_id === distributorId`.
 * 2. Linked recoveries: recovery record has `distributor_id IS NULL`, reference contains `|<target>`,
 *    and `<target>` matches the id (UUID) or reference_number (BKG-*, SAL-*) of an order belonging to `distributorId`.
 * 3. Strict Safety: Never guesses attribution for unlinked or ambiguous records.
 * 4. Deduplication: Keyed by recovery `id` to guarantee zero double counting.
 */
export async function fetchDistributorApprovedRecoveries(distributorId, options = {}) {
  if (!distributorId) return [];
  const { approvedOnly = true, dateFrom = null, dateTo = null } = options;

  // 1. Direct recoveries query
  let directQ = supabase
    .from('recoveries')
    .select('id, reference_number, recovery_date, amount, payment_method, status, notes, distributor_id')
    .eq('distributor_id', distributorId)
    .limit(5000);

  if (approvedOnly) directQ = directQ.in('status', ['Approved', 'Posted']);
  if (dateFrom) directQ = directQ.gte('recovery_date', dateFrom);
  if (dateTo) directQ = directQ.lte('recovery_date', dateTo);

  // 2. Unassigned recoveries query
  let unassignedQ = supabase
    .from('recoveries')
    .select('id, reference_number, recovery_date, amount, payment_method, status, notes, distributor_id')
    .is('distributor_id', null)
    .like('reference_number', '%|%')
    .limit(5000);

  if (approvedOnly) unassignedQ = unassignedQ.in('status', ['Approved', 'Posted']);
  if (dateFrom) unassignedQ = unassignedQ.gte('recovery_date', dateFrom);
  if (dateTo) unassignedQ = unassignedQ.lte('recovery_date', dateTo);

  // 3. Distributor's verified orders
  const distOrdersQ = supabase
    .from('sales_orders')
    .select('id, reference_number')
    .eq('distributor_id', distributorId)
    .limit(5000);

  const [directRes, unassignedRes, distOrdersRes] = await Promise.all([
    directQ,
    unassignedQ,
    distOrdersQ
  ]);

  if (directRes.error) throw directRes.error;
  if (unassignedRes.error) throw unassignedRes.error;
  if (distOrdersRes.error) throw distOrdersRes.error;

  const validOrderIds = new Set((distOrdersRes.data || []).map(o => o.id));
  const validOrderRefs = new Set((distOrdersRes.data || []).map(o => o.reference_number).filter(Boolean));

  const recoveryMap = new Map();

  // Add direct recoveries
  (directRes.data || []).forEach(r => {
    recoveryMap.set(r.id, r);
  });

  // Add verified linked recoveries where direct distributor_id is NULL
  (unassignedRes.data || []).forEach(r => {
    if (r.reference_number && r.reference_number.includes('|')) {
      const target = r.reference_number.split('|')[1]?.trim();
      if (target && (validOrderIds.has(target) || validOrderRefs.has(target))) {
        if (!recoveryMap.has(r.id)) {
          recoveryMap.set(r.id, {
            ...r,
            is_linked_attribution: true
          });
        }
      }
    }
  });

  return Array.from(recoveryMap.values());
}

// ── Distributor Outstanding ───────────────────────────────────────────────────
export async function fetchDistributorOutstanding(distributorId) {
  if (!distributorId) return { 
    totalSales: 0, 
    totalRecoveries: 0, 
    totalSettlementAdjustments: 0,
    totalCredits: 0,
    totalPackets: 0, 
    netBalance: 0,
    outstanding: 0, 
    advanceBalance: 0,
    salesOutstanding: 0, 
    accruedCommission: 0, 
    settledCommission: 0, 
    commissionPayable: 0,
    hasUnreconciledRates: false,
    unreconciledCount: 0,
    unreconciledPackets: 0,
    defaultCommissionRate: 0,
    estimatedUnreconciledCommission: 0,
    pendingBookingsCount: 0,
    pendingBookingsAmount: 0,
    pendingBookingsPackets: 0
  };

  const [distRes, salesRes, allRecoveries, saleItemsRes, settlementsRes, pendingBookingsRes] = await Promise.all([
    supabase.from('distributors').select('id, name, code, commission').eq('id', distributorId).maybeSingle(),
    supabase.from('sales_orders')
      .select('id, reference_number, total_amount, commission_rate_snapshot')
      .eq('distributor_id', distributorId)
      .in('status', ['Approved', 'Posted'])
      .not('reference_number', 'like', 'BKG-%') // Exclude all bookings from approved sales!
      .limit(5000),
    fetchDistributorApprovedRecoveries(distributorId, { approvedOnly: true }),
    supabase.from('sale_items')
      .select('quantity, sales_orders!inner(id, reference_number, distributor_id, status, commission_rate_snapshot)')
      .filter('sales_orders.distributor_id', 'eq', distributorId)
      .filter('sales_orders.status', 'in', '("Approved","Posted")')
      .not('sales_orders.reference_number', 'like', 'BKG-%') // Exclude all bookings from delivered packet count!
      .limit(10000),
    supabase.from('distributor_settlements')
      .select('id, amount, settlement_type, recovery_id, reference_number')
      .eq('distributor_id', distributorId)
      .in('status', ['Approved'])
      .limit(5000),
    supabase.from('sales_orders')
      .select('id, reference_number, total_amount, sale_items(quantity)')
      .eq('distributor_id', distributorId)
      .eq('status', 'Pending')
      .like('reference_number', 'BKG-%')
      .limit(5000)
  ]);

  if (salesRes.error) throw salesRes.error;
  if (saleItemsRes.error) throw saleItemsRes.error;
  if (settlementsRes.error) throw settlementsRes.error;
  if (pendingBookingsRes.error) throw pendingBookingsRes.error;

  const totalSales = (salesRes.data || []).reduce((s, r) => s + Number(r.total_amount), 0);
  const totalPackets = (saleItemsRes.data || []).reduce((s, r) => s + Number(r.quantity), 0);

  // Include all approved recoveries from distributor (including booking advance recoveries)
  const totalRecoveries = allRecoveries.reduce((s, r) => s + Number(r.amount), 0);

  // Accounting: Check for Commission_Against_Outstanding settlements that have NOT already created a separate recovery
  const unlinkedSettlementAdjustments = (settlementsRes.data || [])
    .filter(s => s.settlement_type === 'Commission_Against_Outstanding')
    .filter(s => !s.recovery_id && !allRecoveries.some(r => r.id === s.recovery_id || (r.reference_number && r.reference_number.includes(s.reference_number))));
  
  const totalSettlementAdjustments = unlinkedSettlementAdjustments.reduce((s, a) => s + Number(a.amount || 0), 0);
  const totalCredits = totalRecoveries + totalSettlementAdjustments;
  const netBalance = totalSales - totalCredits;
  const outstanding = Math.max(0, netBalance);
  const advanceBalance = Math.max(0, -netBalance);

  // Commission Analysis: Separate verified immutable rate snapshots from historical missing snapshots
  let unreconciledCount = 0;
  let unreconciledPackets = 0;
  (salesRes.data || []).forEach(order => {
    if (order.commission_rate_snapshot === null || order.commission_rate_snapshot === undefined) {
      unreconciledCount++;
    }
  });

  // Accrued commission based strictly on immutable sale-specific rate snapshots
  let accruedCommission = 0;
  (saleItemsRes.data || []).forEach(item => {
    const qty = Number(item.quantity) || 0;
    const snap = item.sales_orders?.commission_rate_snapshot;
    if (snap !== null && snap !== undefined) {
      accruedCommission += (qty * Number(snap));
    } else {
      unreconciledPackets += qty;
    }
  });

  const hasUnreconciledRates = unreconciledCount > 0;
  const distCommissionRate = Number(distRes?.data?.commission || 0);
  const estimatedUnreconciledCommission = unreconciledPackets * distCommissionRate;

  // Settled commission from approved settlements
  const settledCommission = (settlementsRes.data || []).reduce((acc, s) => acc + Number(s.amount || 0), 0);
  const commissionPayable = Math.max(0, accruedCommission - settledCommission);

  // Pending bookings summary (informational, does NOT alter balances)
  const pendingBookingsCount = (pendingBookingsRes.data || []).length;
  const pendingBookingsAmount = (pendingBookingsRes.data || []).reduce((s, b) => s + Number(b.total_amount || 0), 0);
  const pendingBookingsPackets = (pendingBookingsRes.data || []).reduce((s, b) => {
    return s + (b.sale_items || []).reduce((acc, i) => acc + Number(i.quantity || 0), 0);
  }, 0);

  return { 
    totalSales, 
    totalRecoveries, 
    totalSettlementAdjustments,
    totalCredits,
    totalPackets, 
    netBalance,
    outstanding, 
    advanceBalance,
    salesOutstanding: outstanding, 
    accruedCommission, 
    settledCommission, 
    commissionPayable,
    hasUnreconciledRates,
    unreconciledCount,
    unreconciledPackets,
    defaultCommissionRate: distCommissionRate,
    estimatedUnreconciledCommission,
    pendingBookingsCount,
    pendingBookingsAmount,
    pendingBookingsPackets
  };
}

// ── Distributor today recovery ────────────────────────────────────────────────
export async function fetchDistributorTodayRecovery(distributorId) {
  if (!distributorId) return 0;
  const todayStart = new Date(); todayStart.setHours(0,0,0,0);
  const recs = await fetchDistributorApprovedRecoveries(distributorId, {
    approvedOnly: true,
    dateFrom: todayStart.toISOString()
  });
  return recs.reduce((s, r) => s + Number(r.amount), 0);
}

// ── Distributor stock summary stats ───────────────────────────────────────────
export async function fetchDistributorStockStats(distributorId) {
  if (!distributorId) return { stock: 0, issued: 0, goodReturns: 0, damagedReturns: 0, pendingReturns: 0, hasPhysicalDispatch: false };
  const { data: inv, error } = await supabase
    .from('inventory_transactions')
    .select('transaction_type, quantity, status')
    .eq('distributor_id', distributorId);
  if (error) throw error;

  let issued = 0;
  let goodReturns = 0;
  let damagedReturns = 0;
  let pendingReturns = 0;

  (inv || []).forEach(r => {
    const qty = Number(r.quantity || 0);
    const isApproved = ['Approved', 'Posted'].includes(r.status);
    if (isApproved) {
      if (['Distributor_Issue', 'Salesman_Issue'].includes(r.transaction_type)) {
        issued += qty;
      } else if (['Distributor_Good_Return', 'Salesman_Good_Return'].includes(r.transaction_type)) {
        goodReturns += qty;
      } else if (['Distributor_Damaged_Return', 'Salesman_Damaged_Return'].includes(r.transaction_type)) {
        damagedReturns += qty;
      }
    } else if (r.status === 'Pending') {
      if (['Distributor_Good_Return', 'Distributor_Damaged_Return', 'Salesman_Good_Return', 'Salesman_Damaged_Return'].includes(r.transaction_type)) {
        pendingReturns += qty;
      }
    }
  });

  const stock = Math.max(0, issued - goodReturns - damagedReturns);
  return { stock, issued, goodReturns, damagedReturns, pendingReturns, hasPhysicalDispatch: issued > 0 };
}

// ── Distributor stock ledger records ──────────────────────────────────────────
export async function fetchDistributorStockLedger(distributorId) {
  if (!distributorId) return [];
  const { data, error } = await supabase
    .from('inventory_transactions')
    .select('*, product_packaging(name, products(name))')
    .eq('distributor_id', distributorId)
    .order('transaction_date', { ascending: false });
  if (error) throw error;
  return data || [];
}

// ── Distributor financial ledger records (Sales & Recoveries with running balance) ──
export async function fetchDistributorFinLedger(distributorId) {
  if (!distributorId) return [];
  const [salesRes, allRecs, settsRes] = await Promise.all([
    supabase
      .from('sales_orders')
      .select('id, reference_number, sale_date, total_amount, status, sale_items(quantity)')
      .eq('distributor_id', distributorId)
      .order('sale_date', { ascending: false })
      .limit(5000),
    fetchDistributorApprovedRecoveries(distributorId, { approvedOnly: false }),
    supabase
      .from('distributor_settlements')
      .select('id, reference_number, settlement_date, amount, settlement_type, payment_method, status, notes, recovery_id')
      .eq('distributor_id', distributorId)
      .in('status', ['Approved'])
      .order('settlement_date', { ascending: false })
      .limit(5000)
  ]);

  if (salesRes.error) throw salesRes.error;
  if (settsRes.error) throw settsRes.error;

  const orderRefMap = new Map();
  (salesRes.data || []).forEach(o => {
    orderRefMap.set(o.id, o.reference_number);
  });

  const rows = [];
  (salesRes.data || []).forEach(s => {
    const pkts = (s.sale_items || []).reduce((acc, item) => acc + Number(item.quantity || 0), 0);
    const isBooking = (s.reference_number || '').startsWith('BKG-');
    const isPending = s.status === 'Pending';
    const isApproved = ['Approved', 'Posted'].includes(s.status);

    if (isBooking) {
      // 1. Pending bookings: Nonfinancial commitment. Financial debit must be 0!
      const bookingVal = Number(s.total_amount || 0);
      rows.push({
        id: s.id,
        date: s.sale_date,
        type: isPending ? 'Booking (Pending)' : `Booking (${s.status})`,
        ref: s.reference_number,
        packets: pkts,
        debit: 0, // Financial debit is explicitly 0 (non-financial commitment)
        credit: 0,
        bookingValue: bookingVal,
        status: s.status,
        description: `Booking reservation: ${pkts} pkts · Value: Rs. ${bookingVal.toLocaleString('en-PK')} (${s.reference_number})`,
        isFinancialImpact: false, // Bookings do NOT alter financial receivables/balances
        isBooking: true
      });
    } else {
      rows.push({
        id: s.id,
        date: s.sale_date,
        type: 'Sale',
        ref: s.reference_number,
        packets: pkts,
        debit: Number(s.total_amount || 0),
        credit: 0,
        status: s.status,
        description: `Sale of ${pkts} pkts (${s.reference_number})`,
        isFinancialImpact: isApproved, // Only approved sales alter financial receivables/balances
        isBooking: false
      });
    }
  });

  // All recoveries from distributor (including booking advance recoveries)
  allRecs.forEach(r => {
    const isApproved = ['Approved', 'Posted'].includes(r.status);
    const hasPipe = r.reference_number && r.reference_number.includes('|');
    let cleanRef = r.reference_number;
    let linkedRef = null;

    if (hasPipe) {
      const parts = r.reference_number.split('|');
      cleanRef = parts[0]?.trim();
      const target = parts[1]?.trim();
      linkedRef = orderRefMap.get(target) || target;
    }

    const isBookingAdvance = Boolean(linkedRef);

    rows.push({
      id: r.id,
      date: r.recovery_date,
      type: isBookingAdvance ? 'Recovery (Advance)' : `Recovery (${r.payment_method || 'Cash'})`,
      ref: cleanRef, // Clean human-readable reference (e.g. REC-MUMLRQP1)
      raw_ref: r.reference_number, // Preserved internal reference
      linked_order_ref: linkedRef, // Resolved human-readable booking reference (e.g. BKG-MUMKW006)
      packets: 0,
      debit: 0,
      credit: Number(r.amount || 0),
      status: r.status,
      description: isBookingAdvance 
        ? `Advance payment on booking ${linkedRef}${r.notes ? ' · ' + r.notes : ''}`
        : `Payment received (${r.payment_method || 'Cash'})${r.notes ? ' · ' + r.notes : ''}`,
      isFinancialImpact: isApproved,
      isBooking: false
    });
  });

  // Commission_Against_Outstanding adjustments (counted exactly once if no duplicate recovery row exists)
  (settsRes.data || [])
    .filter(st => st.settlement_type === 'Commission_Against_Outstanding')
    .filter(st => !st.recovery_id && !allRecs.some(r => r.id === st.recovery_id || (r.reference_number && r.reference_number.includes(st.reference_number))))
    .forEach(st => {
      rows.push({
        id: st.id,
        date: st.settlement_date,
        type: 'Commission Adjustment',
        ref: st.reference_number,
        packets: 0,
        debit: 0,
        credit: Number(st.amount || 0),
        status: st.status,
        description: `Commission applied against outstanding balance (${st.reference_number})${st.notes ? ' · ' + st.notes : ''}`,
        isFinancialImpact: true,
        isBooking: false
      });
    });

  // Stable chronological sorting:
  // 1. Timestamp (ascending)
  // 2. Transaction Type Priority: Sale (1) -> Recovery (2) -> Commission Adjustment (3) -> Booking (4)
  // 3. Alphanumeric tie-breaker on reference number/id
  rows.sort((a, b) => {
    const tA = new Date(a.date).getTime() || 0;
    const tB = new Date(b.date).getTime() || 0;
    if (tA !== tB) return tA - tB;

    const priority = (type) => {
      if (type === 'Sale') return 1;
      if (type.startsWith('Recovery')) return 2;
      if (type.startsWith('Commission')) return 3;
      if (type.startsWith('Booking')) return 4;
      return 5;
    };
    const diff = priority(a.type) - priority(b.type);
    if (diff !== 0) return diff;

    const refA = a.ref || a.id || '';
    const refB = b.ref || b.id || '';
    return refA.localeCompare(refB);
  });

  // Running balance calculation:
  // Strict rule: Only approved financial transactions alter running balance.
  // Pending bookings and unapproved entries get balance = null (displayed as a dash in UI).
  let runningBal = 0;
  const withBal = rows.map(r => {
    if (r.isFinancialImpact) {
      if (r.debit) runningBal += Number(r.debit);
      if (r.credit) runningBal -= Number(r.credit);
      return { ...r, balance: runningBal, isPosted: true };
    } else {
      return { ...r, balance: null, isPosted: false };
    }
  });

  return withBal.reverse();
}

// ── Distributor commission ledger records ─────────────────────────────────────
export async function fetchDistributorCommissionLedger(distributorId) {
  if (!distributorId) return [];
  const [salesRes, settsRes] = await Promise.all([
    supabase
      .from('sales_orders')
      .select('id, reference_number, sale_date, status, commission_rate_snapshot, sale_items(quantity)')
      .eq('distributor_id', distributorId)
      .not('reference_number', 'like', 'BKG-%') // Exclude bookings from commission ledger!
      .order('sale_date', { ascending: false }),
    supabase
      .from('distributor_settlements')
      .select('id, reference_number, settlement_date, amount, settlement_type, payment_method, status, notes')
      .eq('distributor_id', distributorId)
      .order('settlement_date', { ascending: false })
  ]);

  const rows = [];
  (salesRes.data || []).forEach(s => {
    const pkts = (s.sale_items || []).reduce((acc, item) => acc + Number(item.quantity || 0), 0);
    const snap = s.commission_rate_snapshot;
    const hasSnap = snap !== null && snap !== undefined;
    const rate = hasSnap ? Number(snap) : null;
    const earned = hasSnap ? (pkts * rate) : 0;
    const isApproved = ['Approved', 'Posted'].includes(s.status);

    rows.push({
      id: s.id,
      date: s.sale_date,
      type: 'Commission Accrued',
      ref: s.reference_number,
      packets: pkts,
      rate: rate,
      earned: earned,
      paid: 0,
      status: s.status,
      isMissingSnapshot: !hasSnap,
      isApproved,
      notes: hasSnap 
        ? `Accrued from sale ${s.reference_number} (${pkts} pkts @ Rs. ${rate})`
        : `Sale ${s.reference_number} (${pkts} pkts) — Rate snapshot missing in DB`
    });
  });

  (settsRes.data || []).forEach(st => {
    const isApproved = ['Approved', 'Posted'].includes(st.status);
    rows.push({
      id: st.id,
      date: st.settlement_date,
      type: `Commission Paid (${st.payment_method || 'Cash'})`,
      ref: st.reference_number,
      packets: 0,
      rate: null,
      earned: 0,
      paid: Number(st.amount || 0),
      status: st.status,
      isMissingSnapshot: false,
      isApproved,
      notes: st.notes || `Settlement payout (${st.settlement_type})`
    });
  });

  // Stable sorting
  rows.sort((a, b) => {
    const tA = new Date(a.date).getTime() || 0;
    const tB = new Date(b.date).getTime() || 0;
    if (tA !== tB) return tA - tB;
    return (a.ref || a.id || '').localeCompare(b.ref || b.id || '');
  });

  let runningComm = 0;
  const withBal = rows.map(r => {
    if (r.isApproved) {
      if (r.earned) runningComm += Number(r.earned);
      if (r.paid) runningComm -= Number(r.paid);
      return { ...r, balance: runningComm };
    }
    return { ...r, balance: null };
  });

  return withBal.reverse();
}


export async function fetchDashboardMetrics(selectedDateStr) {
  const dateObj = selectedDateStr ? new Date(selectedDateStr + 'T00:00:00') : new Date();
  
  const endOfDay = new Date(dateObj);
  endOfDay.setHours(23, 59, 59, 999);
  const eodIso = endOfDay.toISOString();
  
  const startOfDay = new Date(dateObj);
  startOfDay.setHours(0, 0, 0, 0);
  const sodIso = startOfDay.toISOString();

  // 1. INVENTORY TRANSACTIONS (Cumulative up to EOD)
  const { data: invRows, error: invErr } = await supabase
    .from('inventory_transactions')
    .select('transaction_type, quantity, distributor_id, salesman_id, transaction_date')
    .in('status', ['Approved', 'Posted'])
    .lte('transaction_date', eodIso);

  if (invErr) throw invErr;

  let companyStock = 0;
  let distReturnStock = 0;
  let damageReturnStock = 0;
  let distReturnSelectedDate = 0;
  let damageReturnSelectedDate = 0;

  (invRows || []).forEach(r => {
    const qty = Number(r.quantity) || 0;
    const isSelectedDate = r.transaction_date >= sodIso && r.transaction_date <= eodIso;
    const isGoodReturn = ['Salesman_Good_Return', 'Customer_Good_Return', 'Distributor_Good_Return'].includes(r.transaction_type);
    const isDamagedReturn = ['Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Distributor_Damaged_Return', 'Damage', 'Expiry'].includes(r.transaction_type);
    
    // Company Saleable Stock (Cumulative)
    if (['Production', 'Purchase'].includes(r.transaction_type) || isGoodReturn) {
      companyStock += qty;
    }
    if (['Salesman_Issue', 'Distributor_Issue'].includes(r.transaction_type)) {
      companyStock -= qty;
    }
    if (r.transaction_type === 'Adjustment') {
      companyStock += qty;
    }

    // Distributors Return Stock (Cumulative & Selected Date)
    if (r.distributor_id && (isGoodReturn || isDamagedReturn)) {
      distReturnStock += qty;
      if (isSelectedDate) {
        distReturnSelectedDate += qty;
      }
    }
    
    // Damage Return Stock (Cumulative & Selected Date) - strictly isolated from saleable stock
    if (isDamagedReturn) {
      damageReturnStock += qty;
      if (isSelectedDate) {
        damageReturnSelectedDate += qty;
      }
    }
  });

  // 2. GLOBAL SETTINGS (Opening balances & default rates)
  const { data: gs } = await supabase.from('global_settings').select('*').limit(1).maybeSingle();
  const advOpening = Number(gs?.advertisement_opening_balance) || 0;
  const welfOpening = Number(gs?.welfare_opening_balance) || 0;
  const defaultAdvRate = Number(gs?.advertisement_rate) || 20.0;
  const defaultWelfRate = Number(gs?.welfare_rate) || 10.0;

  // 3. SALES & SALE ITEMS (Cumulative & Selected Date)
  const { data: allSales, error: salesErr } = await supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, distributor_id, commission_rate_snapshot, advertisement_rate_snapshot, welfare_rate_snapshot, distributors(commission), sale_items(quantity)')
    .like('reference_number', 'SAL-%')
    .in('status', ['Approved', 'Posted'])
    .lte('sale_date', eodIso);

  if (salesErr) throw salesErr;

  let salesSelectedDateAmount = 0;
  let salesSelectedDatePackets = 0;
  let commissionSelectedDate = 0;
  let cumulativeDistSalesAmount = 0;
  let cumulativePkts = 0;
  let cumulativeCommissionEarned = 0;
  let cumulativeAdvAllocation = 0;
  let cumulativeWelfAllocation = 0;

  (allSales || []).forEach(sale => {
    const isSelectedDate = sale.sale_date >= sodIso && sale.sale_date <= eodIso;
    const pkts = (sale.sale_items || []).reduce((a, item) => a + Number(item.quantity || 0), 0);
    const amt = Number(sale.total_amount) || 0;

    // Use verified immutable snapshots
    const commRate = (sale.commission_rate_snapshot !== null && sale.commission_rate_snapshot !== undefined)
      ? Number(sale.commission_rate_snapshot)
      : (Number(sale.distributors?.commission) || 0);

    const advRate = (sale.advertisement_rate_snapshot !== null && sale.advertisement_rate_snapshot !== undefined)
      ? Number(sale.advertisement_rate_snapshot)
      : defaultAdvRate;

    const welfRate = (sale.welfare_rate_snapshot !== null && sale.welfare_rate_snapshot !== undefined)
      ? Number(sale.welfare_rate_snapshot)
      : defaultWelfRate;

    cumulativePkts += pkts;
    cumulativeDistSalesAmount += amt;
    cumulativeCommissionEarned += (pkts * commRate);
    cumulativeAdvAllocation += (pkts * advRate);
    cumulativeWelfAllocation += (pkts * welfRate);

    if (isSelectedDate) {
      salesSelectedDateAmount += amt;
      salesSelectedDatePackets += pkts;
      commissionSelectedDate += (pkts * commRate);
    }
  });

  // 4. RECOVERIES (Cumulative for Outstanding & Selected Date)
  const { data: allRecs, error: recsErr } = await supabase
    .from('recoveries')
    .select('amount, distributor_id, recovery_date, reference_number')
    .in('status', ['Approved', 'Posted'])
    .lte('recovery_date', eodIso);

  if (recsErr) throw recsErr;

  let cumulativeDistRecAmount = 0;
  let recoverySelectedDateAmount = 0;
  (allRecs || [])
    .filter(r => !r.reference_number || (!r.reference_number.includes('|') && !r.reference_number.includes('|BKG-')))
    .forEach(r => {
      const amt = Number(r.amount || 0);
      cumulativeDistRecAmount += amt;
      if (r.recovery_date >= sodIso && r.recovery_date <= eodIso) {
        recoverySelectedDateAmount += amt;
      }
    });

  const distributorsOutstanding = Math.max(0, cumulativeDistSalesAmount - cumulativeDistRecAmount);

  // 5. DISTRIBUTOR COMMISSION SETTLEMENTS (Separate Commission Paid vs Commission Payable)
  const { data: allSettlements, error: settsErr } = await supabase
    .from('distributor_settlements')
    .select('amount, settlement_type, settlement_date')
    .eq('status', 'Approved')
    .lte('settlement_date', eodIso);

  if (settsErr) throw settsErr;

  let cumulativeCommissionPaid = 0;
  let selectedDateCommissionPaid = 0;
  (allSettlements || []).forEach(s => {
    const amt = Number(s.amount || 0);
    cumulativeCommissionPaid += amt;
    if (s.settlement_date >= sodIso && s.settlement_date <= eodIso) {
      selectedDateCommissionPaid += amt;
    }
  });

  const distributorsCommissionPayable = Math.max(0, cumulativeCommissionEarned - cumulativeCommissionPaid);

  // 6. EXPENSES (Cumulative & Selected Date)
  const { data: allExps, error: expsErr } = await supabase
    .from('expenses')
    .select('amount, expense_date, head, category')
    .in('status', ['Approved', 'Posted'])
    .lte('expense_date', eodIso);

  if (expsErr) throw expsErr;

  let expensesSelectedDate = 0;
  let cumulativeExpensesAmount = 0;
  let cumulativeAdvExp = 0;
  let cumulativeWelfExp = 0;

  (allExps || []).forEach(exp => {
    const amt = Number(exp.amount) || 0;
    const isSelectedDate = exp.expense_date >= sodIso && exp.expense_date <= eodIso;

    cumulativeExpensesAmount += amt;
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

  const advertisementBalance = advOpening + cumulativeAdvAllocation - cumulativeAdvExp;
  const welfareBalance = welfOpening + cumulativeWelfAllocation - cumulativeWelfExp;

  return {
    companyStock,
    salesAmount: salesSelectedDateAmount,
    salesSelectedDatePackets,
    salesCumulativeAmount: cumulativeDistSalesAmount,
    salesCumulativePackets: cumulativePkts,
    distributorsOutstanding,
    recoverySelectedDateAmount,
    recoveryCumulativeAmount: cumulativeDistRecAmount,
    expensesAmount: expensesSelectedDate,
    expensesCumulativeAmount: cumulativeExpensesAmount,
    advertisementBalance,
    advertisementAllocation: cumulativeAdvAllocation,
    advertisementExpenses: cumulativeAdvExp,
    welfareBalance,
    welfareAllocation: cumulativeWelfAllocation,
    welfareExpenses: cumulativeWelfExp,
    commissionAmount: commissionSelectedDate,
    commissionEarnedCumulative: cumulativeCommissionEarned,
    commissionPaidCumulative: cumulativeCommissionPaid,
    commissionPayable: distributorsCommissionPayable,
    distReturnStock,
    distReturnSelectedDate,
    damageReturnStock,
    damageReturnSelectedDate
  };
}

export async function fetchReportsMetrics(selectedDateStr) {
  const dateObj = selectedDateStr ? new Date(selectedDateStr + 'T00:00:00') : new Date();
  
  const endOfDay = new Date(dateObj);
  endOfDay.setHours(23, 59, 59, 999);
  const eodIso = endOfDay.toISOString();
  
  const startOfDay = new Date(dateObj);
  startOfDay.setHours(0, 0, 0, 0);
  const sodIso = startOfDay.toISOString();

  // 1. GLOBAL SETTINGS
  const { data: gs } = await supabase.from('global_settings').select('*').limit(1).maybeSingle();
  const advOpening = Number(gs?.advertisement_opening_balance) || 0;
  const welfOpening = Number(gs?.welfare_opening_balance) || 0;
  const defaultAdvRate = Number(gs?.advertisement_rate) || 20.0;
  const defaultWelfRate = Number(gs?.welfare_rate) || 10.0;

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
    .select('id, reference_number, sale_date, total_amount, distributor_id, commission_rate_snapshot, advertisement_rate_snapshot, welfare_rate_snapshot, distributors(commission), sale_items(quantity)')
    .like('reference_number', 'SAL-%')
    .in('status', ['Approved', 'Posted'])
    .lte('sale_date', eodIso);
    
  let cumulativeAdvAllocation = 0;
  let cumulativeWelfAllocation = 0;
  let selectedDateCommission = 0;
  let selectedDateSalesAmount = 0;
  let selectedDateSalesPackets = 0;
  let selectedDateSalesCount = 0;
  
  (allSales || []).forEach(sale => {
    const isSelectedDate = sale.sale_date >= sodIso && sale.sale_date <= eodIso;
    const pkts = (sale.sale_items || []).reduce((a, item) => a + Number(item.quantity || 0), 0);
    
    const commRate = (sale.commission_rate_snapshot !== null && sale.commission_rate_snapshot !== undefined)
      ? Number(sale.commission_rate_snapshot)
      : (Number(sale.distributors?.commission) || 0);

    const advRate = (sale.advertisement_rate_snapshot !== null && sale.advertisement_rate_snapshot !== undefined)
      ? Number(sale.advertisement_rate_snapshot)
      : defaultAdvRate;

    const welfRate = (sale.welfare_rate_snapshot !== null && sale.welfare_rate_snapshot !== undefined)
      ? Number(sale.welfare_rate_snapshot)
      : defaultWelfRate;

    cumulativeAdvAllocation += (pkts * advRate);
    cumulativeWelfAllocation += (pkts * welfRate);
    
    if (isSelectedDate) {
      selectedDateCommission += (pkts * commRate);
      selectedDateSalesAmount += Number(sale.total_amount || 0);
      selectedDateSalesPackets += pkts;
      selectedDateSalesCount += 1;
    }
  });

  // 4. EXPENSES (Cumulative & Selected Date)
  const { data: allExps } = await supabase
    .from('expenses')
    .select('reference_number, amount, expense_date, category, status, account_detail, tid, description, head, distributor_id, distributors(name, code)')
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
    
    if (exp.category === 'Company' || exp.category === 'Office') {
      cumCompanyOfficeExp += amt;
    } else if (exp.category === 'Others') {
      cumOthersExp += amt;
    }
    
    if (isSelectedDate && exp.category === 'Distributor' && exp.distributor_id) {
      selectedDateDistExp += amt;
    }
  });

  // 5. RECOVERIES (Selected Date)
  const { data: recoveriesData } = await supabase
    .from('recoveries')
    .select('reference_number, amount, recovery_date, status, account_detail, tid, notes, distributor_id, distributors(name, code)')
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
    ['Distributor_Good_Return', 'Distributor_Damaged_Return', 'Salesman_Good_Return', 'Salesman_Damaged_Return'].includes(r.transaction_type)
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
    const isGoodReturn = ['Distributor_Good_Return', 'Customer_Good_Return', 'Salesman_Good_Return'].includes(r.transaction_type);
    const isDamagedReturn = ['Distributor_Damaged_Return', 'Customer_Damaged_Return', 'Salesman_Damaged_Return', 'Damage', 'Expiry'].includes(r.transaction_type);
    
    if (['Production', 'Purchase'].includes(r.transaction_type) || isGoodReturn) {
       stockSellable += qty;
    }
    if (['Salesman_Issue', 'Distributor_Issue'].includes(r.transaction_type)) {
       stockSellable -= qty;
    }
    if (r.transaction_type === 'Adjustment') {
       stockSellable += qty;
    }
    if (isDamagedReturn) {
       stockDamaged += qty;
    }
  });

  // Calculate Balances
  const distributorCommissionBalance = Math.max(0, selectedDateCommission - selectedDateDistExp);
  const advertisementBalance = advOpening + cumulativeAdvAllocation - cumCompanyOfficeExp;
  const welfareBalance = welfOpening + cumulativeWelfAllocation - cumOthersExp;

  return {
    sales: {
      amount: selectedDateSalesAmount,
      packets: selectedDateSalesPackets,
      count: selectedDateSalesCount
    },
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
      allocation: cumulativeAdvAllocation,
      expenses: cumCompanyOfficeExp,
      balance: advertisementBalance
    },
    welfare: {
      opening: welfOpening,
      allocation: cumulativeWelfAllocation,
      expenses: cumOthersExp,
      balance: welfareBalance
    }
  };
}

// ── COMPREHENSIVE REPORTS SERVICES ──────────────────────────────────────────

export async function fetchSalesReport(filters = {}) {
  let q = supabase
    .from('sales_orders')
    .select('*, distributors(name, code, phone), profiles(full_name), sale_items(*, product_packaging(name, products(name)))')
    .like('reference_number', 'SAL-%')
    .order('sale_date', { ascending: false });

  if (filters.status && filters.status !== 'All') {
    q = q.eq('status', filters.status);
  } else {
    q = q.in('status', ['Approved', 'Posted']);
  }
  if (filters.startDate) q = q.gte('sale_date', `${filters.startDate}T00:00:00.000Z`);
  if (filters.endDate) q = q.lte('sale_date', `${filters.endDate}T23:59:59.999Z`);
  if (filters.distributorId) q = q.eq('distributor_id', filters.distributorId);

  const { data, error } = await q;
  if (error) throw error;

  return (data || []).map(s => {
    const totalPackets = (s.sale_items || []).reduce((acc, item) => acc + Number(item.quantity || 0), 0);
    const commRate = s.commission_rate_snapshot !== null && s.commission_rate_snapshot !== undefined
      ? Number(s.commission_rate_snapshot)
      : null;
    const advRate = s.advertisement_rate_snapshot !== null && s.advertisement_rate_snapshot !== undefined
      ? Number(s.advertisement_rate_snapshot)
      : null;
    const welfRate = s.welfare_rate_snapshot !== null && s.welfare_rate_snapshot !== undefined
      ? Number(s.welfare_rate_snapshot)
      : null;
    const totalCommission = commRate !== null ? (totalPackets * commRate) : null;

    return {
      ...s,
      totalPackets,
      commRate,
      advRate,
      welfRate,
      totalCommission
    };
  });
}

export async function fetchBookingReport(filters = {}) {
  let q = supabase
    .from('sales_orders')
    .select('*, distributors(name, code, phone), sale_items(*, product_packaging(name, products(name)))')
    .like('reference_number', 'BKG-%')
    .order('sale_date', { ascending: false });

  if (filters.status && filters.status !== 'All') q = q.eq('status', filters.status);
  if (filters.startDate) q = q.gte('sale_date', `${filters.startDate}T00:00:00.000Z`);
  if (filters.endDate) q = q.lte('sale_date', `${filters.endDate}T23:59:59.999Z`);
  if (filters.distributorId) q = q.eq('distributor_id', filters.distributorId);

  const { data, error } = await q;
  if (error) throw error;

  return (data || []).map(b => ({
    ...b,
    totalPackets: (b.sale_items || []).reduce((acc, item) => acc + Number(item.quantity || 0), 0)
  }));
}

export async function fetchDistributorLedgerReport(distributorId, startDate = null, endDate = null) {
  if (!distributorId) return { entries: [], distributor: null, openingBalance: 0, closingBalance: 0, totalSales: 0, totalRecoveries: 0, settlements: [] };

  const { data: dist, error: dErr } = await supabase.from('distributors').select('*').eq('id', distributorId).single();
  if (dErr) throw dErr;

  let sq = supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, status, commission_rate_snapshot, sale_items(quantity)')
    .eq('distributor_id', distributorId)
    .in('status', ['Approved', 'Posted'])
    .not('reference_number', 'like', 'BKG-%')
    .limit(5000);

  let setq = supabase
    .from('distributor_settlements')
    .select('id, reference_number, settlement_date, amount, settlement_type, payment_method, status, notes, recovery_id')
    .eq('distributor_id', distributorId)
    .in('status', ['Approved'])
    .limit(5000);

  let allOrdersQ = supabase
    .from('sales_orders')
    .select('id, reference_number')
    .eq('distributor_id', distributorId)
    .limit(5000);

  const [{ data: sales, error: sErr }, allRecs, { data: setts, error: setErr }, { data: allOrders }] = await Promise.all([
    sq,
    fetchDistributorApprovedRecoveries(distributorId, { approvedOnly: true }),
    setq,
    allOrdersQ
  ]);

  if (sErr) throw sErr;
  if (setErr) throw setErr;

  const orderRefMap = new Map();
  (allOrders || []).forEach(o => {
    orderRefMap.set(o.id, o.reference_number);
  });

  const allEntries = [];

  (sales || []).forEach(s => {
    const pkts = (s.sale_items || []).reduce((acc, item) => acc + Number(item.quantity || 0), 0);
    allEntries.push({
      id: s.id,
      date: s.sale_date,
      ref: s.reference_number,
      type: 'Sale',
      description: `Sale of ${pkts} pkts (${s.reference_number})`,
      debit: Number(s.total_amount || 0),
      credit: 0,
      packets: pkts,
      status: s.status
    });
  });

  (allRecs || []).forEach(r => {
    const hasPipe = r.reference_number && r.reference_number.includes('|');
    let cleanRef = r.reference_number;
    let linkedRef = '';

    if (hasPipe) {
      const parts = r.reference_number.split('|');
      cleanRef = parts[0]?.trim();
      const target = parts[1]?.trim();
      linkedRef = orderRefMap.get(target) || target;
    }

    const isBookingAdvance = Boolean(linkedRef);

    allEntries.push({
      id: r.id,
      date: r.recovery_date,
      ref: cleanRef,
      raw_ref: r.reference_number,
      linked_order_ref: linkedRef,
      type: isBookingAdvance ? 'Recovery (Advance)' : `Recovery (${r.payment_method || 'Cash'})`,
      description: isBookingAdvance
        ? `Advance payment on booking ${linkedRef}${r.notes ? ' · ' + r.notes : ''}`
        : `Payment received (${r.payment_method || 'Cash'})${r.notes ? ' · ' + r.notes : ''}`,
      debit: 0,
      credit: Number(r.amount || 0),
      packets: 0,
      status: r.status
    });
  });

  // Commission_Against_Outstanding adjustments (counted exactly once if no duplicate recovery row exists)
  (setts || [])
    .filter(st => st.settlement_type === 'Commission_Against_Outstanding')
    .filter(st => !st.recovery_id && !allRecs.some(r => r.id === st.recovery_id || (r.reference_number && r.reference_number.includes(st.reference_number))))
    .forEach(st => {
      allEntries.push({
        id: st.id,
        date: st.settlement_date,
        ref: st.reference_number,
        type: 'Commission Adjustment',
        description: `Commission applied against outstanding balance (${st.reference_number})${st.notes ? ' · ' + st.notes : ''}`,
        debit: 0,
        credit: Number(st.amount || 0),
        packets: 0,
        status: st.status
      });
    });

  allEntries.sort((a, b) => new Date(a.date) - new Date(b.date));

  let openingBalance = 0;
  const filteredEntries = [];
  const startIso = startDate ? `${startDate}T00:00:00.000Z` : null;
  const endIso = endDate ? `${endDate}T23:59:59.999Z` : null;

  allEntries.forEach(entry => {
    if (startIso && entry.date < startIso) {
      openingBalance += (entry.debit - entry.credit);
    } else if (!endIso || entry.date <= endIso) {
      filteredEntries.push(entry);
    }
  });

  let runningBalance = openingBalance;
  let totalPeriodSales = 0;
  let totalPeriodRecoveries = 0;

  const entriesWithBalance = filteredEntries.map(entry => {
    runningBalance += (entry.debit - entry.credit);
    totalPeriodSales += entry.debit;
    totalPeriodRecoveries += entry.credit;
    return {
      ...entry,
      balance: runningBalance
    };
  });

  return {
    distributor: dist,
    openingBalance,
    closingBalance: runningBalance,
    totalSales: totalPeriodSales,
    totalRecoveries: totalPeriodRecoveries,
    entries: entriesWithBalance,
    settlements: setts || []
  };
}

export async function fetchRecoveryReport(filters = {}) {
  let q = supabase
    .from('recoveries')
    .select('*, distributors(name, code, phone)')
    .order('recovery_date', { ascending: false });

  if (filters.status && filters.status !== 'All') q = q.eq('status', filters.status);
  else q = q.in('status', ['Approved', 'Posted']);
  if (filters.startDate) q = q.gte('recovery_date', `${filters.startDate}T00:00:00.000Z`);
  if (filters.endDate) q = q.lte('recovery_date', `${filters.endDate}T23:59:59.999Z`);
  if (filters.paymentMethod && filters.paymentMethod !== 'All') q = q.eq('payment_method', filters.paymentMethod);

  let unassignedQ = null;
  if (filters.distributorId) {
    q = q.eq('distributor_id', filters.distributorId);
    unassignedQ = supabase
      .from('recoveries')
      .select('*, distributors(name, code, phone)')
      .is('distributor_id', null)
      .like('reference_number', '%|%')
      .order('recovery_date', { ascending: false });
    if (filters.status && filters.status !== 'All') unassignedQ = unassignedQ.eq('status', filters.status);
    else unassignedQ = unassignedQ.in('status', ['Approved', 'Posted']);
    if (filters.startDate) unassignedQ = unassignedQ.gte('recovery_date', `${filters.startDate}T00:00:00.000Z`);
    if (filters.endDate) unassignedQ = unassignedQ.lte('recovery_date', `${filters.endDate}T23:59:59.999Z`);
    if (filters.paymentMethod && filters.paymentMethod !== 'All') unassignedQ = unassignedQ.eq('payment_method', filters.paymentMethod);
  }

  const [res, unassignedRes] = await Promise.all([
    q,
    unassignedQ ? unassignedQ : Promise.resolve({ data: [] })
  ]);
  if (res.error) throw res.error;
  if (unassignedRes && unassignedRes.error) throw unassignedRes.error;

  let list = res.data || [];
  if (filters.distributorId && (unassignedRes.data || []).length > 0) {
    const distOrders = await supabase
      .from('sales_orders')
      .select('id, reference_number, distributors(name, code, phone)')
      .eq('distributor_id', filters.distributorId);
    
    const validIds = new Map();
    (distOrders.data || []).forEach(o => {
      validIds.set(o.id, o.distributors);
      if (o.reference_number) validIds.set(o.reference_number, o.distributors);
    });

    const matched = [];
    (unassignedRes.data || []).forEach(r => {
      if (r.reference_number && r.reference_number.includes('|')) {
        const target = r.reference_number.split('|')[1]?.trim();
        if (target && validIds.has(target)) {
          matched.push({
            ...r,
            distributors: validIds.get(target)
          });
        }
      }
    });
    list = [...list, ...matched];
    list.sort((a, b) => new Date(b.recovery_date) - new Date(a.recovery_date));
  }
  return list;
}

export async function fetchStockMovementReport(filters = {}) {
  let q = supabase
    .from('inventory_transactions')
    .select('*, product_packaging(name, products(name)), distributors(name, code), salesmen(code, profiles(full_name))')
    .order('transaction_date', { ascending: false });

  if (filters.status && filters.status !== 'All') q = q.eq('status', filters.status);
  else q = q.in('status', ['Approved', 'Posted']);
  if (filters.startDate) q = q.gte('transaction_date', `${filters.startDate}T00:00:00.000Z`);
  if (filters.endDate) q = q.lte('transaction_date', `${filters.endDate}T23:59:59.999Z`);
  if (filters.transactionType && filters.transactionType !== 'All') q = q.eq('transaction_type', filters.transactionType);
  if (filters.distributorId) q = q.eq('distributor_id', filters.distributorId);

  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

export async function fetchReturnsReport(filters = {}) {
  let q = supabase
    .from('inventory_transactions')
    .select('*, product_packaging(name, products(name)), distributors(name, code), salesmen(code, profiles(full_name))')
    .in('transaction_type', [
      'Distributor_Good_Return', 'Distributor_Damaged_Return',
      'Salesman_Good_Return', 'Salesman_Damaged_Return',
      'Customer_Good_Return', 'Customer_Damaged_Return'
    ])
    .order('transaction_date', { ascending: false });

  if (filters.status && filters.status !== 'All') q = q.eq('status', filters.status);
  else q = q.in('status', ['Approved', 'Posted']);
  if (filters.startDate) q = q.gte('transaction_date', `${filters.startDate}T00:00:00.000Z`);
  if (filters.endDate) q = q.lte('transaction_date', `${filters.endDate}T23:59:59.999Z`);
  if (filters.distributorId) q = q.eq('distributor_id', filters.distributorId);

  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

export async function fetchExpenseReport(filters = {}) {
  let q = supabase
    .from('expenses')
    .select('*, distributors(name, code), persons(name, code, category)')
    .order('expense_date', { ascending: false });

  if (filters.status && filters.status !== 'All') q = q.eq('status', filters.status);
  else q = q.in('status', ['Approved', 'Posted']);
  if (filters.startDate) q = q.gte('expense_date', `${filters.startDate}T00:00:00.000Z`);
  if (filters.endDate) q = q.lte('expense_date', `${filters.endDate}T23:59:59.999Z`);
  if (filters.category && filters.category !== 'All') q = q.eq('category', filters.category);
  if (filters.head && filters.head !== 'All') q = q.eq('head', filters.head);

  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

export async function fetchPersonPaymentReport(filters = {}) {
  let q = supabase
    .from('person_ledger_entries')
    .select('*, persons(name, code, category, phone), expenses(reference_number)')
    .order('entry_date', { ascending: false });

  if (filters.status && filters.status !== 'All') q = q.eq('status', filters.status);
  else q = q.in('status', ['Approved', 'Posted']);
  if (filters.startDate) q = q.gte('entry_date', `${filters.startDate}T00:00:00.000Z`);
  if (filters.endDate) q = q.lte('entry_date', `${filters.endDate}T23:59:59.999Z`);
  if (filters.personId) q = q.eq('person_id', filters.personId);
  if (filters.entryType && filters.entryType !== 'All') q = q.eq('entry_type', filters.entryType);

  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

export async function fetchCommissionSettlementReport(filters = {}) {
  let q = supabase
    .from('distributor_settlements')
    .select('*, distributors(name, code, phone), recoveries(reference_number)')
    .order('settlement_date', { ascending: false });

  if (filters.status && filters.status !== 'All') q = q.eq('status', filters.status);
  if (filters.startDate) q = q.gte('settlement_date', `${filters.startDate}T00:00:00.000Z`);
  if (filters.endDate) q = q.lte('settlement_date', `${filters.endDate}T23:59:59.999Z`);
  if (filters.distributorId) q = q.eq('distributor_id', filters.distributorId);
  if (filters.settlementType && filters.settlementType !== 'All') q = q.eq('settlement_type', filters.settlementType);

  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

export async function fetchAdvWelfareReport(filters = {}) {
  const { data: gs } = await supabase.from('global_settings').select('*').limit(1).maybeSingle();
  const advOpening = Number(gs?.advertisement_opening_balance) || 0;
  const welfOpening = Number(gs?.welfare_opening_balance) || 0;
  const defaultAdvRate = Number(gs?.advertisement_rate) || 20.0;
  const defaultWelfRate = Number(gs?.welfare_rate) || 10.0;

  let sq = supabase.from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, advertisement_rate_snapshot, welfare_rate_snapshot, sale_items(quantity)')
    .in('status', ['Approved', 'Posted'])
    .order('sale_date', { ascending: false });

  let eq = supabase.from('expenses')
    .select('id, reference_number, expense_date, amount, head, category, description')
    .in('status', ['Approved', 'Posted'])
    .in('head', ['Advertisement', 'Welfare'])
    .order('expense_date', { ascending: false });

  if (filters.startDate) {
    sq = sq.gte('sale_date', `${filters.startDate}T00:00:00.000Z`);
    eq = eq.gte('expense_date', `${filters.startDate}T00:00:00.000Z`);
  }
  if (filters.endDate) {
    sq = sq.lte('sale_date', `${filters.endDate}T23:59:59.999Z`);
    eq = eq.lte('expense_date', `${filters.endDate}T23:59:59.999Z`);
  }

  const [{ data: sales }, { data: expenses }] = await Promise.all([sq, eq]);

  let advAllocated = 0;
  let welfAllocated = 0;
  let advSpent = 0;
  let welfSpent = 0;

  (sales || []).forEach(s => {
    const pkts = (s.sale_items || []).reduce((acc, i) => acc + Number(i.quantity || 0), 0);
    const advRate = s.advertisement_rate_snapshot !== null && s.advertisement_rate_snapshot !== undefined
      ? Number(s.advertisement_rate_snapshot)
      : defaultAdvRate;
    const welfRate = s.welfare_rate_snapshot !== null && s.welfare_rate_snapshot !== undefined
      ? Number(s.welfare_rate_snapshot)
      : defaultWelfRate;

    advAllocated += (pkts * advRate);
    welfAllocated += (pkts * welfRate);
  });

  (expenses || []).forEach(e => {
    const amt = Number(e.amount || 0);
    if (e.head === 'Advertisement' || e.category === 'Advertisement') advSpent += amt;
    if (e.head === 'Welfare' || e.category === 'Welfare') welfSpent += amt;
  });

  return {
    advertisement: {
      opening: advOpening,
      allocated: advAllocated,
      spent: advSpent,
      balance: advOpening + advAllocated - advSpent
    },
    welfare: {
      opening: welfOpening,
      allocated: welfAllocated,
      spent: welfSpent,
      balance: welfOpening + welfAllocated - welfSpent
    },
    contributions: sales || [],
    expenses: expenses || []
  };
}


export async function fetchGlobalSettings() {
  const { data, error } = await supabase.from('global_settings').select('*').limit(1).single();
  if (error) throw error;
  return data;
}

export async function updateGlobalSettings(fields) {
  const { error } = await supabase.from('global_settings').update(fields).not('id', 'is', null);
  if (error) throw error;
}

// --- PERSON-WISE PAYMENT MANAGEMENT ------------------------------------------

export async function fetchPersons(filters = {}) {
  let q = supabase.from('persons').select('*').order('name');
  if (filters.category && filters.category !== 'All') {
    q = q.eq('category', filters.category);
  }
  if (filters.isActive !== undefined) {
    q = q.eq('is_active', filters.isActive);
  }
  const { data, error } = await q;
  if (error) {
    console.warn('fetchPersons error:', error);
    return [];
  }
  return data || [];
}

export async function createPerson(personData) {
  const { data, error } = await supabase.from('persons').insert({
    code: personData.code.trim().toUpperCase(),
    name: personData.name.trim(),
    category: personData.category,
    phone: personData.phone || '',
    cnic: personData.cnic || '',
    address: personData.address || '',
    default_rate: Number(personData.default_rate || 0),
    commission_rate: Number(personData.commission_rate || 0),
    opening_payable_balance: Number(personData.opening_payable_balance || 0),
    opening_receivable_balance: Number(personData.opening_receivable_balance || 0),
    is_active: personData.is_active !== false,
    notes: personData.notes || ''
  }).select().single();
  if (error) throw error;
  return data;
}

export async function updatePerson(id, personData) {
  const { data, error } = await supabase.from('persons').update({
    code: personData.code?.trim().toUpperCase(),
    name: personData.name?.trim(),
    category: personData.category,
    phone: personData.phone,
    cnic: personData.cnic,
    address: personData.address,
    default_rate: Number(personData.default_rate || 0),
    commission_rate: Number(personData.commission_rate || 0),
    opening_payable_balance: Number(personData.opening_payable_balance || 0),
    opening_receivable_balance: Number(personData.opening_receivable_balance || 0),
    is_active: personData.is_active,
    notes: personData.notes,
    updated_at: new Date().toISOString()
  }).eq('id', id).select().single();
  if (error) throw error;
  return data;
}

export async function fetchPersonLedger(personId, dateFrom, dateTo) {
  if (!personId) return { entries: [], summary: {} };

  const { data: person, error: pErr } = await supabase.from('persons').select('*').eq('id', personId).single();
  if (pErr) throw pErr;

  let q = supabase.from('person_ledger_entries')
    .select('*, expenses(reference_number, category, head)')
    .eq('person_id', personId)
    .order('entry_date', { ascending: true });

  const { data: allEntries, error: lErr } = await q;
  if (lErr) throw lErr;

  const basePayable = Number(person.opening_payable_balance || 0);
  const baseReceivable = Number(person.opening_receivable_balance || 0);

  let priorNet = basePayable - baseReceivable;
  let workEarned = 0;
  let paid = 0;
  let commissionEarned = 0;
  let commissionPaid = 0;
  let adjustments = 0;

  const filteredEntries = [];

  (allEntries || []).forEach(e => {
    const isApproved = e.status === 'Approved';
    const isBefore = dateFrom && e.entry_date < dateFrom;
    const isAfter = dateTo && e.entry_date > dateTo;
    const amt = Number(e.amount || 0);

    let credit = 0; // Increases company liability / person credit
    let debit = 0;  // Decreases company liability / cash paid

    if (e.entry_type === 'Work_Earning') {
      credit = amt;
    } else if (e.entry_type === 'Payment' || e.entry_type === 'Advance') {
      debit = amt;
    } else if (e.entry_type === 'Commission_Earned') {
      credit = amt;
    } else if (e.entry_type === 'Commission_Paid') {
      debit = amt;
    } else if (e.entry_type === 'Adjustment' || e.entry_type === 'Opening_Balance') {
      if (e.direction === 'Receivable' || e.direction === 'Debit') {
        debit = amt;
      } else if (e.direction === 'Payable' || e.direction === 'Credit') {
        credit = amt;
      } else {
        if (amt >= 0) credit = amt; else debit = Math.abs(amt);
      }
    }

    if (isApproved) {
      if (isBefore) {
        priorNet += (credit - debit);
      } else if (!isAfter) {
        if (e.entry_type === 'Work_Earning') workEarned += amt;
        else if (e.entry_type === 'Payment' || e.entry_type === 'Advance') paid += amt;
        else if (e.entry_type === 'Commission_Earned') commissionEarned += amt;
        else if (e.entry_type === 'Commission_Paid') {
          commissionPaid += amt;
          paid += amt; // Commission cash payouts count as Total Paid
        }
        else if (e.entry_type === 'Adjustment') adjustments += (credit - debit);
      }
    }

    if (!isBefore && !isAfter) {
      filteredEntries.push({
        ...e,
        debit,
        credit,
        isApproved
      });
    }
  });

  let runningBalance = priorNet;
  const entriesWithBalance = filteredEntries.map(e => {
    if (e.isApproved) {
      runningBalance += (e.credit - e.debit);
    }
    return {
      ...e,
      balance: runningBalance
    };
  });

  const closingBalance = runningBalance;
  const closingPayable = closingBalance > 0 ? closingBalance : 0;
  const closingReceivable = closingBalance < 0 ? Math.abs(closingBalance) : 0;

  return {
    person,
    entries: entriesWithBalance,
    summary: {
      openingBalance: priorNet,
      workEarned,
      paid,
      commissionEarned,
      commissionPaid,
      adjustments,
      closingBalance,
      closingPayable,
      closingReceivable
    }
  };
}

export async function submitPersonEntry({
  personId,
  entryType,
  description,
  quantity = 0,
  rate = 0,
  amount,
  direction = null,
  paymentMethod = 'Cash',
  accountDetail = '',
  tid = '',
  notes = '',
  status = 'Approved',
  createExpense = false
}) {
  const numAmt = Math.abs(Number(amount));
  if (numAmt <= 0) throw new Error('Amount must be greater than zero.');

  const numQty = Number(quantity) || 0;
  const numRate = Number(rate) || 0;
  if (entryType === 'Work_Earning' && numQty > 0 && numRate > 0) {
    if (Math.round(numAmt * 100) !== Math.round(numQty * numRate * 100)) {
      throw new Error(`Work amount (Rs. ${numAmt}) must equal Quantity (${numQty}) × Rate (Rs. ${numRate}) = Rs. ${numQty * numRate}`);
    }
  }

  let resolvedDirection = direction;
  if (!resolvedDirection) {
    if (entryType === 'Work_Earning' || entryType === 'Commission_Earned') {
      resolvedDirection = 'Payable';
    } else if (entryType === 'Payment' || entryType === 'Advance' || entryType === 'Commission_Paid') {
      resolvedDirection = 'Receivable';
    } else if (entryType === 'Adjustment') {
      resolvedDirection = Number(amount) >= 0 ? 'Payable' : 'Receivable';
    }
  }

  // 1. Attempt atomic creation RPC first (creates ledger entry + linked expense atomically)
  try {
    const { data: rpcRes, error: rpcErr } = await supabase.rpc('create_person_ledger_entry_with_expense', {
      p_person_id: personId,
      p_entry_type: entryType,
      p_direction: resolvedDirection,
      p_amount: numAmt,
      p_description: description.trim(),
      p_quantity: numQty,
      p_rate: numRate,
      p_payment_method: paymentMethod || 'Cash',
      p_account_detail: accountDetail || '',
      p_tid: tid || '',
      p_notes: notes ? notes.trim() : '',
      p_create_expense: Boolean(createExpense),
      p_auto_approve: status === 'Approved'
    });

    if (!rpcErr && rpcRes) {
      return rpcRes;
    }
    if (rpcErr && rpcErr.code !== 'PGRST202') {
      throw rpcErr;
    }
  } catch (err) {
    if (err.code !== 'PGRST202') throw err;
  }

  // 2. Fallback for non-migrated environment: strictly Pending-first
  const { data: { session } } = await supabase.auth.getSession();
  const userId = session?.user?.id || null;
  const prefix = entryType.startsWith('Work') ? 'WRK' : entryType.startsWith('Pay') ? 'PMT' : 'ENT';
  const ref = refNum(prefix);
  const entryId = crypto.randomUUID();
  let expenseId = null;

  if (createExpense) {
    throw new Error(
      'MIGRATION REQUIRED: The create_person_ledger_entry_with_expense database function is not deployed. ' +
      'Please apply phase2_person_payments.sql to enable atomic person ledger and expense creation. ' +
      'Non-atomic split inserts are intentionally disabled to prevent orphaned financial records.'
    );
  }

  const { data, error } = await supabase.from('person_ledger_entries').insert({
    id: entryId,
    reference_number: ref,
    person_id: personId,
    entry_date: new Date().toISOString(),
    entry_type: entryType,
    direction: resolvedDirection,
    description: description.trim(),
    quantity: numQty,
    rate: numRate,
    amount: numAmt,
    payment_method: paymentMethod,
    account_detail: accountDetail,
    tid: tid,
    notes: notes ? notes.trim() : null,
    expense_id: expenseId,
    status: 'Pending',
    created_by: userId,
    approved_by: null
  }).select().single();

  if (error) throw error;

  // If immediate approval is requested and user is authorized, call the approved RPC
  if (status === 'Approved') {
    try {
      await approvePersonEntry(data.id);
      data.status = 'Approved';
    } catch (apprErr) {
      console.warn('Entry created as Pending, but auto-approval was not permitted:', apprErr.message);
    }
  }

  return data;
}

// --- DISTRIBUTOR COMMISSION SETTLEMENT ----------------------------------------

export async function fetchDistributorSettlements(distributorId = null) {
  let q = supabase.from('distributor_settlements')
    .select('*, distributors(name, code), recoveries(reference_number, amount, payment_method)')
    .order('settlement_date', { ascending: false });
  if (distributorId) q = q.eq('distributor_id', distributorId);
  const { data, error } = await q;
  if (error) {
    console.warn('fetchDistributorSettlements error:', error);
    return [];
  }
  return data || [];
}

export async function submitDistributorCommissionSettlement({
  distributorId,
  amount,
  settlementType = 'Commission_Cash_Paid',
  paymentMethod = 'Cash',
  accountDetail = '',
  tid = '',
  notes = ''
}) {
  const { data: { session } } = await supabase.auth.getSession();
  const userId = session?.user?.id || null;
  const amt = Number(amount);
  if (amt <= 0) throw new Error('Settlement amount must be greater than zero.');

  const setRef = refNum('SET');
  // 1. All settlements MUST start as Pending
  const { data: settlement, error: setErr } = await supabase.from('distributor_settlements').insert({
    reference_number: setRef,
    settlement_date: new Date().toISOString(),
    distributor_id: distributorId,
    settlement_type: settlementType,
    amount: amt,
    payment_method: paymentMethod,
    account_detail: accountDetail || null,
    tid: tid || null,
    recovery_id: null,
    notes: notes,
    status: 'Pending',
    created_by: userId
  }).select().single();

  if (setErr) throw setErr;

  // 2. Transition to Approved via controlled RPC operation
  await approveDistributorSettlement(settlement.id);
  settlement.status = 'Approved';

  if (setErr) throw setErr;

  // Audit log
  await supabase.from('audit_logs').insert({
    table_name: 'distributor_settlements',
    record_id: settlement.id,
    action: 'COMMISSION_SETTLEMENT',
    new_data: { distributor_id: distributorId, settlement_type: settlementType, amount: amt, ref: setRef, notes },
    performed_by: userId
  });

  return settlement;
}

// --- SERVER-SIDE APPROVAL & REVERSAL RPC HELPERS ------------------------------

export async function approvePersonEntry(entryId) {
  const { data, error } = await supabase.rpc('approve_person_ledger_entry', { p_entry_id: entryId });
  if (error) throw error;
  return data;
}

export async function cancelPersonEntry(entryId, reason = '') {
  const { data, error } = await supabase.rpc('cancel_person_ledger_entry', { p_entry_id: entryId, p_reason: reason });
  if (error) throw error;
  return data;
}

export async function approveDistributorSettlement(settlementId) {
  const { data, error } = await supabase.rpc('approve_distributor_settlement', { p_settlement_id: settlementId });
  if (error) throw error;
  return data;
}

export async function cancelDistributorSettlement(settlementId, reason = '') {
  const { data, error } = await supabase.rpc('cancel_distributor_settlement', { p_settlement_id: settlementId, p_reason: reason });
  if (error) throw error;
  return data;
}

export async function reconcileHistoricalSalesOrderRates(orderId, commissionRate, advertisementRate, welfareRate) {
  const { data, error } = await supabase.rpc('reconcile_historical_sales_order_rates', {
    p_order_id: orderId,
    p_commission_rate: Number(commissionRate) || 0,
    p_advertisement_rate: Number(advertisementRate) || 0,
    p_welfare_rate: Number(welfareRate) || 0
  });
  if (error) throw error;
  return data;
}



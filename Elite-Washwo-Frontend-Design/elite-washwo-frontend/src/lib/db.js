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
  const { data: salesRows } = await supabase.from('sales_orders').select('total_amount').in('status',['Approved','Posted']).gte('sale_date', monthStart.toISOString());
  const salesTotal = (salesRows||[]).reduce((s,r)=>s+Number(r.total_amount),0);

  const todayStart = new Date(); todayStart.setHours(0,0,0,0);
  const { data: recRows } = await supabase.from('recoveries').select('amount').in('status',['Approved','Posted']).gte('recovery_date', todayStart.toISOString());
  const recoveryToday = (recRows||[]).reduce((s,r)=>s+Number(r.amount),0);

  const { data: allSales } = await supabase.from('sales_orders').select('total_amount').in('status',['Approved','Posted']);
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
  let q=supabase.from('inventory_transactions').select('*, salesmen(profiles(full_name)), product_packaging(name, products(name))').order('transaction_date',{ascending:false}).limit(100);
  if(filters.salesman_id) q=q.eq('salesman_id',filters.salesman_id);
  if(filters.transaction_type) q=q.eq('transaction_type',filters.transaction_type);
  const {data,error}=await q;
  if(error) throw error;
  return data||[];
}

export async function submitStockReturn({salesmanId,packagingId,transaction_type,quantity,notes,unit_cost=0}) {
  const {error}=await supabase.from('inventory_transactions').insert({reference_number:refNum('RTN'),transaction_date:new Date().toISOString(),packaging_id:packagingId,category:transaction_type==='Salesman_Good_Return'?'Sellable Stock':'Damaged Stock',transaction_type,quantity:Number(quantity),unit_cost:Number(unit_cost),total_cost:Number(quantity)*Number(unit_cost),salesman_id:salesmanId,status:'Pending',notes});
  if(error) throw error;
}

export async function approveTransaction(id) {
  const {error}=await supabase.from('inventory_transactions').update({status:'Approved'}).eq('id',id);
  if(error) throw error;
}

// --- EXPENSES -----------------------------------------------------------------
export async function fetchExpenses(filters={}) {
  let q=supabase.from('expenses').select('*, salesmen(profiles(full_name))').order('expense_date',{ascending:false}).limit(100);
  if(filters.salesman_id) q=q.eq('salesman_id',filters.salesman_id);
  if(filters.status) q=q.eq('status',filters.status);
  const {data,error}=await q;
  if(error) throw error;
  return data||[];
}

export async function submitExpense({salesmanId,category,amount,description,paid_by,payment_method}) {
  const {error}=await supabase.from('expenses').insert({reference_number:refNum('EXP'),expense_date:new Date().toISOString(),salesman_id:salesmanId,category,amount:Number(amount),description,paid_by,payment_method,status:'Pending'});
  if(error) throw error;
}

export async function updateExpenseStatus(id,status) {
  const {error}=await supabase.from('expenses').update({status}).eq('id',id);
  if(error) throw error;
}

export async function fetchExpenseSummary() {
  const monthStart=new Date();monthStart.setDate(1);monthStart.setHours(0,0,0,0);
  const {data}=await supabase.from('expenses').select('amount,status,paid_by').gte('expense_date',monthStart.toISOString());
  const total=(data||[]).reduce((s,r)=>s+Number(r.amount),0);
  const pending=(data||[]).filter(r=>['Pending','Submitted'].includes(r.status)).reduce((s,r)=>s+Number(r.amount),0);
  const company=(data||[]).filter(r=>r.paid_by==='Company').reduce((s,r)=>s+Number(r.amount),0);
  const salesman=total-company;
  return {total,pending,company,salesman,companyPct:total?Math.round(company/total*100):0};
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
    if(r.transaction_type==='Production')s.production+=r.quantity;
    if(r.transaction_type==='Salesman_Issue')s.salesman_issues+=r.quantity;
    if(['Salesman_Good_Return','Salesman_Damaged_Return'].includes(r.transaction_type))s.salesman_returns+=r.quantity;
    if(['Customer_Good_Return','Customer_Damaged_Return'].includes(r.transaction_type))s.customer_returns+=r.quantity;
    if(r.transaction_type==='Damage')s.damaged+=r.quantity;
    if(r.transaction_type==='Adjustment')s.adjustments+=r.quantity;
  });
  s.closing=s.production-s.salesman_issues+s.salesman_returns+s.customer_returns-s.damaged+s.adjustments;
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
  const { data: salesmen, error: sErr } = await supabase.from('salesmen').select('id, code, profiles(full_name)');
  if (sErr) throw sErr;

  const results = [];
  for (const sm of (salesmen || [])) {
    const { data: ts } = await supabase.from('sales_orders').select('total_amount').eq('salesman_id', sm.id).in('status', ['Approved', 'Posted']).gte('sale_date', closingDate);
    const salesAmt = (ts || []).reduce((s, r) => s + Number(r.total_amount), 0);

    const { data: tr } = await supabase.from('recoveries').select('amount').eq('salesman_id', sm.id).in('status', ['Approved', 'Posted']).gte('recovery_date', closingDate);
    const recAmt = (tr || []).reduce((s, r) => s + Number(r.amount), 0);

    const { data: stockRows } = await supabase.from('inventory_transactions').select('quantity, transaction_type').eq('salesman_id', sm.id).in('status', ['Approved', 'Posted']);
    let currentStock = 0;
    (stockRows || []).forEach(r => {
      if (r.transaction_type === 'Salesman_Issue') currentStock += r.quantity;
      if (['Sale', 'Salesman_Good_Return', 'Salesman_Damaged_Return'].includes(r.transaction_type)) currentStock -= r.quantity;
    });

    const expectedCash = recAmt;
    const submittedCash = recAmt;

    const { data: closing, error: cErr } = await supabase.from('daily_closings').upsert({
      closing_date: closingDate,
      salesman_id: sm.id,
      expected_cash: expectedCash,
      submitted_cash: submittedCash,
      expected_stock: { packets: currentStock },
      submitted_stock: { packets: currentStock },
      status: 'Approved'
    }, { onConflict: 'closing_date,salesman_id' }).select().single();

    if (cErr) console.warn('Closing notice for ' + sm.code, cErr);
    else results.push(closing);
  }

  return { success: true, count: results.length };
}

export async function fetchDailyClosingReport(filters = {}) {
  let q = supabase.from('daily_closings').select('*, salesmen(code, route, profiles(full_name))').order('closing_date', { ascending: false });
  if (filters.startDate) q = q.gte('closing_date', filters.startDate);
  if (filters.endDate) q = q.lte('closing_date', filters.endDate);
  if (filters.salesmanId) q = q.eq('salesman_id', filters.salesmanId);
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

export async function submitSale({ salesmanId, customerId, items, totalAmount }) {
  const { data: user } = await supabase.auth.getUser();
  const { data: profile } = await supabase.from('profiles').select('full_name').eq('id', user.user?.id).single();
  const created_by = profile?.full_name || 'System';

  const { data: order, error: orderErr } = await supabase.from('sales_orders').insert({
    salesman_id: salesmanId,
    customer_id: customerId,
    total_amount: totalAmount,
    sale_date: new Date().toISOString(),
    status: 'Approved',
    created_by
  }).select().single();
  
  if (orderErr) throw orderErr;

  const saleItems = items.map(item => ({
    sales_order_id: order.id,
    product_packaging_id: item.packagingId,
    quantity: item.quantity,
    unit_price: item.price
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

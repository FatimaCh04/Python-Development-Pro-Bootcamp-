with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

# Add fetchSales function if not present
if 'export async function fetchSales' not in c:
    appendStr = '''

// ── Sales (SAL- records) with distributor + filters ──────────────────────────
export async function fetchSales({ dateFrom, dateTo, distributorId } = {}) {
  let q = supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, status, customer_id, salesman_id, distributor_id, customers(name, code), salesmen(profiles(full_name)), distributors(id, code, name, id_card, phone), sale_items(quantity, unit_price, subtotal, packaging_id, product_packaging:packaging_id(name, product_id))')
    .like('reference_number', 'SAL-%')
    .order('sale_date', { ascending: false });
  if (dateFrom) q = q.gte('sale_date', dateFrom);
  if (dateTo)   q = q.lte('sale_date', dateTo);
  if (distributorId) q = q.eq('distributor_id', distributorId);
  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

// ── Distributor Outstanding (Sales total - Recoveries total) ─────────────────
export async function fetchDistributorOutstanding(distributorId) {
  if (!distributorId) return 0;
  const { data: sales }     = await supabase.from('sales_orders').select('total_amount').eq('distributor_id', distributorId).in('status', ['Approved', 'Posted']);
  const { data: recoveries } = await supabase.from('recoveries').select('amount').eq('distributor_id', distributorId).in('status', ['Approved', 'Posted']);
  const totalSales     = (sales     || []).reduce((s, r) => s + Number(r.total_amount), 0);
  const totalRecovered = (recoveries || []).reduce((s, r) => s + Number(r.amount), 0);
  return Math.max(0, totalSales - totalRecovered);
}

// ── Distributor today's recovery ─────────────────────────────────────────────
export async function fetchDistributorTodayRecovery(distributorId) {
  if (!distributorId) return 0;
  const todayStart = new Date(); todayStart.setHours(0,0,0,0);
  const { data } = await supabase.from('recoveries').select('amount').eq('distributor_id', distributorId).gte('recovery_date', todayStart.toISOString()).in('status', ['Approved', 'Posted']);
  return (data || []).reduce((s, r) => s + Number(r.amount), 0);
}
'''
    c = c + appendStr
    with open('src/lib/db.js', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Added fetchSales, fetchDistributorOutstanding, fetchDistributorTodayRecovery')
else:
    print('fetchSales already exists')

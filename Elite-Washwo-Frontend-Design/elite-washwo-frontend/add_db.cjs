const fs = require('fs');
let content = fs.readFileSync('src/lib/db.js', 'utf8');

const bookingFns = `
export async function submitBooking({ salesmanId, customerId, items, totalAmount }) {
  const ref = refNum('BKG');
  const { data: order, error: orderErr } = await supabase.from('sales_orders').insert({
    reference_number: ref,
    salesman_id: salesmanId,
    customer_id: customerId,
    total_amount: totalAmount,
    sale_date: new Date().toISOString(),
    status: 'Pending'
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

export async function fetchBookings() {
  const { data, error } = await supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, status, customers(name), salesmen(profiles(full_name))')
    .like('reference_number', 'BKG-%')
    .order('sale_date', { ascending: false });
  if (error) throw error;
  
  const { data: recs, error: rErr } = await supabase
    .from('recoveries')
    .select('amount, reference_number')
    .like('reference_number', '%|BKG-%');
    
  if (rErr) throw rErr;

  return data.map(b => {
    const bookingRecs = recs.filter(r => r.reference_number.endsWith('|' + b.id));
    const totalRecovered = bookingRecs.reduce((sum, r) => sum + Number(r.amount), 0);
    return {
      ...b,
      total_recovered: totalRecovered,
      remaining_balance: Number(b.total_amount) - totalRecovered
    };
  });
}

export async function addBookingRecovery({ bookingId, customerId, salesmanId, amount, paymentMethod }) {
  const ref = refNum('REC') + '|' + bookingId;
  const { error } = await supabase.from('recoveries').insert({
    reference_number: ref,
    salesman_id: salesmanId,
    customer_id: customerId,
    amount: Number(amount),
    payment_method: paymentMethod,
    recovery_date: new Date().toISOString(),
    status: 'Approved'
  });
  if (error) throw error;
}
`;

content = content + '\n' + bookingFns;
fs.writeFileSync('src/lib/db.js', content, 'utf8');
console.log('Added booking functions to db.js');

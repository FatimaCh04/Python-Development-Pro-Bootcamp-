content = open("src/lib/db.js", "r", encoding="utf-8", errors="ignore").read()

if "submitSale" not in content:
    func = """
export async function submitSale({ salesmanId, customerId, items, totalAmount }) {
  const { data: user } = await supabase.auth.getUser();
  const { data: profile } = await supabase.from('profiles').select('full_name').eq('id', user.user?.id).single();
  const created_by = profile?.full_name || 'System';

  const { data: order, error: orderErr } = await supabase.from('sales_orders').insert({
    salesman_id: salesmanId,
    customer_id: customerId,
    total_amount: totalAmount,
    sale_date: new Date().toISOString(),
    status: 'Pending',
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
"""
    content += func
    open("src/lib/db.js", "w", encoding="utf-8").write(content)
    print("Added submitSale")

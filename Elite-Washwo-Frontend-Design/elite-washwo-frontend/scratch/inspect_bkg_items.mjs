import { createClient } from '@supabase/supabase-js';

const url = 'https://vcisakapfzpqziwjyfni.supabase.co';
const anonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjaXNha2FwZnpwcXppd2p5Zm5pIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAwODI3MjcsImV4cCI6MjEwNTY1ODcyN30.wLFJEupXYpj3hakWECI2XplRJTTuhcKsDdZAD_PgwJ8';

const supabase = createClient(url, anonKey);

async function inspect() {
  const { data, error } = await supabase
    .from('sales_orders')
    .select('id, reference_number, sale_date, total_amount, status, distributor_id, distributors(name, code), sale_items(id, quantity, unit_price, subtotal, packaging_id)')
    .like('reference_number', 'BKG-%')
    .order('sale_date', { ascending: true });

  if (error) {
    console.error('Error fetching bookings:', error);
    return;
  }

  console.log(`Found ${data.length} bookings:`);
  for (const b of data) {
    const items = b.sale_items || [];
    const pkts = items.reduce((sum, i) => sum + Number(i.quantity || 0), 0);
    const dist = b.distributors ? `${b.distributors.name} (${b.distributors.code})` : 'NULL';
    console.log(`[${b.reference_number}] Date: ${b.sale_date} | Dist: ${dist} | Status: ${b.status} | Value: Rs. ${b.total_amount} | Items: ${items.length} | Packets: ${pkts}`);
    if (items.length === 0) {
      console.log(`   *** WARNING: Booking has 0 sale_items rows! ID: ${b.id}`);
    } else {
      for (const item of items) {
        console.log(`       - ${item.quantity} pkts @ Rs. ${item.unit_price} = Rs. ${item.subtotal} (pkg_id: ${item.packaging_id})`);
      }
    }
  }
}

inspect();

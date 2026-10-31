import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://vcisakapfzpqziwjyfni.supabase.co';
const SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjaXNha2FwZnpwcXppd2p5Zm5pIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MDA4MjcyNywiZXhwIjoyMTA1NjU4NzI3fQ.0rNZ3TJurI_kIsJdkloZ1y3qHPtWZntq_o-d9Sd9XP0';

const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false }
});

async function inspectCustomerDependencies() {
  console.log("======================================================================");
  console.log("INSPECTING LIVE DATABASE SCHEMA FOR CUSTOMER MODULE DEPENDENCIES");
  console.log("======================================================================");

  // 1. Check if public.customers exists and get row count
  const { data: custRows, error: custErr } = await supabase
    .from('customers')
    .select('*');
  if (custErr) {
    console.log("public.customers table error:", custErr.message);
  } else {
    console.log(`public.customers exists! Total rows: ${custRows.length}`);
    console.table(custRows);
  }

  // 2. Check if customer_ledger exists
  const { data: ledgerRows, error: ledgerErr } = await supabase
    .from('customer_ledger')
    .select('*');
  if (ledgerErr) {
    console.log("customer_ledger query error:", ledgerErr.message);
  } else {
    console.log(`customer_ledger exists! Total rows: ${ledgerRows.length}`);
    console.table(ledgerRows);
  }

  // 3. Check customer_id in sales_orders
  const { data: soCust, error: soErr } = await supabase
    .from('sales_orders')
    .select('id, reference_number, customer_id')
    .not('customer_id', 'is', null);
  console.log(`sales_orders with non-null customer_id: ${soCust?.length || 0}`);
  if (soCust?.length) console.table(soCust);

  // 4. Check customer_id in recoveries
  const { data: recCust, error: recErr } = await supabase
    .from('recoveries')
    .select('id, reference_number, customer_id')
    .not('customer_id', 'is', null);
  console.log(`recoveries with non-null customer_id: ${recCust?.length || 0}`);
  if (recCust?.length) console.table(recCust);

  // 5. Check customer_id in inventory_transactions
  const { data: invCust, error: invErr } = await supabase
    .from('inventory_transactions')
    .select('id, customer_id')
    .not('customer_id', 'is', null);
  console.log(`inventory_transactions with non-null customer_id: ${invCust?.length || 0}`);
  if (invCust?.length) console.table(invCust);
}

inspectCustomerDependencies().catch(console.error);

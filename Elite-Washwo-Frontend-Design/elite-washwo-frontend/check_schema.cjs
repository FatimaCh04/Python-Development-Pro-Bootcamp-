const { createClient } = require('@supabase/supabase-js');
const sb = createClient('https://vcisakapfzpqziwjyfni.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjaXNha2FwZnpwcXppd2p5Zm5pIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MDA4MjcyNywiZXhwIjoyMTA1NjU4NzI3fQ.0rNZ3TJurI_kIsJdkloZ1y3qHPtWZntq_o-d9Sd9XP0');

async function run() {
  const { data, error } = await sb.from('expenses').select('id, salesman_id, description, account_detail, tid, head').limit(1);
  if (error) console.error('Error:', error);
  console.log('Columns retrieved:', data ? Object.keys(data[0]) : null);
  
  // Test insert with null salesman_id
  const { error: insErr } = await sb.from('expenses').insert({ 
    reference_number: 'TEST_COL_CHK', 
    expense_date: new Date().toISOString(),
    amount: 1, 
    category: 'Company',
    salesman_id: null 
  });
  console.log('Insert error with null salesman_id:', insErr?.message || 'Success');
}
run();

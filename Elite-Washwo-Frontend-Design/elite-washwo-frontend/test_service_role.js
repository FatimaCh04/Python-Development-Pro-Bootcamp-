import { createClient } from '@supabase/supabase-js';
import fs from 'fs';

const env = {};
fs.readFileSync('.env', 'utf-8').split('\n').forEach(line => {
  if (line.includes('=')) {
    const [k, v] = line.trim().split('=');
    env[k] = v;
  }
});

const supabase = createClient(env.VITE_SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);

async function run() {
  const { data: pkgs } = await supabase.from('product_packaging').select('id').limit(1);
  const packaging_id = pkgs[0]?.id;

  const { data: dists } = await supabase.from('distributors').select('id').limit(1);
  const distributor_id = dists[0]?.id;

  if (!packaging_id) return console.log('No packaging found');

  const payload = {
    reference_number: 'TEST-RTN-2',
    transaction_date: new Date().toISOString(),
    packaging_id: packaging_id,
    category: 'Damaged Stock',
    transaction_type: 'Salesman_Damaged_Return', // Or Distributor_Damaged_Return if it exists
    quantity: 1,
    unit_cost: 0,
    total_cost: 0,
    salesman_id: null,
    distributor_id: distributor_id,
    status: 'Pending',
    notes: 'test'
  };

  const { data, error } = await supabase.from('inventory_transactions').insert(payload);
  console.log('Insert with service_role:', error ? error : 'Success');
}
run();

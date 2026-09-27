import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config();

const supabase = createClient(process.env.VITE_SUPABASE_URL, process.env.VITE_SUPABASE_ANON_KEY);

async function run() {
  const { data: { session }, error: authErr } = await supabase.auth.signInWithPassword({
    email: 'admin@elitewashwo.com', // guess email or I will fetch token? I don't know the password...
    password: 'password123'
  });
  console.log('auth:', session ? 'ok' : authErr);
}
run();

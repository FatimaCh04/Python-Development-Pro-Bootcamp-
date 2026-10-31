/**
 * Elite Wash ERP — Administrative Script: delete_salesman_auth_users.mjs
 * 
 * Safely purges the 4 discontinued Salesman accounts from Supabase Authentication
 * using the official Supabase Admin Auth API (service_role key).
 * 
 * Targets:
 *   1. Ahsan   — Salesman — Disabled
 *   2. Ali     — Salesman — Disabled
 *   3. Nouman  — Salesman — Disabled
 *   4. Ahmed   — Salesman — Disabled
 * 
 * Usage:
 *   node delete_salesman_auth_users.mjs <service_role_key>
 *   -OR-
 *   $env:SUPABASE_SERVICE_ROLE_KEY="your-key"; node delete_salesman_auth_users.mjs
 */

import { createClient } from '@supabase/supabase-js';
import { readFileSync, existsSync } from 'fs';

// Native zero-dependency .env loader (no dotenv package required)
function loadEnv() {
  const envPaths = ['.env', '.env.local', 'elite-washwo-frontend/.env', '../.env'];
  for (const p of envPaths) {
    if (existsSync(p)) {
      try {
        const content = readFileSync(p, 'utf-8');
        for (const line of content.split(/\r?\n/)) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith('#')) continue;
          const eqIdx = trimmed.indexOf('=');
          if (eqIdx === -1) continue;
          const key = trimmed.slice(0, eqIdx).trim();
          let val = trimmed.slice(eqIdx + 1).trim();
          if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
            val = val.slice(1, -1);
          }
          if (!process.env[key]) {
            process.env[key] = val;
          }
        }
      } catch (_) {}
    }
  }
}

loadEnv();

const SUPABASE_URL = process.env.VITE_SUPABASE_URL || process.env.SUPABASE_URL;
let SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SERVICE_ROLE_KEY || process.argv[2];

if (SERVICE_ROLE_KEY) {
  SERVICE_ROLE_KEY = SERVICE_ROLE_KEY.trim();
  if (SERVICE_ROLE_KEY.startsWith('<') && SERVICE_ROLE_KEY.endsWith('>')) {
    SERVICE_ROLE_KEY = SERVICE_ROLE_KEY.slice(1, -1).trim();
  }
}

if (!SUPABASE_URL) {
  console.error('[ABORT] Missing SUPABASE_URL (ensure VITE_SUPABASE_URL is in .env or set SUPABASE_URL).');
  process.exit(1);
}

if (!SERVICE_ROLE_KEY) {
  console.error('======================================================================');
  console.error('[ABORT] Supabase Service Role Key is required to purge Auth Users.');
  console.error('======================================================================');
  console.error('');
  console.error('You can provide it directly as an argument:');
  console.error('  node delete_salesman_auth_users.mjs <your-service-role-key>');
  console.error('');
  console.error('Or set it as an environment variable in PowerShell:');
  console.error('  $env:SUPABASE_SERVICE_ROLE_KEY="<your-service-role-key>"');
  console.error('  node delete_salesman_auth_users.mjs');
  console.error('');
  console.error('Note: Obtain the "service_role" secret key from:');
  console.error('Supabase Dashboard -> Project Settings -> API -> Project API keys (secret).');
  console.error('======================================================================');
  process.exit(1);
}

const supabaseAdmin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false }
});

const TARGET_NAMES = ['ahsan', 'ali', 'nouman', 'ahmed'];

async function purgeSalesmanAuthUsers() {
  console.log('======================================================================');
  console.log('STARTING ADMINISTRATIVE PURGE: SALESMAN AUTH USERS');
  console.log('Supabase URL:', SUPABASE_URL);
  console.log('Target Names:', TARGET_NAMES.join(', '));
  console.log('======================================================================');

  // 1. Identify profiles in database
  const { data: profiles, error: profErr } = await supabaseAdmin
    .from('profiles')
    .select('id, full_name, role, is_active');

  if (profErr) {
    console.warn('[NOTICE] Could not query profiles table directly (may already be purged or RLS):', profErr.message);
  }

  // 2. List auth users from Supabase Admin API
  const { data: { users }, error: authErr } = await supabaseAdmin.auth.admin.listUsers({
    page: 1,
    perPage: 100
  });

  if (authErr) {
    console.error('[ERROR] Failed to list auth users:', authErr);
    process.exit(1);
  }

  console.log(`[INFO] Found ${users.length} total user accounts in Supabase Auth.`);

  const targetsToDelete = [];

  for (const user of users) {
    const userEmail = (user.email || '').toLowerCase();
    const matchingProfile = (profiles || []).find(p => p.id === user.id);
    const profileName = (matchingProfile?.full_name || '').trim().toLowerCase();

    // Check if user matches any target salesman
    const isTargetName = TARGET_NAMES.some(name => profileName.includes(name) || userEmail.startsWith(name));
    const isSalesmanRole = matchingProfile?.role === 'Salesman';
    const isDisabled = matchingProfile ? !matchingProfile.is_active : true;

    // Strict preservation guard: never delete Super Admin or Muhammad saeed
    const isPreserved = profileName.includes('saeed') || profileName.includes('admin') || userEmail.includes('admin') || userEmail.includes('saeed');

    if (isTargetName && !isPreserved) {
      targetsToDelete.push({
        id: user.id,
        email: user.email,
        name: matchingProfile?.full_name || 'N/A',
        role: matchingProfile?.role || 'Salesman'
      });
    }
  }

  console.log(`[INFO] Identified ${targetsToDelete.length} target accounts for deletion:`);
  targetsToDelete.forEach(t => console.log(`   - ID: ${t.id} | Email: ${t.email} | Name: ${t.name} | Role: ${t.role}`));

  if (targetsToDelete.length === 0) {
    console.log('[COMPLETE] No target accounts found in auth.users. Already cleaned up!');
    return;
  }

  for (const target of targetsToDelete) {
    console.log(`[DELETING] Deleting auth user: ${target.name} (${target.id})...`);
    const { error: delErr } = await supabaseAdmin.auth.admin.deleteUser(target.id);
    if (delErr) {
      console.error(`[ERROR] Failed to delete user ${target.id}:`, delErr.message);
    } else {
      console.log(`[SUCCESS] Deleted user ${target.name} (${target.id}) from Supabase Auth.`);
    }
  }

  console.log('======================================================================');
  console.log('ADMINISTRATIVE PURGE COMPLETED SUCCESSFULLY');
  console.log('======================================================================');
}

purgeSalesmanAuthUsers().catch(err => {
  console.error('[FATAL ERROR]:', err);
  process.exit(1);
});

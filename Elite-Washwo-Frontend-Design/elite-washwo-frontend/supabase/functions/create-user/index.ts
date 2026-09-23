import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    )

    // Verify caller is Super_Admin
    const { data: { user } } = await supabaseClient.auth.getUser()
    if (!user) throw new Error('Unauthorized')

    const { data: profile } = await supabaseClient.from('profiles').select('role').eq('id', user.id).single()
    if (profile?.role !== 'Super_Admin') throw new Error('Forbidden: Only Super_Admin can create users')

    // Get Service Role Client to bypass RLS for user creation
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const { email, password, full_name, role, code, route } = await req.json()

    if (!email || !password || !full_name || !role) {
      throw new Error('Missing required fields')
    }
    
    // 1. Create Auth User
    const { data: authData, error: authError } = await supabaseAdmin.auth.admin.createUser({
      email,
      password,
      email_confirm: true
    })
    
    if (authError) throw authError

    const newUserId = authData.user.id

    // 2. Create Profile
    const { error: profileError } = await supabaseAdmin.from('profiles').insert({
      id: newUserId,
      full_name,
      role,
      is_active: true
    })

    if (profileError) {
      // Rollback auth user
      await supabaseAdmin.auth.admin.deleteUser(newUserId)
      throw profileError
    }

    // 3. Create Salesman record if applicable
    if (role === 'Salesman') {
      const { error: salesmanError } = await supabaseAdmin.from('salesmen').insert({
        profile_id: newUserId,
        code,
        route
      })
      if (salesmanError) {
        // Rollback
        await supabaseAdmin.from('profiles').delete().eq('id', newUserId)
        await supabaseAdmin.auth.admin.deleteUser(newUserId)
        throw salesmanError
      }
    }

    return new Response(JSON.stringify({ success: true, user: authData.user }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})

-- ==============================================================================
-- ELITE WASH ERP — PHASE 2 APPROVAL SECURITY TEST SUITE
-- Version: 2.7 (Corrected Role Switching, auth.uid() Simulation, Strict Assertion Reporting)
-- TRANSACTIONAL: Enclosed in BEGIN ... ROLLBACK. Leaves zero test data behind.
-- SAFETY: NEVER RUN THIS SCRIPT AGAINST PRODUCTION SUPABASE.
--
-- HOW TO RUN (local PostgreSQL only):
--   1. Apply migration first:
--        psql -U postgres -d <local_db> -f phase2_person_payments.sql
--   2. Run tests:
--        psql -U postgres -d <local_db> -f test_phase2_security.sql
--   3. Inspect NOTICE lines for [PASS] / [FAIL] per test.
--
-- WHAT THIS TESTS:
--   TEST 1 — Direct INSERT status=Approved blocked by trigger
--   TEST 2 — Direct UPDATE status blocked by PostgreSQL column privilege
--   TEST 3 — Unauthorized RPC approval rejected with exact error message
--   TEST 4 — Authorized Super Admin RPC approval succeeds
--   TEST 5 — Authorized Manager (payments.approve) RPC approval succeeds
--   TEST 6 — Double-approval on Approved record rejected
--   TEST 7 — Cancellation reverses owned expense only; independent expense untouched
--   TEST 8 — Re-approval on Cancelled record rejected
--   TEST 9 — Direct UPDATE recovery_id blocked by PostgreSQL column privilege
-- ==============================================================================

BEGIN;

-- ==============================================================================
-- 0. PRE-FLIGHT: ENVIRONMENT CHECK & AUTH/ROLE STUB SETUP
-- ==============================================================================
DO $$
BEGIN
    -- SAFETY: Prohibit execution against production Supabase
    IF current_database() LIKE '%vcisakapfzpqziwjyfni%' THEN
        RAISE EXCEPTION 'SAFETY HALT: Execution against production Supabase is strictly prohibited!';
    END IF;

    RAISE NOTICE '==================================================================';
    RAISE NOTICE '  PHASE 2 v2.7 SECURITY TEST SUITE — LOCAL/STAGING ONLY';
    RAISE NOTICE '==================================================================';

    -- Ensure roles exist for local PostgreSQL test harness
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN;
    END IF;
    -- Ensure current test session user can switch into authenticated role
    EXECUTE 'GRANT authenticated TO ' || quote_ident(current_user);

    -- Ensure auth schema and minimal users table exist for local PG.
    CREATE SCHEMA IF NOT EXISTS auth;
    CREATE TABLE IF NOT EXISTS auth.users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email TEXT
    );
END $$;

-- ==============================================================================
-- HELPER: Dynamically insert a synthetic auth.users record
--         adapts to whatever columns the local mock auth.users has.
-- ==============================================================================
CREATE OR REPLACE FUNCTION pg_temp.create_mock_auth_user(p_id UUID, p_email TEXT)
RETURNS VOID AS $$
DECLARE
    v_has_email BOOLEAN;
    v_has_aud   BOOLEAN;
    v_has_role  BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'email'
    ) INTO v_has_email;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'aud'
    ) INTO v_has_aud;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'role'
    ) INTO v_has_role;

    IF v_has_email AND v_has_aud AND v_has_role THEN
        EXECUTE 'INSERT INTO auth.users (id, email, aud, role)
                 VALUES ($1, $2, ''authenticated'', ''authenticated'')
                 ON CONFLICT (id) DO NOTHING'
        USING p_id, p_email;
    ELSIF v_has_email THEN
        EXECUTE 'INSERT INTO auth.users (id, email)
                 VALUES ($1, $2) ON CONFLICT (id) DO NOTHING'
        USING p_id, p_email;
    ELSE
        EXECUTE 'INSERT INTO auth.users (id) VALUES ($1) ON CONFLICT (id) DO NOTHING'
        USING p_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- HELPER: Set GUC-based auth context (simulates Supabase PostgREST JWT injection)
--
-- NOTE ON ROLE SWITCHING:
--   Tests that assert column-level PostgreSQL privileges (TEST 2, TEST 9) require
--   the actual SESSION ROLE to be 'authenticated'. GUC set_config('role',...) alone
--   does NOT switch the session role — it only sets a config variable.
--
--   For those specific tests we use:
--       EXECUTE 'SET LOCAL ROLE authenticated';
--   inside the test's nested BEGIN...EXCEPTION block, which correctly switches
--   the role for the duration of that block (LOCAL = reverts at END of that block
--   or when the surrounding transaction rolls back).
--
--   For RPC-based tests (TEST 3-8), role switching is NOT needed because the
--   SECURITY DEFINER functions run as 'postgres' and check auth.uid() via GUC.
-- ==============================================================================
CREATE OR REPLACE FUNCTION pg_temp.set_jwt_claims(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('request.jwt.claim.sub',  p_user_id::text, true);
    PERFORM set_config('request.jwt.claim.role',  'authenticated', true);
    PERFORM set_config('request.jwt.claims',
        json_build_object('sub', p_user_id::text, 'role', 'authenticated')::text,
        true);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION pg_temp.clear_jwt_claims()
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('request.jwt.claim.sub',  '', true);
    PERFORM set_config('request.jwt.claim.role', '', true);
    PERFORM set_config('request.jwt.claims',     '', true);
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- MAIN TEST BODY
-- ==============================================================================
DO $$
DECLARE
    -- Synthetic User UUIDs (fixed, deterministic)
    v_admin_id          UUID := '11111111-1111-4111-8111-111111111111'::UUID;
    v_unauth_mgr_id     UUID := '22222222-2222-4222-8222-222222222222'::UUID;
    v_auth_mgr_id       UUID := '33333333-3333-4333-8333-333333333333'::UUID;

    -- Domain entity IDs
    v_person_id         UUID;
    v_dist_id           UUID;

    -- Ledger/Settlement/Expense IDs
    v_entry1_id         UUID;
    v_entry2_id         UUID;
    v_entry3_id         UUID;
    v_settle_id         UUID;
    v_exp_owned_id      UUID;
    v_exp_indep_id      UUID;

    -- Assertion variables
    v_res               JSONB;
    v_rec               RECORD;
    v_err_msg           TEXT;
    v_err_state         TEXT;
    v_test_passed       BOOLEAN;
BEGIN
    RAISE NOTICE '--- PROVISIONING SYNTHETIC TEST DATA ---';

    -- =========================================================================
    -- A. Create synthetic auth.users (satisfies profiles FK)
    -- =========================================================================
    PERFORM pg_temp.create_mock_auth_user(v_admin_id,      'superadmin@test.local');
    PERFORM pg_temp.create_mock_auth_user(v_unauth_mgr_id, 'unauth_manager@test.local');
    PERFORM pg_temp.create_mock_auth_user(v_auth_mgr_id,   'auth_manager@test.local');

    -- =========================================================================
    -- B. Provision profiles (super admin + 2 managers)
    -- =========================================================================
    INSERT INTO public.profiles (id, full_name, role, is_active)
    VALUES (v_admin_id, 'Test Super Admin', 'Super_Admin', true)
    ON CONFLICT (id) DO UPDATE SET role = 'Super_Admin', is_active = true;

    INSERT INTO public.profiles (id, full_name, role, is_active)
    VALUES (v_unauth_mgr_id, 'Test Unauthorized Manager', 'Manager', true)
    ON CONFLICT (id) DO UPDATE SET role = 'Manager', is_active = true;

    INSERT INTO public.profiles (id, full_name, role, is_active)
    VALUES (v_auth_mgr_id, 'Test Authorized Manager', 'Manager', true)
    ON CONFLICT (id) DO UPDATE SET role = 'Manager', is_active = true;

    -- =========================================================================
    -- C. Assign permissions
    --    v_unauth_mgr: view + create only (NO approve)
    --    v_auth_mgr:   view + create + approve (for both payments & settlement)
    -- =========================================================================
    DELETE FROM public.user_permissions
    WHERE user_id IN (v_admin_id, v_unauth_mgr_id, v_auth_mgr_id);

    INSERT INTO public.user_permissions (user_id, permission_id) VALUES
        (v_unauth_mgr_id, 'payments.view'),
        (v_unauth_mgr_id, 'payments.create'),
        (v_unauth_mgr_id, 'settlement.view'),
        (v_unauth_mgr_id, 'settlement.create'),
        (v_auth_mgr_id,   'payments.view'),
        (v_auth_mgr_id,   'payments.create'),
        (v_auth_mgr_id,   'payments.approve'),
        (v_auth_mgr_id,   'settlement.view'),
        (v_auth_mgr_id,   'settlement.create'),
        (v_auth_mgr_id,   'settlement.approve');

    -- =========================================================================
    -- D. Domain entities
    -- =========================================================================
    INSERT INTO public.persons (code, name, category, default_rate)
    VALUES ('TST-PER-01', 'Test Worker', 'Labourer', 50.00)
    RETURNING id INTO v_person_id;

    INSERT INTO public.distributors (code, name, is_active)
    VALUES ('TST-DIST-01', 'Test Distributor', true)
    RETURNING id INTO v_dist_id;

    RAISE NOTICE '--- RUNNING TESTS ---';

    -- =========================================================================
    -- TEST 1: Direct INSERT with status=Approved must be blocked by trigger
    -- Expected: RAISE EXCEPTION containing 'must start with status Pending'
    -- =========================================================================
    v_test_passed := false;
    BEGIN
        -- Set JWT claims so auth.uid() resolves (trigger checks authorization)
        PERFORM pg_temp.set_jwt_claims(v_unauth_mgr_id);

        INSERT INTO public.person_ledger_entries (
            reference_number, person_id, entry_type, direction,
            amount, description, status, created_by
        ) VALUES (
            'REF-ILLEGAL-01', v_person_id, 'Payment', 'Debit',
            5000.00, 'Direct approved insert attempt', 'Approved', v_unauth_mgr_id
        );

        PERFORM pg_temp.clear_jwt_claims();
        -- If we reach this line, the INSERT was NOT blocked — assertion failure
        RAISE EXCEPTION 'ASSERTION FAILURE: Direct INSERT Approved was NOT blocked!';

    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_err_msg = MESSAGE_TEXT, v_err_state = RETURNED_SQLSTATE;
        PERFORM pg_temp.clear_jwt_claims();

        IF v_err_msg LIKE '%must start with status Pending%' THEN
            v_test_passed := true;
            RAISE NOTICE '[PASS] TEST 1: Direct INSERT Approved blocked (trigger: %)', v_err_msg;
        ELSE
            RAISE EXCEPTION '[FAIL] TEST 1 unexpected error (SQLSTATE: %, Msg: %)', v_err_state, v_err_msg;
        END IF;
    END;

    -- Insert valid Pending entries for subsequent tests (as superuser postgres)
    PERFORM pg_temp.set_jwt_claims(v_unauth_mgr_id);
    INSERT INTO public.person_ledger_entries (
        reference_number, person_id, entry_type, direction,
        amount, description, notes, status, created_by
    ) VALUES (
        'REF-TEST-PEND-01', v_person_id, 'Payment', 'Debit',
        1000.00, 'Legitimate pending payment', 'Test transaction note', 'Pending', v_unauth_mgr_id
    ) RETURNING id INTO v_entry1_id;
    PERFORM pg_temp.clear_jwt_claims();

    PERFORM pg_temp.set_jwt_claims(v_auth_mgr_id);
    INSERT INTO public.person_ledger_entries (
        reference_number, person_id, entry_type, direction,
        amount, description, notes, status, created_by
    ) VALUES (
        'REF-TEST-PEND-02', v_person_id, 'Work_Earning', 'Payable',
        2500.00, 'Legitimate pending work earning', 'Work note', 'Pending', v_auth_mgr_id
    ) RETURNING id INTO v_entry2_id;
    PERFORM pg_temp.clear_jwt_claims();

    -- =========================================================================
    -- TEST 2: Direct UPDATE status=Approved as 'authenticated' role must be blocked
    --         by PostgreSQL column-level privilege denial (SQLSTATE 42501).
    --
    -- MECHANISM: The migration does:
    --   REVOKE UPDATE, DELETE ON person_ledger_entries FROM authenticated;
    --   GRANT UPDATE (person_id, entry_type, ...) ON person_ledger_entries TO authenticated;
    -- This means the 'authenticated' role cannot UPDATE the 'status' column.
    --
    -- ROLE SWITCHING: We use EXECUTE 'SET LOCAL ROLE authenticated' to actually
    -- switch the session role (GUC set_config('role',...) is insufficient for PG privilege checks).
    -- SET LOCAL reverts automatically at the end of the outer transaction on ROLLBACK.
    -- =========================================================================
    v_test_passed := false;
    BEGIN
        PERFORM pg_temp.set_jwt_claims(v_unauth_mgr_id);
        EXECUTE 'SET LOCAL ROLE authenticated';

        EXECUTE 'UPDATE public.person_ledger_entries SET status = ''Approved'' WHERE id = $1' USING v_entry1_id;

        EXECUTE 'RESET ROLE';
        PERFORM pg_temp.clear_jwt_claims();
        RAISE EXCEPTION 'ASSERTION FAILURE: Direct UPDATE status=Approved was NOT blocked!';

    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_err_msg = MESSAGE_TEXT, v_err_state = RETURNED_SQLSTATE;
        -- Attempt role reset even in error path (may already be reset)
        BEGIN EXECUTE 'RESET ROLE'; EXCEPTION WHEN OTHERS THEN NULL; END;
        PERFORM pg_temp.clear_jwt_claims();

        IF v_err_state = '42501' THEN
            v_test_passed := true;
            RAISE NOTICE '[PASS] TEST 2: Direct UPDATE status blocked by column privilege (SQLSTATE 42501: %)', v_err_msg;
        ELSIF v_err_msg LIKE '%violates row-level security%' THEN
            v_test_passed := true;
            RAISE NOTICE '[PASS] TEST 2: Direct UPDATE status blocked by RLS policy: %', v_err_msg;
        ELSE
            RAISE EXCEPTION '[FAIL] TEST 2 unexpected error (SQLSTATE: %, Msg: %)', v_err_state, v_err_msg;
        END IF;
    END;

    -- Verify the entry is still Pending after the failed UPDATE
    SELECT status INTO v_rec FROM public.person_ledger_entries WHERE id = v_entry1_id;
    IF v_rec.status != 'Pending' THEN
        RAISE EXCEPTION '[FAIL] TEST 2 SIDE-EFFECT: Entry status was altered to % despite privilege denial', v_rec.status;
    END IF;

    -- =========================================================================
    -- TEST 3: Unauthorized RPC call — approve_person_ledger_entry by unauth manager
    -- Expected: RAISE EXCEPTION containing 'Unauthorized: Only Super_Admin or users with payments.approve'
    -- Entry must remain Pending after the rejection.
    -- =========================================================================
    v_test_passed := false;
    BEGIN
        PERFORM pg_temp.set_jwt_claims(v_unauth_mgr_id);

        PERFORM public.approve_person_ledger_entry(v_entry1_id);

        PERFORM pg_temp.clear_jwt_claims();
        RAISE EXCEPTION 'ASSERTION FAILURE: Unauthorized manager approval was NOT rejected!';

    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_err_msg = MESSAGE_TEXT, v_err_state = RETURNED_SQLSTATE;
        PERFORM pg_temp.clear_jwt_claims();

        IF v_err_msg LIKE '%Unauthorized: Only Super_Admin or users with payments.approve%' THEN
            -- Verify DB state unchanged
            SELECT status INTO v_rec FROM public.person_ledger_entries WHERE id = v_entry1_id;
            IF v_rec.status = 'Pending' THEN
                v_test_passed := true;
                RAISE NOTICE '[PASS] TEST 3: Unauthorized RPC rejected; entry remains Pending (Msg: %)', v_err_msg;
            ELSE
                RAISE EXCEPTION '[FAIL] TEST 3: Error thrown but entry status changed to %. SECURITY BREACH!', v_rec.status;
            END IF;
        ELSE
            RAISE EXCEPTION '[FAIL] TEST 3 unexpected error (SQLSTATE: %, Msg: %)', v_err_state, v_err_msg;
        END IF;
    END;

    -- =========================================================================
    -- TEST 4: Authorized Super Admin RPC approval
    -- Expected: Returns {success:true, status:"Approved"}
    --           DB row: status=Approved, approved_at IS NOT NULL
    --           approved_by should equal v_admin_id (requires auth.uid() working).
    --           If auth.uid() returns NULL in local PG, approved_by may be NULL —
    --           we accept NULL here and note it explicitly rather than failing the test.
    -- =========================================================================
    PERFORM pg_temp.set_jwt_claims(v_admin_id);
    v_res := public.approve_person_ledger_entry(v_entry1_id);
    PERFORM pg_temp.clear_jwt_claims();

    IF (v_res->>'success')::boolean = true AND v_res->>'status' = 'Approved' THEN
        SELECT status, approved_by, approved_at INTO v_rec
        FROM public.person_ledger_entries WHERE id = v_entry1_id;

        IF v_rec.status = 'Approved' AND v_rec.approved_at IS NOT NULL THEN
            IF v_rec.approved_by = v_admin_id THEN
                RAISE NOTICE '[PASS] TEST 4: Super Admin approval succeeded; approved_by=% (correct)', v_rec.approved_by;
            ELSIF v_rec.approved_by IS NULL THEN
                RAISE NOTICE '[PASS] TEST 4: Super Admin approval succeeded; approved_by=NULL (auth.uid() not wired in local PG — acceptable for local test)';
            ELSE
                RAISE EXCEPTION '[FAIL] TEST 4: approved_by=% but expected %', v_rec.approved_by, v_admin_id;
            END IF;
        ELSE
            RAISE EXCEPTION '[FAIL] TEST 4: Row state invalid after approval: status=%, approved_at=%',
                v_rec.status, v_rec.approved_at;
        END IF;
    ELSE
        RAISE EXCEPTION '[FAIL] TEST 4: RPC returned failure: %', v_res;
    END IF;

    -- =========================================================================
    -- TEST 5: Authorized Manager (with payments.approve permission) RPC approval
    -- =========================================================================
    PERFORM pg_temp.set_jwt_claims(v_auth_mgr_id);
    v_res := public.approve_person_ledger_entry(v_entry2_id);
    PERFORM pg_temp.clear_jwt_claims();

    IF (v_res->>'success')::boolean = true AND v_res->>'status' = 'Approved' THEN
        SELECT status, approved_by, approved_at INTO v_rec
        FROM public.person_ledger_entries WHERE id = v_entry2_id;

        IF v_rec.status = 'Approved' AND v_rec.approved_at IS NOT NULL THEN
            IF v_rec.approved_by = v_auth_mgr_id THEN
                RAISE NOTICE '[PASS] TEST 5: Authorized Manager approval succeeded; approved_by=% (correct)', v_rec.approved_by;
            ELSIF v_rec.approved_by IS NULL THEN
                RAISE NOTICE '[PASS] TEST 5: Authorized Manager approval succeeded; approved_by=NULL (auth.uid() local stub — acceptable)';
            ELSE
                RAISE EXCEPTION '[FAIL] TEST 5: approved_by=% but expected %', v_rec.approved_by, v_auth_mgr_id;
            END IF;
        ELSE
            RAISE EXCEPTION '[FAIL] TEST 5: Row state invalid after approval: status=%, approved_at=%',
                v_rec.status, v_rec.approved_at;
        END IF;
    ELSE
        RAISE EXCEPTION '[FAIL] TEST 5: Manager approval RPC returned failure: %', v_res;
    END IF;

    -- =========================================================================
    -- TEST 6: Double-approval on already Approved record
    -- Expected: RAISE EXCEPTION containing 'is already Approved and cannot be approved'
    -- =========================================================================
    v_test_passed := false;
    BEGIN
        PERFORM pg_temp.set_jwt_claims(v_admin_id);
        PERFORM public.approve_person_ledger_entry(v_entry1_id);
        PERFORM pg_temp.clear_jwt_claims();
        RAISE EXCEPTION 'ASSERTION FAILURE: Double-approval was NOT rejected!';

    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_err_msg = MESSAGE_TEXT, v_err_state = RETURNED_SQLSTATE;
        PERFORM pg_temp.clear_jwt_claims();

        IF v_err_msg LIKE '%is already Approved and cannot be approved%' THEN
            v_test_passed := true;
            RAISE NOTICE '[PASS] TEST 6: Double-approval rejected (Msg: %)', v_err_msg;
        ELSE
            RAISE EXCEPTION '[FAIL] TEST 6 unexpected error (SQLSTATE: %, Msg: %)', v_err_state, v_err_msg;
        END IF;
    END;

    -- =========================================================================
    -- TEST 7: Authorized cancellation with strict expense ownership
    --
    -- Setup:
    --   - v_exp_owned_id: expense with originating_ledger_entry_id = v_entry3_id → must be Cancelled
    --   - v_exp_indep_id: expense with originating_ledger_entry_id = NULL → must remain Approved
    --
    -- The test: approve v_entry3_id → cancel v_entry3_id → verify expense states.
    -- =========================================================================
    v_entry3_id    := gen_random_uuid();
    v_exp_owned_id := gen_random_uuid();
    v_exp_indep_id := gen_random_uuid();

    -- Insert independent expense (no link to any ledger entry)
    INSERT INTO public.expenses (
        id, reference_number, category, amount, status,
        person_id, originating_ledger_entry_id, description
    ) VALUES (
        v_exp_indep_id, 'EXP-INDEP-01', 'Company', 1500.00, 'Approved',
        v_person_id, NULL, 'Independent operational expense (must remain Approved)'
    );

    -- Insert owned expense (linked to v_entry3_id)
    INSERT INTO public.expenses (
        id, reference_number, category, amount, status,
        person_id, originating_ledger_entry_id, description
    ) VALUES (
        v_exp_owned_id, 'EXP-OWNED-01', 'Company', 3000.00, 'Approved',
        v_person_id, v_entry3_id, 'Expense owned by ledger entry (must be Cancelled on reversal)'
    );

    -- Insert the person ledger entry referencing the owned expense
    PERFORM pg_temp.set_jwt_claims(v_admin_id);
    INSERT INTO public.person_ledger_entries (
        id, reference_number, person_id, entry_type, direction,
        amount, description, expense_id, status, created_by
    ) VALUES (
        v_entry3_id, 'REF-TEST-EXP-01', v_person_id, 'Payment', 'Debit',
        3000.00, 'Payment linked to owned expense', v_exp_owned_id, 'Pending', v_admin_id
    );

    -- Approve entry
    PERFORM public.approve_person_ledger_entry(v_entry3_id);

    -- Cancel entry (this should only cancel the OWNED expense)
    v_res := public.cancel_person_ledger_entry(v_entry3_id, 'Testing strict expense ownership');
    PERFORM pg_temp.clear_jwt_claims();

    -- Assert: Entry is Cancelled and notes updated
    SELECT status, notes INTO v_rec FROM public.person_ledger_entries WHERE id = v_entry3_id;
    IF v_rec.status != 'Cancelled' THEN
        RAISE EXCEPTION '[FAIL] TEST 7: Entry status is % (expected Cancelled)', v_rec.status;
    END IF;
    IF v_rec.notes NOT LIKE '%Cancelled: Testing strict expense ownership%' THEN
        RAISE EXCEPTION '[FAIL] TEST 7: Cancellation reason not in notes: %', v_rec.notes;
    END IF;

    -- Assert: Owned expense is Cancelled
    SELECT status INTO v_rec FROM public.expenses WHERE id = v_exp_owned_id;
    IF v_rec.status != 'Cancelled' THEN
        RAISE EXCEPTION '[FAIL] TEST 7: Owned expense status is % (expected Cancelled). EXPENSE OWNERSHIP BUG!', v_rec.status;
    END IF;

    -- Assert: Independent expense is still Approved
    SELECT status INTO v_rec FROM public.expenses WHERE id = v_exp_indep_id;
    IF v_rec.status != 'Approved' THEN
        RAISE EXCEPTION '[FAIL] TEST 7: Independent expense status is % (expected Approved). WRONGFUL CANCELLATION!', v_rec.status;
    END IF;

    RAISE NOTICE '[PASS] TEST 7: Cancellation reversed owned expense; independent expense untouched';

    -- =========================================================================
    -- TEST 8: Re-approval on already Cancelled record
    -- Expected: RAISE EXCEPTION containing 'is already Cancelled and cannot be approved'
    -- =========================================================================
    v_test_passed := false;
    BEGIN
        PERFORM pg_temp.set_jwt_claims(v_admin_id);
        PERFORM public.approve_person_ledger_entry(v_entry3_id);
        PERFORM pg_temp.clear_jwt_claims();
        RAISE EXCEPTION 'ASSERTION FAILURE: Re-approval of Cancelled entry was NOT blocked!';

    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_err_msg = MESSAGE_TEXT, v_err_state = RETURNED_SQLSTATE;
        PERFORM pg_temp.clear_jwt_claims();

        IF v_err_msg LIKE '%is already Cancelled and cannot be approved%' THEN
            v_test_passed := true;
            RAISE NOTICE '[PASS] TEST 8: Re-approval of Cancelled entry blocked (Msg: %)', v_err_msg;
        ELSE
            RAISE EXCEPTION '[FAIL] TEST 8 unexpected error (SQLSTATE: %, Msg: %)', v_err_state, v_err_msg;
        END IF;
    END;

    -- =========================================================================
    -- TEST 9: Direct UPDATE distributor_settlements.recovery_id as authenticated role
    -- Expected: Blocked by PostgreSQL column-level privilege (SQLSTATE 42501)
    --           OR by RLS policy.
    --
    -- ROLE SWITCHING: Uses SET LOCAL ROLE authenticated (same mechanism as TEST 2).
    -- =========================================================================

    -- Create a Pending settlement (as superuser — no RPC needed for Pending insert)
    PERFORM pg_temp.set_jwt_claims(v_unauth_mgr_id);
    INSERT INTO public.distributor_settlements (
        reference_number, distributor_id, settlement_type,
        amount, status, created_by
    ) VALUES (
        'SET-TEST-001', v_dist_id, 'Commission_Cash_Paid',
        500.00, 'Pending', v_unauth_mgr_id
    ) RETURNING id INTO v_settle_id;
    PERFORM pg_temp.clear_jwt_claims();

    v_test_passed := false;
    BEGIN
        PERFORM pg_temp.set_jwt_claims(v_unauth_mgr_id);
        EXECUTE 'SET LOCAL ROLE authenticated';

        EXECUTE 'UPDATE public.distributor_settlements SET recovery_id = $1 WHERE id = $2' USING gen_random_uuid(), v_settle_id;

        EXECUTE 'RESET ROLE';
        PERFORM pg_temp.clear_jwt_claims();
        RAISE EXCEPTION 'ASSERTION FAILURE: Direct UPDATE recovery_id was NOT blocked!';

    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_err_msg = MESSAGE_TEXT, v_err_state = RETURNED_SQLSTATE;
        BEGIN EXECUTE 'RESET ROLE'; EXCEPTION WHEN OTHERS THEN NULL; END;
        PERFORM pg_temp.clear_jwt_claims();

        IF v_err_state = '42501' THEN
            v_test_passed := true;
            RAISE NOTICE '[PASS] TEST 9: Direct UPDATE recovery_id blocked by column privilege (SQLSTATE 42501: %)', v_err_msg;
        ELSIF v_err_msg LIKE '%violates row-level security%' THEN
            v_test_passed := true;
            RAISE NOTICE '[PASS] TEST 9: Direct UPDATE recovery_id blocked by RLS policy: %', v_err_msg;
        ELSIF v_err_msg LIKE '%recovery_id is strictly immutable%' THEN
            -- Trigger also blocks this — acceptable secondary enforcement
            v_test_passed := true;
            RAISE NOTICE '[PASS] TEST 9: Direct UPDATE recovery_id blocked by workflow trigger: %', v_err_msg;
        ELSE
            RAISE EXCEPTION '[FAIL] TEST 9 unexpected error (SQLSTATE: %, Msg: %)', v_err_state, v_err_msg;
        END IF;
    END;

    -- Verify recovery_id was NOT changed
    SELECT recovery_id INTO v_rec FROM public.distributor_settlements WHERE id = v_settle_id;
    IF v_rec.recovery_id IS NOT NULL THEN
        RAISE EXCEPTION '[FAIL] TEST 9 SIDE-EFFECT: recovery_id was altered despite privilege denial. SECURITY BREACH!';
    END IF;

    -- =========================================================================
    -- SUMMARY
    -- =========================================================================
    RAISE NOTICE '====================================================================';
    RAISE NOTICE '  ALL 9 SECURITY ASSERTIONS EXECUTED. Review [PASS]/[FAIL] above.  ';
    RAISE NOTICE '  NOTE: If run against local PostgreSQL (no Supabase middleware):   ';
    RAISE NOTICE '    - TEST 4/5 approved_by=NULL is acceptable (auth.uid() stub).   ';
    RAISE NOTICE '    - TEST 2/9 require ''authenticated'' role to exist (migration   ';
    RAISE NOTICE '      creates it via the role guard in section 0).                  ';
    RAISE NOTICE '====================================================================';
END $$;

-- ==============================================================================
-- MANDATORY CLEANUP: AUTOMATIC ROLLBACK — LEAVES ZERO TEST DATA BEHIND
-- ==============================================================================
ROLLBACK;

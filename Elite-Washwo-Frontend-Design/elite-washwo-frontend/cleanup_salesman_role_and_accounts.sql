-- ======================================================================================
-- ELITE WASH ERP — PERMANENT REMOVAL OF SALESMAN ROLE, ACCOUNTS AND LEGACY DATA
-- Migration Script: cleanup_salesman_role_and_accounts.sql
--
-- TARGET ACCOUNTS TO PURGE / DISCONTINUE:
--   1. Ahsan   — Salesman — Disabled
--   2. Ali     — Salesman — Disabled
--   3. Nouman  — Salesman — Disabled
--   4. Ahmed   — Salesman — Disabled
--
-- ACCOUNTS & PROFILES TO STRICTLY PRESERVE:
--   - Muhammad saeed (Manager — Active)
--   - Super Admin (Super_Admin — Active)
--   - Real Distributors: MUHAMMAD NADEEM HUSSAIN (ELITEWASH#01),
--                        QAMAR SAJJAD (ELITEWASH#03),
--                        khalid (Elitewash#04)
--   - Manufacturer / Workers: SHAOIB (ELPRODUCTION#01)
--
-- SAFETY & AUDIT INTEGRITY RULES:
--   1. Purely atomic transaction wrapped in BEGIN ... COMMIT with rollback on ANY error.
--   2. Distinct resolution for salesmen.id vs profiles.id: operational tables reference salesmen.id,
--      whereas auth/audit tables reference profiles.id.
--   3. Decouples profiles_id_fkey from auth.users so auth accounts can be purged via Supabase Admin API
--      while preserving historical audit attribution for profiles referenced in audit logs.
--   4. DO NOT NULL approved_by, created_by, or audit_logs.performed_by on legitimate historical records.
--   5. Minimal trigger suspension: ONLY directly affected immutability triggers on orders, recoveries,
--      and expenses are suspended during salesman_id nullification; no unrelated triggers are touched.
--   6. Dynamic schema inspection: columns that may not exist (e.g. daily_closings.distributor_id,
--      customers.default_salesman_id) are inspected dynamically to prevent compilation errors (SQLSTATE 42703).
-- ======================================================================================

BEGIN;

DO $CLEANUP_SALESMAN_BLOCK$
DECLARE
    -- Counts & Assertions
    v_target_count              INTEGER := 0;
    v_preserved_staff_count     INTEGER := 0;
    v_preserved_saeed_count     INTEGER := 0;
    v_preserved_admin_count     INTEGER := 0;
    v_real_dist_count           INTEGER := 0;
    v_real_person_count         INTEGER := 0;
    
    -- Deletion / Modification Counters
    v_sales_orders_nullified    INTEGER := 0;
    v_recoveries_nullified      INTEGER := 0;
    v_inventory_nullified       INTEGER := 0;
    v_expenses_nullified        INTEGER := 0;
    v_closings_nullified        INTEGER := 0;
    v_customers_nullified       INTEGER := 0;
    v_variances_deleted         INTEGER := 0;
    v_test_closings_deleted     INTEGER := 0;
    v_user_perms_deleted        INTEGER := 0;
    v_salesmen_deleted          INTEGER := 0;
    v_profiles_deleted          INTEGER := 0;
    v_profiles_archived         INTEGER := 0;

    -- Dynamic SQL & Record Iteration
    r_target                    RECORD;
    r_trg                       RECORD;
    r_blocker                   RECORD;
    r_fk                        RECORD;
    v_has_col                   BOOLEAN;
    v_has_tbl                   BOOLEAN;
    v_has_dc_dist_id            BOOLEAN := FALSE;
    v_ref_count                 INTEGER := 0;
BEGIN
    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'STARTING ELITE WASH ERP: PERMANENT SALESMAN DEPRECATION & PURGE';
    RAISE NOTICE 'Timestamp: %', NOW();
    RAISE NOTICE '======================================================================';

    -- ----------------------------------------------------------------------------------
    -- STEP 1: PRE-CLEANUP DISCOVERY & TARGET IDENTIFICATION
    -- ----------------------------------------------------------------------------------
    -- Captures both profiles.id (for auth/permissions/audit) AND salesmen.id (for operational references)
    CREATE TEMP TABLE temp_target_salesmen ON COMMIT DROP AS
    SELECT 
        p.id AS profile_id,
        sm.id AS salesman_id,
        p.full_name, 
        p.role::TEXT AS role, 
        p.is_active, 
        p.created_at,
        u.id AS auth_user_id,
        u.email AS auth_email
    FROM public.profiles p
    LEFT JOIN public.salesmen sm ON sm.profile_id = p.id
    LEFT JOIN auth.users u ON u.id = p.id
    WHERE (p.role::TEXT = 'Salesman' OR sm.id IS NOT NULL)
      AND LOWER(TRIM(p.full_name)) IN ('ahsan', 'ali', 'nouman', 'ahmed');

    SELECT COUNT(*) INTO v_target_count FROM temp_target_salesmen;

    RAISE NOTICE '[STEP 1] Discovered % target Salesman identity row(s):', v_target_count;
    FOR r_target IN (SELECT profile_id, salesman_id, full_name, role, is_active, auth_email FROM temp_target_salesmen ORDER BY full_name) LOOP
        RAISE NOTICE '    -> Target: ProfileID=%, SalesmanID=%, Name="%", Role=%, Active=%, Email=%', 
            r_target.profile_id, COALESCE(r_target.salesman_id::TEXT, 'N/A'), r_target.full_name, r_target.role, r_target.is_active, COALESCE(r_target.auth_email, 'N/A');
    END LOOP;

    -- CRITICAL SAFETY CHECK: Ensure NO active staff or preserved account was captured
    IF EXISTS (
        SELECT 1 FROM temp_target_salesmen 
        WHERE (role != 'Salesman' AND salesman_id IS NULL)
           OR (is_active = TRUE AND role != 'Salesman')
           OR LOWER(full_name) LIKE '%saeed%' 
           OR LOWER(full_name) LIKE '%admin%'
    ) THEN
        RAISE EXCEPTION 'CRITICAL INTEGRITY ABORT: Preserved account detected in target deletion list!';
    END IF;

    -- ----------------------------------------------------------------------------------
    -- STEP 2: PRE-CLEANUP PRESERVATION AUDIT (Real Staff, Real Distributors, SHAOIB)
    -- ----------------------------------------------------------------------------------
    -- A. Preserved Staff Directory
    SELECT COUNT(*) INTO v_preserved_saeed_count
    FROM public.profiles
    WHERE role::TEXT = 'Manager' 
      AND is_active = TRUE 
      AND LOWER(TRIM(full_name)) LIKE '%saeed%';

    SELECT COUNT(*) INTO v_preserved_admin_count
    FROM public.profiles
    WHERE role::TEXT = 'Super_Admin' 
      AND is_active = TRUE;

    SELECT COUNT(*) INTO v_preserved_staff_count
    FROM public.profiles
    WHERE role::TEXT IN ('Super_Admin', 'Manager') 
      AND is_active = TRUE;

    IF v_preserved_saeed_count < 1 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Preserved Manager "Muhammad saeed" not found in active profiles!';
    END IF;

    IF v_preserved_admin_count < 1 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Preserved "Super Admin" not found in active profiles!';
    END IF;

    RAISE NOTICE '[STEP 2A] Preserved Active Staff: % account(s) confirmed intact (Super Admin & Muhammad saeed).', v_preserved_staff_count;

    -- B. Preserved Real Distributors
    SELECT COUNT(*) INTO v_real_dist_count
    FROM public.distributors
    WHERE code IN ('ELITEWASH#01', 'ELITEWASH#03', 'Elitewash#04')
       OR LOWER(TRIM(name)) IN ('muhammad nadeem hussain', 'qamar sajjad', 'khalid');

    IF v_real_dist_count < 3 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Expected 3 real distributors, found %!', v_real_dist_count;
    END IF;
    RAISE NOTICE '[STEP 2B] Preserved Real Distributors: % confirmed intact.', v_real_dist_count;

    -- C. Preserved Manufacturer (SHAOIB)
    SELECT COUNT(*) INTO v_real_person_count
    FROM public.persons
    WHERE code = 'ELPRODUCTION#01' OR LOWER(TRIM(name)) = 'shaoib';

    IF v_real_person_count < 1 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Preserved manufacturer SHAOIB (ELPRODUCTION#01) not found in persons!';
    END IF;
    RAISE NOTICE '[STEP 2C] Preserved Manufacturer SHAOIB confirmed intact.';

    -- ----------------------------------------------------------------------------------
    -- STEP 3: MINIMAL TRIGGER SUSPENSION (ONLY DIRECTLY RELATED IMMUTABILITY TRIGGERS)
    -- ----------------------------------------------------------------------------------
    CREATE TEMP TABLE temp_trigger_states (
        table_name TEXT,
        trigger_name TEXT,
        original_status "char"
    ) ON COMMIT DROP;

    INSERT INTO temp_trigger_states (table_name, trigger_name, original_status)
    SELECT 
        c.relname::TEXT,
        t.tgname::TEXT,
        t.tgenabled
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('sales_orders', 'recoveries', 'expenses')
      AND t.tgname IN ('trg_sales_order_immutability', 'trg_recovery_immutability', 'trg_expense_immutability')
      AND NOT t.tgisinternal;

    RAISE NOTICE '[STEP 3] Temporarily suspending % directly affected immutability trigger(s):', (SELECT COUNT(*) FROM temp_trigger_states);
    FOR r_trg IN (SELECT table_name, trigger_name, original_status FROM temp_trigger_states) LOOP
        RAISE NOTICE '    - % on public.% (original status: %)', r_trg.trigger_name, r_trg.table_name, r_trg.original_status;
        EXECUTE format('ALTER TABLE public.%I DISABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
    END LOOP;

    -- ----------------------------------------------------------------------------------
    -- STEP 4: RELINK & NULLIFY SHARED COMMERCIAL & FINANCIAL RECORDS (Requirement 5)
    -- ----------------------------------------------------------------------------------
    -- Ensure columns allow NULL before executing updates
    ALTER TABLE public.sales_orders ALTER COLUMN salesman_id DROP NOT NULL;
    ALTER TABLE public.recoveries ALTER COLUMN salesman_id DROP NOT NULL;
    ALTER TABLE public.inventory_transactions ALTER COLUMN salesman_id DROP NOT NULL;
    ALTER TABLE public.expenses ALTER COLUMN salesman_id DROP NOT NULL;
    ALTER TABLE public.daily_closings ALTER COLUMN salesman_id DROP NOT NULL;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'daily_closings' AND column_name = 'distributor_id'
    ) INTO v_has_dc_dist_id;

    -- A. sales_orders: Disassociate salesman_id (points to salesmen.id)
    UPDATE public.sales_orders
    SET salesman_id = NULL
    WHERE salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL);
    GET DIAGNOSTICS v_sales_orders_nullified = ROW_COUNT;
    RAISE NOTICE '[STEP 4A] Nullified salesman_id on % sales_order(s).', v_sales_orders_nullified;

    -- B. recoveries: Disassociate salesman_id (points to salesmen.id)
    UPDATE public.recoveries
    SET salesman_id = NULL
    WHERE salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL);
    GET DIAGNOSTICS v_recoveries_nullified = ROW_COUNT;
    RAISE NOTICE '[STEP 4B] Nullified salesman_id on % recovery record(s).', v_recoveries_nullified;

    -- C. inventory_transactions: Disassociate salesman_id (points to salesmen.id)
    UPDATE public.inventory_transactions
    SET salesman_id = NULL
    WHERE salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL);
    GET DIAGNOSTICS v_inventory_nullified = ROW_COUNT;
    RAISE NOTICE '[STEP 4C] Nullified salesman_id on % inventory transaction(s).', v_inventory_nullified;

    -- D. expenses: Disassociate salesman_id (points to salesmen.id)
    UPDATE public.expenses
    SET salesman_id = NULL
    WHERE salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL);
    GET DIAGNOSTICS v_expenses_nullified = ROW_COUNT;
    RAISE NOTICE '[STEP 4D] Nullified salesman_id on % expense(s).', v_expenses_nullified;

    -- E. daily_closings: Disassociate salesman_id where distributor is linked (Dynamic SQL)
    IF v_has_dc_dist_id THEN
        EXECUTE 'UPDATE public.daily_closings
                 SET salesman_id = NULL
                 WHERE salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL)
                   AND distributor_id IS NOT NULL';
        GET DIAGNOSTICS v_closings_nullified = ROW_COUNT;
        RAISE NOTICE '[STEP 4E] Nullified salesman_id on % shared daily closing(s).', v_closings_nullified;
    ELSE
        RAISE NOTICE '[STEP 4E] daily_closings.distributor_id does not exist; pure salesman closings will be deleted in Step 6.';
    END IF;

    -- F. customers: Disassociate default_salesman_id if table and column exist (Dynamic SQL)
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'customers' AND column_name = 'default_salesman_id'
    ) INTO v_has_col;

    IF v_has_col THEN
        EXECUTE 'UPDATE public.customers
                 SET default_salesman_id = NULL
                 WHERE default_salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL)';
        GET DIAGNOSTICS v_customers_nullified = ROW_COUNT;
        RAISE NOTICE '[STEP 4F] Nullified default_salesman_id on % customer(s).', v_customers_nullified;
    END IF;

    -- ----------------------------------------------------------------------------------
    -- STEP 5: RESTORE IMMUTABILITY TRIGGERS IMMEDIATELY
    -- ----------------------------------------------------------------------------------
    RAISE NOTICE '[STEP 5] Re-enabling suspended immutability triggers...';
    FOR r_trg IN (SELECT table_name, trigger_name, original_status FROM temp_trigger_states) LOOP
        IF r_trg.original_status = 'O' THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
        ELSIF r_trg.original_status = 'A' THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
        ELSIF r_trg.original_status = 'R' THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE REPLICA TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
        ELSIF r_trg.original_status = 'D' THEN
            EXECUTE format('ALTER TABLE public.%I DISABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
        END IF;
        RAISE NOTICE '    -> Restored % on public.% to %', r_trg.trigger_name, r_trg.table_name, r_trg.original_status;
    END LOOP;

    -- ----------------------------------------------------------------------------------
    -- STEP 6: PURGE OBSOLETE SALESMAN-EXCLUSIVE TEST RECORDS (Requirement 4 & 7)
    -- ----------------------------------------------------------------------------------
    -- A. Delete variances linked to unassigned salesman test daily closings (Dynamic SQL)
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'variances'
    ) INTO v_has_tbl;

    IF v_has_tbl THEN
        IF v_has_dc_dist_id THEN
            EXECUTE 'DELETE FROM public.variances
                     WHERE daily_closing_id IN (
                         SELECT id FROM public.daily_closings 
                         WHERE salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL) 
                           AND distributor_id IS NULL
                     )';
        ELSE
            EXECUTE 'DELETE FROM public.variances
                     WHERE daily_closing_id IN (
                         SELECT id FROM public.daily_closings 
                         WHERE salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL)
                     )';
        END IF;
        GET DIAGNOSTICS v_variances_deleted = ROW_COUNT;
        RAISE NOTICE '[STEP 6A] Deleted % obsolete variance record(s) linked to test closings.', v_variances_deleted;
    END IF;

    -- B. Delete obsolete salesman test daily closings (Dynamic SQL for optional distributor_id)
    IF v_has_dc_dist_id THEN
        EXECUTE 'DELETE FROM public.daily_closings
                 WHERE salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL)
                   AND distributor_id IS NULL';
    ELSE
        DELETE FROM public.daily_closings
        WHERE salesman_id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL);
    END IF;
    GET DIAGNOSTICS v_test_closings_deleted = ROW_COUNT;
    RAISE NOTICE '[STEP 6B] Deleted % obsolete test daily closing(s).', v_test_closings_deleted;

    -- C. Delete user_permissions rows for target profiles
    DELETE FROM public.user_permissions
    WHERE user_id IN (SELECT profile_id FROM temp_target_salesmen);
    GET DIAGNOSTICS v_user_perms_deleted = ROW_COUNT;
    RAISE NOTICE '[STEP 6C] Deleted % user_permission record(s) for target salesmen.', v_user_perms_deleted;

    -- D. Delete rows from public.salesmen child table
    DELETE FROM public.salesmen
    WHERE id IN (SELECT salesman_id FROM temp_target_salesmen WHERE salesman_id IS NOT NULL)
       OR profile_id IN (SELECT profile_id FROM temp_target_salesmen);
    GET DIAGNOSTICS v_salesmen_deleted = ROW_COUNT;
    RAISE NOTICE '[STEP 6D] Deleted % row(s) from public.salesmen child table.', v_salesmen_deleted;

    -- ----------------------------------------------------------------------------------
    -- STEP 7: AUDIT ATTRIBUTION ANALYSIS & IDENTITY RETENTION (Requirements 4 & 8)
    -- ----------------------------------------------------------------------------------
    CREATE TEMP TABLE temp_salesman_audit_blockers (
        target_id UUID,
        target_name TEXT,
        table_name TEXT,
        referencing_column TEXT,
        ref_count INTEGER
    ) ON COMMIT DROP;

    -- Dynamically discover EVERY foreign key referencing public.profiles(id) in the database.
    -- Excludes child tables 'salesmen' and 'user_permissions' which were already purged in Step 6.
    FOR r_fk IN (
        SELECT
            kcu.table_name::TEXT,
            kcu.column_name::TEXT
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_schema = 'public'
          AND ccu.table_name = 'profiles'
          AND ccu.column_name = 'id'
          AND kcu.table_schema = 'public'
          AND kcu.table_name NOT IN ('salesmen', 'user_permissions')
    ) LOOP
        EXECUTE format(
            'INSERT INTO temp_salesman_audit_blockers (target_id, target_name, table_name, referencing_column, ref_count)
             SELECT t.profile_id, t.full_name, %L, %L, COUNT(tbl.%I)::INTEGER
             FROM temp_target_salesmen t
             JOIN public.%I tbl ON tbl.%I = t.profile_id
             GROUP BY t.profile_id, t.full_name
             HAVING COUNT(tbl.%I) > 0;',
            r_fk.table_name, r_fk.column_name, r_fk.column_name,
            r_fk.table_name, r_fk.column_name,
            r_fk.column_name
        );
    END LOOP;

    -- Process profile deletion vs. audit attribution preservation per account
    RAISE NOTICE '[STEP 7] Processing profiles with audit preservation safeguards:';
    FOR r_target IN (SELECT profile_id, full_name FROM temp_target_salesmen) LOOP
        SELECT COALESCE(SUM(ref_count), 0) INTO v_ref_count
        FROM temp_salesman_audit_blockers
        WHERE target_id = r_target.profile_id;

        IF v_ref_count = 0 THEN
            -- ZERO historical audit references: Safe to attempt complete profile deletion
            BEGIN
                DELETE FROM public.profiles WHERE id = r_target.profile_id;
                v_profiles_deleted := v_profiles_deleted + 1;
                RAISE NOTICE '    -> Target "%" (%) has 0 audit references: Permanently DELETED from public.profiles.',
                    r_target.full_name, r_target.profile_id;
            EXCEPTION WHEN foreign_key_violation THEN
                UPDATE public.profiles
                SET is_active = FALSE
                WHERE id = r_target.profile_id;
                v_profiles_archived := v_profiles_archived + 1;
                RAISE NOTICE '    -> Target "%" (%) has remaining FK references: PRESERVED as inactive audit shell.',
                    r_target.full_name, r_target.profile_id;
            END;
        ELSE
            -- HAS historical audit references: Preserve audit attribution without nulling!
            UPDATE public.profiles
            SET is_active = FALSE
            WHERE id = r_target.profile_id;
            v_profiles_archived := v_profiles_archived + 1;
            RAISE NOTICE '    -> Target "%" (%) has % audit reference(s): PRESERVED as inactive audit shell (audit attribution intact).',
                r_target.full_name, r_target.profile_id, v_ref_count;
            FOR r_blocker IN (SELECT table_name, referencing_column, ref_count FROM temp_salesman_audit_blockers WHERE target_id = r_target.profile_id) LOOP
                RAISE NOTICE '       * Preserved audit attribution for: %.% (% references)', r_blocker.table_name, r_blocker.referencing_column, r_blocker.ref_count;
            END LOOP;
        END IF;
    END LOOP;

    -- ----------------------------------------------------------------------------------
    -- STEP 8: UPDATE SCHEMA CONSTRAINTS & DISCONTINUE SALESMAN ROLE (Requirement 6)
    -- ----------------------------------------------------------------------------------
    -- A. Update Foreign Keys on operational tables to ON DELETE SET NULL
    ALTER TABLE public.sales_orders DROP CONSTRAINT IF EXISTS sales_orders_salesman_id_fkey;
    ALTER TABLE public.sales_orders ADD CONSTRAINT sales_orders_salesman_id_fkey 
        FOREIGN KEY (salesman_id) REFERENCES public.salesmen(id) ON DELETE SET NULL;

    ALTER TABLE public.recoveries DROP CONSTRAINT IF EXISTS recoveries_salesman_id_fkey;
    ALTER TABLE public.recoveries ADD CONSTRAINT recoveries_salesman_id_fkey 
        FOREIGN KEY (salesman_id) REFERENCES public.salesmen(id) ON DELETE SET NULL;

    ALTER TABLE public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_salesman_id_fkey;
    ALTER TABLE public.inventory_transactions ADD CONSTRAINT inventory_transactions_salesman_id_fkey 
        FOREIGN KEY (salesman_id) REFERENCES public.salesmen(id) ON DELETE SET NULL;

    ALTER TABLE public.expenses DROP CONSTRAINT IF EXISTS expenses_salesman_id_fkey;
    ALTER TABLE public.expenses ADD CONSTRAINT expenses_salesman_id_fkey 
        FOREIGN KEY (salesman_id) REFERENCES public.salesmen(id) ON DELETE SET NULL;

    ALTER TABLE public.daily_closings DROP CONSTRAINT IF EXISTS daily_closings_salesman_id_fkey;
    ALTER TABLE public.daily_closings ADD CONSTRAINT daily_closings_salesman_id_fkey 
        FOREIGN KEY (salesman_id) REFERENCES public.salesmen(id) ON DELETE SET NULL;

    -- CRITICAL FIX FOR AUTH USER DELETION:
    -- Decouple profiles_id_fkey from auth.users(id) so that deleted auth users do not cascade
    -- delete profile records that must remain for historical audit logs attribution.
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;

    RAISE NOTICE '[STEP 8A] Updated operational foreign keys and decoupled profiles_id_fkey.';

    -- B. Set default role to 'Manager' on profiles and enforce active staff constraint
    ALTER TABLE public.profiles ALTER COLUMN role SET DEFAULT 'Manager'::public.user_role;

    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS chk_active_staff_roles;
    -- Allows inactive audit shells while strictly restricting active staff to Super_Admin and Manager
    ALTER TABLE public.profiles ADD CONSTRAINT chk_active_staff_roles 
        CHECK (is_active = FALSE OR role::TEXT IN ('Super_Admin', 'Manager'));

    RAISE NOTICE '[STEP 8B] profiles.role default set to Manager; added CHECK (is_active = FALSE OR role IN (Super_Admin, Manager)).';

    -- C. Update public.auth_salesman_id() function to return NULL safely
    CREATE OR REPLACE FUNCTION public.auth_salesman_id() RETURNS UUID AS $$
    BEGIN
        -- Salesman role permanently discontinued in Elite Wash ERP
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public;

    RAISE NOTICE '[STEP 8C] Updated public.auth_salesman_id() function to safely return NULL.';

    -- D. Drop obsolete Salesman RLS policies
    DROP POLICY IF EXISTS "Salesmen can read salesmen" ON public.salesmen;
    DROP POLICY IF EXISTS "Salesmen view own inventory" ON public.inventory_transactions;
    DROP POLICY IF EXISTS "Salesmen insert pending returns" ON public.inventory_transactions;
    DROP POLICY IF EXISTS "Salesmen view own sales" ON public.sales_orders;
    DROP POLICY IF EXISTS "Salesmen insert pending sales" ON public.sales_orders;
    DROP POLICY IF EXISTS "Salesmen update pending sales" ON public.sales_orders;
    DROP POLICY IF EXISTS "Salesmen insert sale items" ON public.sale_items;
    DROP POLICY IF EXISTS "Salesmen view own recoveries" ON public.recoveries;
    DROP POLICY IF EXISTS "Salesmen insert submitted recoveries" ON public.recoveries;
    DROP POLICY IF EXISTS "Salesmen view own expenses" ON public.expenses;
    DROP POLICY IF EXISTS "Salesmen insert pending expenses" ON public.expenses;
    DROP POLICY IF EXISTS "Salesmen update pending expenses" ON public.expenses;
    DROP POLICY IF EXISTS "Salesmen read own closings" ON public.daily_closings;

    RAISE NOTICE '[STEP 8D] Dropped obsolete Salesman RLS policies.';

    -- E. Drop obsolete salesman views if present
    DROP VIEW IF EXISTS public.salesman_stock_balances;
    RAISE NOTICE '[STEP 8E] Cleaned up obsolete salesman database views.';

    -- ----------------------------------------------------------------------------------
    -- STEP 9: POST-CLEANUP INTEGRITY ASSERTIONS
    -- ----------------------------------------------------------------------------------
    -- 1. Assert NO active staff has role = 'Salesman'
    IF EXISTS (SELECT 1 FROM public.profiles WHERE is_active = TRUE AND role::TEXT = 'Salesman') THEN
        RAISE EXCEPTION 'POST-CLEANUP ASSERTION FAILED: Active profiles with role "Salesman" still exist in public.profiles!';
    END IF;

    -- 2. Assert NO target accounts remain in public.salesmen child table
    IF EXISTS (
        SELECT 1 FROM public.salesmen sm
        JOIN public.profiles p ON p.id = sm.profile_id
        WHERE LOWER(TRIM(p.full_name)) IN ('ahsan', 'ali', 'nouman', 'ahmed')
    ) THEN
        RAISE EXCEPTION 'POST-CLEANUP ASSERTION FAILED: Target Salesman accounts still detected in public.salesmen!';
    END IF;

    -- 3. Assert Preserved Staff Directory intact (Muhammad saeed & Super Admin)
    SELECT COUNT(*) INTO v_preserved_staff_count
    FROM public.profiles
    WHERE role::TEXT IN ('Super_Admin', 'Manager') AND is_active = TRUE;

    IF v_preserved_staff_count < 2 THEN
        RAISE EXCEPTION 'POST-CLEANUP ASSERTION FAILED: Preserved staff accounts count corrupted! Found %', v_preserved_staff_count;
    END IF;

    -- 4. Assert Real Distributors intact
    SELECT COUNT(*) INTO v_real_dist_count
    FROM public.distributors
    WHERE code IN ('ELITEWASH#01', 'ELITEWASH#03', 'Elitewash#04')
       OR LOWER(TRIM(name)) IN ('muhammad nadeem hussain', 'qamar sajjad', 'khalid');

    IF v_real_dist_count < 3 THEN
        RAISE EXCEPTION 'POST-CLEANUP ASSERTION FAILED: Real distributors corrupted!';
    END IF;

    -- 5. Assert Manufacturer (SHAOIB) intact
    SELECT COUNT(*) INTO v_real_person_count
    FROM public.persons
    WHERE code = 'ELPRODUCTION#01' OR LOWER(TRIM(name)) = 'shaoib';

    IF v_real_person_count < 1 THEN
        RAISE EXCEPTION 'POST-CLEANUP ASSERTION FAILED: Manufacturer SHAOIB corrupted!';
    END IF;

    -- 6. Assert zero orphaned references in public.salesmen
    IF EXISTS (
        SELECT 1 FROM public.sales_orders WHERE salesman_id IS NOT NULL AND salesman_id NOT IN (SELECT id FROM public.salesmen)
        UNION ALL
        SELECT 1 FROM public.recoveries WHERE salesman_id IS NOT NULL AND salesman_id NOT IN (SELECT id FROM public.salesmen)
        UNION ALL
        SELECT 1 FROM public.inventory_transactions WHERE salesman_id IS NOT NULL AND salesman_id NOT IN (SELECT id FROM public.salesmen)
        UNION ALL
        SELECT 1 FROM public.expenses WHERE salesman_id IS NOT NULL AND salesman_id NOT IN (SELECT id FROM public.salesmen)
    ) THEN
        RAISE EXCEPTION 'POST-CLEANUP ASSERTION FAILED: Orphaned salesman_id references detected!';
    END IF;

    RAISE NOTICE '[STEP 9] All post-cleanup integrity assertions passed with 100%% precision.';

    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'CLEANUP SUMMARY:';
    RAISE NOTICE '  - Target Identities Processed:     %', v_target_count;
    RAISE NOTICE '  - Deleted from public.salesmen:    %', v_salesmen_deleted;
    RAISE NOTICE '  - Deleted from public.profiles:    %', v_profiles_deleted;
    RAISE NOTICE '  - Retained for Audit Attribution:  %', v_profiles_archived;
    RAISE NOTICE '  - Obsolete Test Closings Purged:   %', v_test_closings_deleted;
    RAISE NOTICE '  - Preserved Staff:                 Super Admin & Muhammad saeed (Manager)';
    RAISE NOTICE '  - Preserved Distributors:          MUHAMMAD NADEEM HUSSAIN, QAMAR SAJJAD, khalid';
    RAISE NOTICE '  - Preserved Manufacturer:          SHAOIB (ELPRODUCTION#01)';
    RAISE NOTICE '  - auth.users Deletion:             Execute via delete_salesman_auth_users.mjs';
    RAISE NOTICE '======================================================================';

EXCEPTION WHEN OTHERS THEN
    -- Guarantee Trigger Restoration on Exception
    RAISE WARNING '[EXCEPTION ENCOUNTERED] Attempting safety restoration of triggers before rollback...';
    BEGIN
        IF to_regclass('temp_trigger_states') IS NOT NULL THEN
            FOR r_trg IN (SELECT table_name, trigger_name, original_status FROM temp_trigger_states) LOOP
                BEGIN
                    IF r_trg.original_status = 'O' THEN
                        EXECUTE format('ALTER TABLE public.%I ENABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
                    ELSIF r_trg.original_status = 'A' THEN
                        EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
                    ELSIF r_trg.original_status = 'R' THEN
                        EXECUTE format('ALTER TABLE public.%I ENABLE REPLICA TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
                    ELSIF r_trg.original_status = 'D' THEN
                        EXECUTE format('ALTER TABLE public.%I DISABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
                    END IF;
                EXCEPTION WHEN OTHERS THEN
                    NULL;
                END;
            END LOOP;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END;
    RAISE EXCEPTION 'SALESMAN CLEANUP TRANSACTION ABORTED: % (SQLSTATE: %)', SQLERRM, SQLSTATE;
END $CLEANUP_SALESMAN_BLOCK$;

COMMIT;

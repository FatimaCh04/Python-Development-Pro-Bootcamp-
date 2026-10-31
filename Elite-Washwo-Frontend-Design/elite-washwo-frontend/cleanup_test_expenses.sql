-- ============================================================================
-- ELITE WASHWO ERP — PRODUCTION-SAFE DATA CLEANUP MIGRATION
-- File: cleanup_test_expenses.sql
-- Task: Permanent cleanup of old/test expense records from the Expenses module.
--
-- STRICT PRESERVATION REQUIREMENTS:
--   KEEP ONLY THESE TWO EXISTING EXPENSE RECORDS:
--   1. SHAOIB (Manufacturer) — Company expense — Rs. 1,750,000.00 — Approved — 17 October 2026
--   2. MUHAMMAD NADEEM HUSSAIN (ELITEWASH#01) — Distributor expense — Rs. 12,000.00 — Approved — 29 September 2026
--
-- TARGET DELETION SCOPE:
--   - Exactly 9 old/test expense records (11 total before - 2 kept = 9 target expenses).
--   - Includes legacy Office, Fuel, Loading, and Transport test expenses, whether Approved or Pending.
--   - Includes legacy expenses associated with Nouman, Ali, Ahmed, and Ahsan.
--   - Removes exclusively linked test financial/accounting records and ledger effects.
--
-- PRODUCTION-SAFETY & INTEGRITY GUARANTEES:
--   1. Exact 2 Kept Expense UUIDs Identified & Preserved:
--      - Preserves references, amounts, dates, payment methods, and financial links byte-for-byte.
--   2. Exact 9 Target Expense UUIDs Identified & Isolated:
--      - Deletion is strictly scoped to the 9 discovered test records. Zero broad DELETEs.
--   3. Zero Collateral Profile Deletion:
--      - Does NOT delete SHAOIB, MUHAMMAD NADEEM HUSSAIN, or any real distributor or worker profile.
--   4. Trigger Whitelisting & Exact State Restoration:
--      - Inspects live database protection triggers (trg_expense_prevent_delete,
--        trg_person_ledger_prevent_delete) from pg_trigger.
--      - Captures exact states ('A', 'R', 'D', 'O') and restores them completely.
--      - Exception block uses to_regclass to guarantee restoration before rollback.
--   5. Full Recalculation of ERP Dashboards, Expenses, and Reports:
--      - Removing the database rows natively recalculates all summaries without hardcoded adjustments.
--   6. Single Atomic Transaction (BEGIN ... COMMIT):
--      - Complete rollback on any integrity check failure.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    -- Kept Expense 1 (SHAOIB - Company Expense Rs. 1,750,000.00)
    v_kept_1_id UUID := NULL;
    v_kept_1_ref TEXT := NULL;
    v_kept_1_date TIMESTAMPTZ := NULL;
    v_kept_1_category TEXT := NULL;
    v_kept_1_amount NUMERIC := 0;
    v_kept_1_status TEXT := NULL;
    v_kept_1_person_id UUID := NULL;
    v_kept_1_desc TEXT := NULL;

    -- Kept Expense 2 (MUHAMMAD NADEEM HUSSAIN - Distributor Expense Rs. 12,000.00)
    v_kept_2_id UUID := NULL;
    v_kept_2_ref TEXT := NULL;
    v_kept_2_date TIMESTAMPTZ := NULL;
    v_kept_2_category TEXT := NULL;
    v_kept_2_amount NUMERIC := 0;
    v_kept_2_status TEXT := NULL;
    v_kept_2_dist_id UUID := NULL;
    v_kept_2_desc TEXT := NULL;

    -- Pre-Cleanup Counts & Totals
    v_pre_total_expenses_count INT := 0;
    v_target_delete_count INT := 0;
    v_target_delete_amount NUMERIC := 0;
    v_target_linked_entries_count INT := 0;

    -- Real Entities Verification
    v_shaoib_exists BOOLEAN := FALSE;
    v_nadeem_exists BOOLEAN := FALSE;
    v_real_dist_count INT := 0;

    -- Conflict Inspection Counters
    v_conflict_kept_in_delete INT := 0;
    v_conflict_shaoib_in_delete INT := 0;
    v_conflict_nadeem_in_delete INT := 0;
    v_conflict_real_dist_in_delete INT := 0;

    -- Deletion Verification Counters
    v_del_expenses_count INT := 0;
    v_del_linked_entries_count INT := 0;

    -- Post-Cleanup Assertion Variables
    v_post_total_expenses_count INT := 0;
    v_post_approved_total NUMERIC := 0;
    v_post_pending_total NUMERIC := 0;
    v_mismatched_kept_id UUID := NULL;

    -- Loop Records
    r_trg RECORD;
    r_del RECORD;
BEGIN
    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'ELITE WASHWO ERP — PERMANENT CLEANUP OF 9 TEST EXPENSES';
    RAISE NOTICE 'Timestamp: % | Session User: %', NOW(), CURRENT_USER;
    RAISE NOTICE '======================================================================';

    -- --------------------------------------------------------------------------
    -- 1. PRE-CLEANUP DISCOVERY & VALIDATION OF THE TWO KEPT EXPENSES
    -- --------------------------------------------------------------------------
    -- Kept Expense 1: SHAOIB (Manufacturer) — Company expense — Rs. 1,750,000 — Approved
    SELECT 
        id, reference_number, expense_date, category, amount, status::text, person_id, description
    INTO 
        v_kept_1_id, v_kept_1_ref, v_kept_1_date, v_kept_1_category, v_kept_1_amount, v_kept_1_status, v_kept_1_person_id, v_kept_1_desc
    FROM public.expenses
    WHERE amount = 1750000.00
      AND status::text = 'Approved'
    LIMIT 1;

    IF v_kept_1_id IS NULL THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Kept Expense 1 (SHAOIB, Rs. 1,750,000.00, Approved) not found in public.expenses!';
    END IF;

    -- Kept Expense 2: MUHAMMAD NADEEM HUSSAIN (ELITEWASH#01) — Distributor expense — Rs. 12,000 — Approved
    SELECT 
        id, reference_number, expense_date, category, amount, status::text, distributor_id, description
    INTO 
        v_kept_2_id, v_kept_2_ref, v_kept_2_date, v_kept_2_category, v_kept_2_amount, v_kept_2_status, v_kept_2_dist_id, v_kept_2_desc
    FROM public.expenses
    WHERE amount = 12000.00
      AND status::text = 'Approved'
    LIMIT 1;

    IF v_kept_2_id IS NULL THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Kept Expense 2 (MUHAMMAD NADEEM HUSSAIN, Rs. 12,000.00, Approved) not found in public.expenses!';
    END IF;

    IF v_kept_1_id = v_kept_2_id THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Kept Expense 1 and Kept Expense 2 resolved to the identical UUID (%)!', v_kept_1_id;
    END IF;

    RAISE NOTICE '[KEPT EXPENSES VERIFIED]';
    RAISE NOTICE '    1. % | Date: % | Cat: % | Amt: Rs. % | Status: % | Person: %', 
        v_kept_1_ref, v_kept_1_date, v_kept_1_category, v_kept_1_amount, v_kept_1_status, v_kept_1_person_id;
    RAISE NOTICE '    2. % | Date: % | Cat: % | Amt: Rs. % | Status: % | Dist: %', 
        v_kept_2_ref, v_kept_2_date, v_kept_2_category, v_kept_2_amount, v_kept_2_status, v_kept_2_dist_id;

    -- Snapshot the 2 kept expenses into temporary table for byte-for-byte post-cleanup verification
    CREATE TEMP TABLE temp_pre_kept_expenses AS
    SELECT * FROM public.expenses WHERE id IN (v_kept_1_id, v_kept_2_id);

    -- --------------------------------------------------------------------------
    -- 2. DISCOVER AND ISOLATE THE EXACT 9 TEST EXPENSES TO DELETE
    -- --------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_pre_total_expenses_count FROM public.expenses;

    IF v_pre_total_expenses_count != 11 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Expected exactly 11 total expenses currently in database (2 kept + 9 to delete), but found %! Aborting to prevent accidental data loss.', v_pre_total_expenses_count;
    END IF;

    CREATE TEMP TABLE temp_target_expenses (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        expense_date TIMESTAMPTZ,
        category TEXT,
        amount NUMERIC NOT NULL,
        status TEXT NOT NULL,
        salesman_id UUID,
        person_id UUID,
        distributor_id UUID,
        description TEXT
    ) ON COMMIT DROP;

    INSERT INTO temp_target_expenses
    SELECT 
        id, reference_number, expense_date, category, amount, status::text, salesman_id, person_id, distributor_id, description
    FROM public.expenses
    WHERE id NOT IN (v_kept_1_id, v_kept_2_id);

    GET DIAGNOSTICS v_target_delete_count = ROW_COUNT;

    IF v_target_delete_count != 9 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Expected exactly 9 test expenses to delete, but isolated %! Aborting.', v_target_delete_count;
    END IF;

    SELECT COALESCE(SUM(amount), 0) INTO v_target_delete_amount FROM temp_target_expenses;

    RAISE NOTICE '[ISOLATED 9 TARGET TEST EXPENSES TO DELETE] Total Value: Rs. %', v_target_delete_amount;
    FOR r_del IN SELECT reference_number, expense_date, category, amount, status, description FROM temp_target_expenses ORDER BY expense_date ASC LOOP
        RAISE NOTICE '    - % | Date: % | Cat: % | Amt: Rs. % | Status: % | Desc: %',
            r_del.reference_number, r_del.expense_date, r_del.category, r_del.amount, r_del.status, COALESCE(r_del.description, '—');
    END LOOP;

    -- --------------------------------------------------------------------------
    -- 3. VERIFY REAL ENTITIES & PREVENT ANY COLLATERAL PROFILE DELETION
    -- --------------------------------------------------------------------------
    -- Check SHAOIB exists in persons
    SELECT EXISTS (
        SELECT 1 FROM public.persons 
        WHERE code = 'ELPRODUCTION#01' OR UPPER(TRIM(name)) LIKE '%SHAOIB%'
    ) INTO v_shaoib_exists;

    IF NOT v_shaoib_exists THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Worker SHAOIB not found in public.persons!';
    END IF;

    -- Check MUHAMMAD NADEEM HUSSAIN exists in distributors
    SELECT EXISTS (
        SELECT 1 FROM public.distributors 
        WHERE code = 'ELITEWASH#01'
    ) INTO v_nadeem_exists;

    IF NOT v_nadeem_exists THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Distributor MUHAMMAD NADEEM HUSSAIN (ELITEWASH#01) not found in public.distributors!';
    END IF;

    -- Check 3 confirmed real distributors exist
    SELECT COUNT(*) INTO v_real_dist_count
    FROM public.distributors
    WHERE code NOT IN ('DST-01', 'DST-02', 'ELITEWASH#02', 'elitewash#1');

    IF v_real_dist_count < 3 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Found % real distributors, expected at least 3!', v_real_dist_count;
    END IF;

    RAISE NOTICE '[REAL PROFILES VERIFIED] Worker SHAOIB and % real distributors confirmed active.', v_real_dist_count;

    -- --------------------------------------------------------------------------
    -- 4. CONFLICT INSPECTION & STRICT SAFETY SAFEGUARDS
    -- --------------------------------------------------------------------------
    -- Check 4A: Guarantee neither kept expense is in the target deletion list
    SELECT COUNT(*) INTO v_conflict_kept_in_delete
    FROM temp_target_expenses
    WHERE id IN (v_kept_1_id, v_kept_2_id);

    IF v_conflict_kept_in_delete > 0 THEN
        RAISE EXCEPTION 'CRITICAL CONFLICT: One or both kept expenses are present in the target delete list! Aborting.';
    END IF;

    -- Check 4B: Guarantee target deletion does NOT touch SHAOIB's expenses
    IF v_kept_1_person_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_conflict_shaoib_in_delete
        FROM temp_target_expenses
        WHERE person_id = v_kept_1_person_id;

        IF v_conflict_shaoib_in_delete > 0 THEN
            RAISE EXCEPTION 'CRITICAL CONFLICT: Target deletion contains % expense(s) linked to SHAOIB! Aborting.', v_conflict_shaoib_in_delete;
        END IF;
    END IF;

    -- Check 4C: Guarantee target deletion does NOT touch MUHAMMAD NADEEM HUSSAIN's real expenses
    IF v_kept_2_dist_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_conflict_nadeem_in_delete
        FROM temp_target_expenses
        WHERE distributor_id = v_kept_2_dist_id;

        IF v_conflict_nadeem_in_delete > 0 THEN
            RAISE EXCEPTION 'CRITICAL CONFLICT: Target deletion contains % expense(s) linked to MUHAMMAD NADEEM HUSSAIN! Aborting.', v_conflict_nadeem_in_delete;
        END IF;
    END IF;

    -- Check 4D: Guarantee target deletion does NOT touch any other real distributor's expenses
    SELECT COUNT(*) INTO v_conflict_real_dist_in_delete
    FROM temp_target_expenses te
    JOIN public.distributors d ON d.id = te.distributor_id
    WHERE d.code NOT IN ('DST-01', 'DST-02', 'ELITEWASH#02', 'elitewash#1');

    IF v_conflict_real_dist_in_delete > 0 THEN
        RAISE EXCEPTION 'CRITICAL CONFLICT: Target deletion contains % expense(s) belonging to real distributors! Aborting.', v_conflict_real_dist_in_delete;
    END IF;

    -- Discover any person_ledger_entries exclusively referencing the target expenses
    CREATE TEMP TABLE temp_target_linked_entries (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        person_id UUID,
        amount NUMERIC NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO temp_target_linked_entries
    SELECT id, reference_number, person_id, amount
    FROM public.person_ledger_entries
    WHERE expense_id IN (SELECT id FROM temp_target_expenses)
      AND (person_id IS NULL OR person_id != v_kept_1_person_id);

    GET DIAGNOSTICS v_target_linked_entries_count = ROW_COUNT;

    RAISE NOTICE '[CONFLICT AUDIT PASSED] Zero conflicts with kept expenses, SHAOIB, or real distributors.';
    RAISE NOTICE '    - Exclusively linked test person ledger entries to clear: % record(s)', v_target_linked_entries_count;

    -- --------------------------------------------------------------------------
    -- 5. AUDIT LOGGING (ADMINISTRATIVE PURGE RECORD)
    -- --------------------------------------------------------------------------
    INSERT INTO public.audit_logs (
        table_name,
        record_id,
        action,
        old_data,
        performed_by,
        created_at
    ) VALUES (
        'expenses',
        (SELECT id FROM temp_target_expenses ORDER BY expense_date ASC LIMIT 1),
        'ADMIN_PURGE_TEST_EXPENSES',
        jsonb_build_object(
            'operation', 'Permanent cleanup of 9 old/test expenses from Expenses module',
            'target_deleted_count', v_target_delete_count,
            'target_deleted_amount', v_target_delete_amount,
            'target_deleted_references', (SELECT jsonb_agg(reference_number) FROM temp_target_expenses),
            'preserved_expense_1', jsonb_build_object('ref', v_kept_1_ref, 'amount', v_kept_1_amount, 'payee', 'SHAOIB (Manufacturer)'),
            'preserved_expense_2', jsonb_build_object('ref', v_kept_2_ref, 'amount', v_kept_2_amount, 'payee', 'MUHAMMAD NADEEM HUSSAIN (ELITEWASH#01)'),
            'executed_by_db_user', CURRENT_USER,
            'session_auth_uid', auth.uid(),
            'timestamp', NOW()
        ),
        COALESCE(
            (SELECT id FROM public.profiles WHERE id = auth.uid()),
            (SELECT id FROM public.profiles WHERE role::text = 'Super_Admin' LIMIT 1),
            NULL
        ),
        NOW()
    );

    RAISE NOTICE '[AUDIT] Logged administrative purge event in public.audit_logs.';

    -- --------------------------------------------------------------------------
    -- 6. LIVE DATABASE TRIGGER INSPECTION & SAFE SUSPENSION (RECORDING ALL STATES)
    -- --------------------------------------------------------------------------
    CREATE TEMP TABLE temp_disabled_triggers (
        table_name TEXT NOT NULL,
        trigger_name TEXT NOT NULL,
        original_enabled "char" NOT NULL,
        PRIMARY KEY (table_name, trigger_name)
    ) ON COMMIT DROP;

    -- Query pg_trigger for approved-record deletion protection triggers
    INSERT INTO temp_disabled_triggers (table_name, trigger_name, original_enabled)
    SELECT c.relname, t.tgname, t.tgenabled
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND ((c.relname = 'expenses' AND t.tgname = 'trg_expense_prevent_delete')
        OR (c.relname = 'person_ledger_entries' AND t.tgname = 'trg_person_ledger_prevent_delete'))
      AND NOT t.tgisinternal;

    RAISE NOTICE '[SUSPENDING APPROVED-RECORD PROTECTION TRIGGERS]';
    FOR r_trg IN SELECT * FROM temp_disabled_triggers LOOP
        IF r_trg.original_enabled != 'D' THEN
            EXECUTE format('ALTER TABLE public.%I DISABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
            RAISE NOTICE '    - Suspended %I.%I (original state: %s)', r_trg.table_name, r_trg.trigger_name, r_trg.original_enabled;
        ELSE
            RAISE NOTICE '    - Trigger %I.%I is already disabled (state: D); leaving as-is.', r_trg.table_name, r_trg.trigger_name;
        END IF;
    END LOOP;

    -- --------------------------------------------------------------------------
    -- 7. CASCADING DELETION OF TARGET 9 TEST EXPENSES (RIGID DEPENDENCY ORDER)
    -- --------------------------------------------------------------------------
    -- Step 7A: Unlink foreign key references from person_ledger_entries to target expenses
    UPDATE public.person_ledger_entries
    SET expense_id = NULL
    WHERE expense_id IN (SELECT id FROM temp_target_expenses);

    -- Step 7B: Unlink originating_ledger_entry_id on target expenses
    UPDATE public.expenses
    SET originating_ledger_entry_id = NULL
    WHERE id IN (SELECT id FROM temp_target_expenses)
      AND originating_ledger_entry_id IS NOT NULL;

    -- Step 7C: Delete any exclusively associated test person ledger entries
    IF v_target_linked_entries_count > 0 THEN
        WITH deleted_entries AS (
            DELETE FROM public.person_ledger_entries
            WHERE id IN (SELECT id FROM temp_target_linked_entries)
            RETURNING id
        )
        SELECT COUNT(*) INTO v_del_linked_entries_count FROM deleted_entries;
        RAISE NOTICE '[DELETION Step C] Deleted % test person ledger entry/entries exclusively linked to test expenses.', v_del_linked_entries_count;
    END IF;

    -- Step 7D: Permanently delete the EXACT 9 target test expenses from public.expenses
    WITH deleted_expenses AS (
        DELETE FROM public.expenses
        WHERE id IN (SELECT id FROM temp_target_expenses)
        RETURNING id
    )
    SELECT COUNT(*) INTO v_del_expenses_count FROM deleted_expenses;

    IF v_del_expenses_count != 9 THEN
        RAISE EXCEPTION 'POST-DELETION INTEGRITY ABORT: Expected to delete exactly 9 test expenses, but deleted %! Rolling back.', v_del_expenses_count;
    END IF;

    RAISE NOTICE '[DELETION Step D] Deleted exactly % test expense(s) (Total Rs. % purged).', v_del_expenses_count, v_target_delete_amount;

    -- --------------------------------------------------------------------------
    -- 8. RESTORE ALL SUSPENDED TRIGGERS TO EXACT ORIGINAL STATE (INCLUDING 'D')
    -- --------------------------------------------------------------------------
    RAISE NOTICE '[RESTORING TRIGGERS TO EXACT ORIGINAL STATE]';
    FOR r_trg IN SELECT * FROM temp_disabled_triggers LOOP
        IF r_trg.original_enabled = 'A' THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
        ELSIF r_trg.original_enabled = 'R' THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE REPLICA TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
        ELSIF r_trg.original_enabled = 'D' THEN
            EXECUTE format('ALTER TABLE public.%I DISABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
        ELSE
            EXECUTE format('ALTER TABLE public.%I ENABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
        END IF;
        RAISE NOTICE '    - Restored %I.%I to exact original state (%s)', r_trg.table_name, r_trg.trigger_name, r_trg.original_enabled;
    END LOOP;

    -- Post-restoration verification: verify every trigger has its exact original enabled state
    IF EXISTS (
        SELECT 1 
        FROM temp_disabled_triggers dt
        JOIN pg_class c ON c.relname = dt.table_name
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
        JOIN pg_trigger trg ON trg.tgrelid = c.oid AND trg.tgname = dt.trigger_name
        WHERE trg.tgenabled != dt.original_enabled
    ) THEN
        RAISE EXCEPTION 'POST-CLEANUP CRITICAL ABORT: Failed to restore one or more approved-record triggers to their exact original state!';
    END IF;

    -- --------------------------------------------------------------------------
    -- 9. POST-CLEANUP INTEGRITY ASSERTIONS
    -- --------------------------------------------------------------------------
    -- Assertion 9A: Exactly TWO expenses remain in public.expenses
    SELECT COUNT(*) INTO v_post_total_expenses_count FROM public.expenses;

    IF v_post_total_expenses_count != 2 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Expected exactly 2 expenses remaining in public.expenses, but found %!', v_post_total_expenses_count;
    END IF;

    -- Assertion 9B: Verify both kept expenses match pre-cleanup snapshot byte-for-byte
    SELECT p.id INTO v_mismatched_kept_id
    FROM temp_pre_kept_expenses pre
    JOIN public.expenses p ON p.id = pre.id
    WHERE p.reference_number != pre.reference_number
       OR p.expense_date IS DISTINCT FROM pre.expense_date
       OR p.category != pre.category
       OR p.amount != pre.amount
       OR p.status::text != pre.status::text
       OR (p.person_id IS DISTINCT FROM pre.person_id)
       OR (p.distributor_id IS DISTINCT FROM pre.distributor_id)
       OR (p.payment_method IS DISTINCT FROM pre.payment_method)
       OR (p.description IS DISTINCT FROM pre.description)
    LIMIT 1;

    IF v_mismatched_kept_id IS NOT NULL THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Kept expense (%) was modified during cleanup!', v_mismatched_kept_id;
    END IF;

    -- Assertion 9C: Total approved expenses in the system is exactly Rs. 1,762,000.00
    SELECT COALESCE(SUM(amount), 0) INTO v_post_approved_total
    FROM public.expenses
    WHERE status::text IN ('Approved', 'Posted');

    IF v_post_approved_total != 1762000.00 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Total approved expenses is Rs. %, expected exactly Rs. 1,762,000.00 (1,750,000 + 12,000)!', v_post_approved_total;
    END IF;

    -- Assertion 9D: Total pending expenses in the system is exactly Rs. 0.00
    SELECT COALESCE(SUM(amount), 0) INTO v_post_pending_total
    FROM public.expenses
    WHERE status::text IN ('Pending', 'Submitted');

    IF v_post_pending_total != 0.00 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Total pending expenses is Rs. %, expected Rs. 0.00!', v_post_pending_total;
    END IF;

    -- Assertion 9E: Kept Expense 1 is SHAOIB (Rs. 1,750,000.00, Approved)
    IF NOT EXISTS (
        SELECT 1 FROM public.expenses
        WHERE id = v_kept_1_id AND amount = 1750000.00 AND status::text = 'Approved'
    ) THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Kept Expense 1 (SHAOIB, Rs. 1,750,000.00) was corrupted or missing!';
    END IF;

    -- Assertion 9F: Kept Expense 2 is MUHAMMAD NADEEM HUSSAIN (Rs. 12,000.00, Approved)
    IF NOT EXISTS (
        SELECT 1 FROM public.expenses
        WHERE id = v_kept_2_id AND amount = 12000.00 AND status::text = 'Approved'
    ) THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Kept Expense 2 (MUHAMMAD NADEEM HUSSAIN, Rs. 12,000.00) was corrupted or missing!';
    END IF;

    -- Assertion 9G: Verify zero profiles were deleted from public.persons or public.distributors
    IF NOT EXISTS (SELECT 1 FROM public.persons WHERE code = 'ELPRODUCTION#01' OR UPPER(TRIM(name)) LIKE '%SHAOIB%') THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Worker SHAOIB was accidentally deleted from public.persons!';
    END IF;

    IF (SELECT COUNT(*) FROM public.distributors WHERE code NOT IN ('DST-01', 'DST-02', 'ELITEWASH#02', 'elitewash#1')) < 3 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: One or more real distributors were accidentally deleted!';
    END IF;

    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'CLEANUP TRANSACTION VERIFIED SUCCESSFULLY:';
    RAISE NOTICE '    - Test expenses purged:                % records (Total Rs. % purged)', v_del_expenses_count, v_target_delete_amount;
    RAISE NOTICE '    - Remaining expenses in Expenses module: 2 records';
    RAISE NOTICE '        1. SHAOIB (Manufacturer):          Rs. 1,750,000.00 (Approved | %)', v_kept_1_ref;
    RAISE NOTICE '        2. MUHAMMAD NADEEM HUSSAIN (DST):   Rs. 12,000.00 (Approved | %)', v_kept_2_ref;
    RAISE NOTICE '    - Total Approved Expenses:             Rs. 1,762,000.00';
    RAISE NOTICE '    - Total Pending Expenses:              Rs. 0.00';
    RAISE NOTICE '    - Worker & Distributor Profiles:       100%% UNTOUCHED';
    RAISE NOTICE '    - All approved-record triggers:        RESTORED & ACTIVE (EXACT STATE)';
    RAISE NOTICE '======================================================================';

EXCEPTION WHEN OTHERS THEN
    -- Guarantee trigger restoration before rollback using to_regclass
    BEGIN
        IF to_regclass('pg_temp.temp_disabled_triggers') IS NOT NULL THEN
            FOR r_trg IN SELECT * FROM temp_disabled_triggers LOOP
                IF r_trg.original_enabled = 'A' THEN
                    EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
                ELSIF r_trg.original_enabled = 'R' THEN
                    EXECUTE format('ALTER TABLE public.%I ENABLE REPLICA TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
                ELSIF r_trg.original_enabled = 'D' THEN
                    EXECUTE format('ALTER TABLE public.%I DISABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
                ELSE
                    EXECUTE format('ALTER TABLE public.%I ENABLE TRIGGER %I;', r_trg.table_name, r_trg.trigger_name);
                END IF;
            END LOOP;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END;
    RAISE;
END $$;

COMMIT;

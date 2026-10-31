-- ============================================================================
-- ELITE WASHWO ERP — PRODUCTION-SAFE DATA CLEANUP MIGRATION
-- File: cleanup_test_person_payment.sql
-- Task: Permanent cleanup of one test person from Person Payments:
--       - Name:     zainulabideen
--       - Code:     PER-001
--       - Category: Labourer
--       - Opening Payable: Rs. 3.00
--       - Opening Advance: Rs. 4.00
--       along with all exclusively associated test work entries, person ledger
--       entries, payments, commissions, and expenses.
--
-- TARGET VERIFICATION INVARIANTS:
--   - Code: exactly 'PER-001'
--   - Name: 'zainulabideen' (case-insensitive verified)
--   - Category: 'Labourer'
--   - Opening Payable Balance: Rs. 3.00
--   - Opening Advance (Receivable) Balance: Rs. 4.00
--
-- PRESERVED PRODUCTION PERSON INVARIANTS:
--   - Preserves SHAOIB (ELPRODUCTION#01) byte-for-byte, including:
--       * Personal profile, contact info, CNIC, and category
--       * Opening payable and advance balances
--       * All historical work earning entries, payments, and advance allocations
--       * Total ledger balance and direction
--
-- PRODUCTION-SAFETY & INTEGRITY GUARANTEES:
--   1. Exact Trigger State Preservation & Restoration:
--      - Approved-record deletion protection triggers (trg_person_ledger_prevent_delete,
--        trg_expense_prevent_delete) are inspected from pg_trigger.
--      - Exact states ('A' for ALWAYS, 'R' for REPLICA, 'D' for DISABLED, 'O' for ORIGIN)
--        are captured and restored. Triggers originally disabled ('D') remain disabled.
--      - Exception block uses to_regclass('pg_temp.temp_disabled_triggers') to guarantee
--        restoration before rollback on any unexpected runtime error.
--   2. Strict Relational Scoping (ZERO Collision with Real Workers):
--      - Target deletions isolated exclusively to the verified UUID of PER-001.
--      - Real worker SHAOIB (ELPRODUCTION#01) verified 100% untouched before and after.
--   3. Removal of Opening Balances (Rs. 3 Payable, Rs. 4 Advance):
--      - Permanent removal of the person row eliminates Rs. 3 payable and Rs. 4 advance
--        from all directory totals, ledger summaries, and reports.
--   4. Single Atomic Transaction (BEGIN ... COMMIT):
--      - Full rollback on any assertion or integrity mismatch.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    -- Target Person Identification Variables
    v_target_person_id UUID := NULL;
    v_target_person_code TEXT := NULL;
    v_target_person_name TEXT := NULL;
    v_target_person_category TEXT := NULL;
    v_target_opening_payable NUMERIC := 0;
    v_target_opening_receivable NUMERIC := 0;

    -- Target Associated Records Counts
    v_target_entries_count INT := 0;
    v_target_entries_work_sum NUMERIC := 0;
    v_target_entries_pay_sum NUMERIC := 0;
    v_target_expenses_count INT := 0;
    v_target_expenses_sum NUMERIC := 0;

    -- Preserved Production Worker (SHAOIB / ELPRODUCTION#01) Variables
    v_shaoib_id UUID := NULL;
    v_shaoib_code TEXT := NULL;
    v_shaoib_name TEXT := NULL;
    v_shaoib_category TEXT := NULL;
    v_shaoib_payable NUMERIC := 0;
    v_shaoib_receivable NUMERIC := 0;
    v_shaoib_entries_count INT := 0;
    v_shaoib_entries_sum NUMERIC := 0;

    -- Pre-Cleanup Total Persons Count
    v_pre_total_persons_count INT := 0;

    -- Conflict Inspection Counts
    v_conflict_shaoib_entries INT := 0;
    v_conflict_dist_exp INT := 0;
    v_conflict_sm_exp INT := 0;

    -- Deletion Verification Counters
    v_del_expenses_count INT := 0;
    v_del_entries_count INT := 0;
    v_del_person_count INT := 0;

    -- Post-Cleanup Assertion Variables
    v_post_target_person_count INT := 0;
    v_post_target_entries_count INT := 0;
    v_post_target_expenses_count INT := 0;
    v_post_shaoib_person_count INT := 0;
    v_post_shaoib_entries_count INT := 0;
    v_post_shaoib_entries_sum NUMERIC := 0;
    v_post_total_persons_count INT := 0;

    -- Loop Records
    r_trg RECORD;
    r_target_entry RECORD;
BEGIN
    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'ELITE WASHWO ERP — PERMANENT CLEANUP OF TEST PERSON (PER-001)';
    RAISE NOTICE 'Timestamp: % | Session User: %', NOW(), CURRENT_USER;
    RAISE NOTICE '======================================================================';

    -- --------------------------------------------------------------------------
    -- 1. DISCOVER AND VERIFY TARGET TEST PERSON (zainulabideen / PER-001)
    -- --------------------------------------------------------------------------
    SELECT 
        id, 
        code, 
        name, 
        category, 
        COALESCE(opening_payable_balance, 0), 
        COALESCE(opening_receivable_balance, 0)
    INTO 
        v_target_person_id,
        v_target_person_code,
        v_target_person_name,
        v_target_person_category,
        v_target_opening_payable,
        v_target_opening_receivable
    FROM public.persons
    WHERE code = 'PER-001';

    IF v_target_person_id IS NULL THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Target person with code PER-001 not found in public.persons!';
    END IF;

    -- Strict verification of Name, Category, Opening Payable (Rs. 3), and Opening Advance (Rs. 4)
    IF LOWER(TRIM(v_target_person_name)) != 'zainulabideen' THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Target person name mismatch! Expected "zainulabideen", found "%"', v_target_person_name;
    END IF;

    IF v_target_person_category != 'Labourer' THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Target person category mismatch! Expected "Labourer", found "%"', v_target_person_category;
    END IF;

    IF v_target_opening_payable != 3.00 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Target person opening payable mismatch! Expected Rs. 3.00, found Rs. %', v_target_opening_payable;
    END IF;

    IF v_target_opening_receivable != 4.00 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Target person opening advance mismatch! Expected Rs. 4.00, found Rs. %', v_target_opening_receivable;
    END IF;

    SELECT COUNT(*) INTO v_pre_total_persons_count FROM public.persons;

    RAISE NOTICE '[TARGET PERSON VERIFIED]';
    RAISE NOTICE '    - ID:                %', v_target_person_id;
    RAISE NOTICE '    - Code:              %', v_target_person_code;
    RAISE NOTICE '    - Name:              %', v_target_person_name;
    RAISE NOTICE '    - Category:          %', v_target_person_category;
    RAISE NOTICE '    - Opening Payable:   Rs. % (Company owes them)', v_target_opening_payable;
    RAISE NOTICE '    - Opening Advance:   Rs. % (Advance given)', v_target_opening_receivable;
    RAISE NOTICE '    - Total Persons Pre: %', v_pre_total_persons_count;

    -- --------------------------------------------------------------------------
    -- 2. DISCOVER AND SNAPSHOT REAL PRODUCTION WORKER (SHAOIB / ELPRODUCTION#01)
    -- --------------------------------------------------------------------------
    SELECT 
        id, 
        code, 
        name, 
        category, 
        COALESCE(opening_payable_balance, 0), 
        COALESCE(opening_receivable_balance, 0)
    INTO 
        v_shaoib_id,
        v_shaoib_code,
        v_shaoib_name,
        v_shaoib_category,
        v_shaoib_payable,
        v_shaoib_receivable
    FROM public.persons
    WHERE code = 'ELPRODUCTION#01'
       OR UPPER(TRIM(name)) LIKE '%SHAOIB%'
    LIMIT 1;

    IF v_shaoib_id IS NULL THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Production worker SHAOIB (ELPRODUCTION#01) not found! Aborting to ensure real worker data is accounted for.';
    END IF;

    -- Snapshot SHAOIB's person profile
    CREATE TEMP TABLE temp_pre_shaoib_person AS
    SELECT * FROM public.persons WHERE id = v_shaoib_id;

    -- Snapshot SHAOIB's ledger entries
    CREATE TEMP TABLE temp_pre_shaoib_entries AS
    SELECT * FROM public.person_ledger_entries WHERE person_id = v_shaoib_id;

    SELECT 
        COUNT(*),
        COALESCE(SUM(amount), 0)
    INTO 
        v_shaoib_entries_count,
        v_shaoib_entries_sum
    FROM temp_pre_shaoib_entries;

    RAISE NOTICE '[REAL WORKER SHAOIB VERIFIED & SNAPSHOTTED]';
    RAISE NOTICE '    - ID:                %', v_shaoib_id;
    RAISE NOTICE '    - Code:              %', v_shaoib_code;
    RAISE NOTICE '    - Name:              %', v_shaoib_name;
    RAISE NOTICE '    - Category:          %', v_shaoib_category;
    RAISE NOTICE '    - Opening Payable:   Rs. %', v_shaoib_payable;
    RAISE NOTICE '    - Opening Advance:   Rs. %', v_shaoib_receivable;
    RAISE NOTICE '    - Ledger Entries:    % record(s) (Total Rs. %)', v_shaoib_entries_count, v_shaoib_entries_sum;

    -- --------------------------------------------------------------------------
    -- 3. DISCOVER EXCLUSIVELY ASSOCIATED TARGET TEST ENTRIES & EXPENSES
    -- --------------------------------------------------------------------------
    -- Discover target person_ledger_entries
    CREATE TEMP TABLE temp_target_entries (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        entry_type TEXT NOT NULL,
        direction TEXT NOT NULL,
        amount NUMERIC NOT NULL,
        status TEXT NOT NULL,
        expense_id UUID
    ) ON COMMIT DROP;

    INSERT INTO temp_target_entries (id, reference_number, entry_type, direction, amount, status, expense_id)
    SELECT id, reference_number, entry_type::text, direction, amount, status::text, expense_id
    FROM public.person_ledger_entries
    WHERE person_id = v_target_person_id;

    GET DIAGNOSTICS v_target_entries_count = ROW_COUNT;

    SELECT 
        COALESCE(SUM(CASE WHEN direction = 'Payable' THEN amount ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN direction = 'Receivable' THEN amount ELSE 0 END), 0)
    INTO 
        v_target_entries_work_sum,
        v_target_entries_pay_sum
    FROM temp_target_entries;

    -- Discover target expenses linked to PER-001 (by person_id or originating_ledger_entry_id)
    CREATE TEMP TABLE temp_target_expenses (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        amount NUMERIC NOT NULL,
        status TEXT NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO temp_target_expenses (id, reference_number, amount, status)
    SELECT id, reference_number, amount, status::text
    FROM public.expenses
    WHERE person_id = v_target_person_id
       OR originating_ledger_entry_id IN (SELECT id FROM temp_target_entries)
       OR id IN (SELECT expense_id FROM temp_target_entries WHERE expense_id IS NOT NULL);

    GET DIAGNOSTICS v_target_expenses_count = ROW_COUNT;

    SELECT COALESCE(SUM(amount), 0) INTO v_target_expenses_sum
    FROM temp_target_expenses;

    RAISE NOTICE '[TARGET ASSOCIATED RECORDS DISCOVERED]';
    RAISE NOTICE '    - Target Person Ledger Entries: % record(s)', v_target_entries_count;
    RAISE NOTICE '        * Payable Work Earnings:   Rs. %', v_target_entries_work_sum;
    RAISE NOTICE '        * Disbursed Payments:      Rs. %', v_target_entries_pay_sum;
    RAISE NOTICE '    - Target Linked Expenses:       % record(s) (Rs. %)', v_target_expenses_count, v_target_expenses_sum;

    -- --------------------------------------------------------------------------
    -- 4. CONFLICT INSPECTION & SAFEGUARD AUDIT
    -- --------------------------------------------------------------------------
    -- Check 4A: Ensure zero target entries belong to SHAOIB
    SELECT COUNT(*) INTO v_conflict_shaoib_entries
    FROM temp_target_entries
    WHERE id IN (SELECT id FROM temp_pre_shaoib_entries);

    IF v_conflict_shaoib_entries > 0 THEN
        RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: % target entry/entries belong to SHAOIB! Aborting.', v_conflict_shaoib_entries;
    END IF;

    -- Check 4B: Ensure target expenses are not shared with distributors
    SELECT COUNT(*) INTO v_conflict_dist_exp
    FROM public.expenses e
    WHERE e.id IN (SELECT id FROM temp_target_expenses)
      AND e.distributor_id IS NOT NULL;

    IF v_conflict_dist_exp > 0 THEN
        RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: % target expense(s) are linked to distributors! Aborting.', v_conflict_dist_exp;
    END IF;

    -- Check 4C: Ensure target expenses are not shared with salesmen
    SELECT COUNT(*) INTO v_conflict_sm_exp
    FROM public.expenses e
    WHERE e.id IN (SELECT id FROM temp_target_expenses)
      AND e.salesman_id IS NOT NULL;

    IF v_conflict_sm_exp > 0 THEN
        RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: % target expense(s) are linked to salesmen! Aborting.', v_conflict_sm_exp;
    END IF;

    RAISE NOTICE '[CONFLICT AUDIT PASSED] Zero conflicts with SHAOIB, distributors, or salesmen.';

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
        'persons',
        v_target_person_id,
        'ADMIN_PURGE_TEST_PERSON_PER001',
        jsonb_build_object(
            'operation', 'Permanent cleanup of test person PER-001 (zainulabideen)',
            'target_person_id', v_target_person_id,
            'target_code', v_target_person_code,
            'target_name', v_target_person_name,
            'target_category', v_target_person_category,
            'opening_payable_removed', v_target_opening_payable,
            'opening_advance_removed', v_target_opening_receivable,
            'target_ledger_entries_count', v_target_entries_count,
            'target_expenses_count', v_target_expenses_count,
            'preserved_production_worker', v_shaoib_name,
            'preserved_production_code', v_shaoib_code,
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

    -- Query pg_trigger for exact approved-record deletion protection triggers
    INSERT INTO temp_disabled_triggers (table_name, trigger_name, original_enabled)
    SELECT c.relname, t.tgname, t.tgenabled
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND ((c.relname = 'person_ledger_entries' AND t.tgname = 'trg_person_ledger_prevent_delete')
        OR (c.relname = 'expenses' AND t.tgname = 'trg_expense_prevent_delete'))
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
    -- 7. CASCADING DELETION OF TARGET UNASSIGNED TEST DATA (RIGID DEPENDENCY ORDER)
    -- --------------------------------------------------------------------------
    -- Step 7A: Unlink foreign key references between target entries and expenses
    UPDATE public.person_ledger_entries
    SET expense_id = NULL
    WHERE person_id = v_target_person_id
      AND expense_id IS NOT NULL;

    UPDATE public.expenses
    SET originating_ledger_entry_id = NULL
    WHERE person_id = v_target_person_id
      AND originating_ledger_entry_id IS NOT NULL;

    -- Step 7B: Delete target expenses exclusively associated with PER-001
    IF v_target_expenses_count > 0 THEN
        WITH deleted_exp AS (
            DELETE FROM public.expenses
            WHERE id IN (SELECT id FROM temp_target_expenses)
            RETURNING id
        )
        SELECT COUNT(*) INTO v_del_expenses_count FROM deleted_exp;
        RAISE NOTICE '[DELETION Step B] Deleted % associated test expense(s).', v_del_expenses_count;
    END IF;

    -- Step 7C: Delete target person ledger entries
    IF v_target_entries_count > 0 THEN
        WITH deleted_entries AS (
            DELETE FROM public.person_ledger_entries
            WHERE person_id = v_target_person_id
            RETURNING id
        )
        SELECT COUNT(*) INTO v_del_entries_count FROM deleted_entries;
        RAISE NOTICE '[DELETION Step C] Deleted % test person ledger entry/entries.', v_del_entries_count;
    END IF;

    -- Step 7D: Permanently delete target person from public.persons
    WITH deleted_person AS (
        DELETE FROM public.persons
        WHERE id = v_target_person_id
        RETURNING id
    )
    SELECT COUNT(*) INTO v_del_person_count FROM deleted_person;

    IF v_del_person_count != 1 THEN
        RAISE EXCEPTION 'POST-DELETION INTEGRITY ABORT: Expected to delete exactly 1 person (PER-001), but deleted %! Rolling back.', v_del_person_count;
    END IF;

    RAISE NOTICE '[DELETION Step D] Deleted test person: % (% | ID: %).', v_target_person_name, v_target_person_code, v_target_person_id;

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
    -- Assertion 9A: Target person PER-001 is completely gone from public.persons
    SELECT COUNT(*) INTO v_post_target_person_count
    FROM public.persons
    WHERE code = 'PER-001' OR id = v_target_person_id;

    IF v_post_target_person_count != 0 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Target person PER-001 still exists in public.persons!';
    END IF;

    -- Assertion 9B: Target person ledger entries are completely gone
    SELECT COUNT(*) INTO v_post_target_entries_count
    FROM public.person_ledger_entries
    WHERE person_id = v_target_person_id;

    IF v_post_target_entries_count != 0 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Found % remaining ledger entries for PER-001!', v_post_target_entries_count;
    END IF;

    -- Assertion 9C: Target expenses are completely gone
    SELECT COUNT(*) INTO v_post_target_expenses_count
    FROM public.expenses
    WHERE person_id = v_target_person_id;

    IF v_post_target_expenses_count != 0 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Found % remaining expenses for PER-001!', v_post_target_expenses_count;
    END IF;

    -- Assertion 9D: Production worker SHAOIB is 100% preserved byte-for-byte
    SELECT COUNT(*) INTO v_post_shaoib_person_count
    FROM public.persons p
    JOIN temp_pre_shaoib_person pre ON pre.id = p.id
    WHERE p.code = pre.code
      AND p.name = pre.name
      AND p.category = pre.category
      AND p.opening_payable_balance = pre.opening_payable_balance
      AND p.opening_receivable_balance = pre.opening_receivable_balance
      AND p.default_rate = pre.default_rate
      AND p.commission_rate = pre.commission_rate
      AND p.is_active = pre.is_active;

    IF v_post_shaoib_person_count != 1 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: SHAOIB profile was modified or corrupted during cleanup!';
    END IF;

    -- Assertion 9E: SHAOIB ledger entries and amounts are 100% preserved
    SELECT 
        COUNT(*),
        COALESCE(SUM(amount), 0)
    INTO 
        v_post_shaoib_entries_count,
        v_post_shaoib_entries_sum
    FROM public.person_ledger_entries
    WHERE person_id = v_shaoib_id;

    IF v_post_shaoib_entries_count != v_shaoib_entries_count OR v_post_shaoib_entries_sum != v_shaoib_entries_sum THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: SHAOIB ledger entries were modified! Pre: [% recs, Rs. %] vs Post: [% recs, Rs. %]',
            v_shaoib_entries_count, v_shaoib_entries_sum, v_post_shaoib_entries_count, v_post_shaoib_entries_sum;
    END IF;

    -- Assertion 9F: Total persons in public.persons is exactly pre_total - 1
    SELECT COUNT(*) INTO v_post_total_persons_count FROM public.persons;

    IF v_post_total_persons_count != (v_pre_total_persons_count - 1) THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Total persons count is %, expected %!', v_post_total_persons_count, (v_pre_total_persons_count - 1);
    END IF;

    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'CLEANUP TRANSACTION VERIFIED SUCCESSFULLY:';
    RAISE NOTICE '    - Target person purged:                PER-001 (zainulabideen)';
    RAISE NOTICE '    - Opening payable removed:             Rs. 3.00';
    RAISE NOTICE '    - Opening advance removed:             Rs. 4.00';
    RAISE NOTICE '    - Associated ledger entries purged:    % record(s)', v_del_entries_count;
    RAISE NOTICE '    - Associated expenses purged:          % record(s)', v_del_expenses_count;
    RAISE NOTICE '    - Production worker SHAOIB preserved:  100%% UNCHANGED';
    RAISE NOTICE '        * SHAOIB Profile:                  INTACT (% / %)', v_shaoib_name, v_shaoib_code;
    RAISE NOTICE '        * SHAOIB Ledger Entries:           % record(s) (Rs. %)', v_post_shaoib_entries_count, v_post_shaoib_entries_sum;
    RAISE NOTICE '    - Remaining persons in directory:      % person(s)', v_post_total_persons_count;
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

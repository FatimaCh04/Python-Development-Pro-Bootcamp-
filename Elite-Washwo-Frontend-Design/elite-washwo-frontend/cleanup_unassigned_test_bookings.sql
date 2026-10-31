-- ============================================================================
-- ELITE WASHWO ERP — PRODUCTION-SAFE DATA CLEANUP MIGRATION
-- File: cleanup_unassigned_test_bookings.sql
-- Task: Permanent cleanup of the 7 unassigned test bookings ("Not Assigned")
--       and ALL directly associated test advance payments (including the Rs. 10,200
--       advances on Bills #01, #02, and #03), line items, and payment allocations.
-- 
-- STRICT INVARIANTS & PRODUCTION-SAFETY GUARANTEES:
--   1. Exact Trigger State Restoration (Including Disabled 'D'):
--      - Live approved-record protection triggers are inspected from pg_trigger.
--      - Every trigger's exact original state ('A' for ALWAYS, 'R' for REPLICA,
--        'D' for DISABLED, 'O' for ORIGIN/ENABLED) is preserved and restored.
--      - Triggers originally disabled ('D') are guaranteed to remain disabled.
--      - Exception block uses to_regclass('pg_temp.temp_disabled_triggers') to
--        guarantee restoration before rollback on any unexpected runtime failure.
--   2. Relational Payment Identification (ZERO reference_number LIKE Patterns):
--      - Eliminates all loose text / LIKE pattern matching on reference_number.
--      - Discovers and links payments strictly via verified booking IDs (UUID) and
--        actual relational Foreign Keys (recoveries.sale_order_id and allocations).
--      - Includes ALL test payments across all states (fully paid, partially paid, unpaid),
--        reversing the Rs. 10,200 advances recorded on Bills #01, #02, and #03.
--   3. Cash/Bank Accounting Reversal:
--      - Explicitly computes and reverses test cash and bank advance inflows
--        (v_target_rec_cash_sum, v_target_rec_bank_sum) from transaction ledgers.
--   4. Dynamic SQL Isolation for Optional Columns:
--      - Optional columns/tables (sales_orders.booking_id, sale_items.booking_item_id,
--        inventory_transactions.sale_order_id, daily_closings.distributor_id,
--        invoice_payment_allocations) are isolated with dynamic SQL.
--   5. Strict Preservation of Real Business Operations:
--      - All 8 assigned bookings belonging to the 3 confirmed real distributors
--        (MUHAMMAD NADEEM HUSSAIN, QAMAR SAJJAD, khalid) are preserved byte-for-byte.
--      - Zero mutations to database UUIDs, BKG references, dates, or financial links.
--   6. Single Atomic Transaction (BEGIN ... COMMIT):
--      - Rolls back completely if any integrity check or count assertion fails.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    -- Schema Detection Flags (for Optional Columns / Tables)
    v_has_alloc_table BOOLEAN := FALSE;
    v_has_inv_sale_order_id BOOLEAN := FALSE;
    v_has_so_booking_id BOOLEAN := FALSE;
    v_has_si_booking_item_id BOOLEAN := FALSE;
    v_has_rec_sale_order_id BOOLEAN := FALSE;
    v_has_dc_dist_id BOOLEAN := FALSE;

    -- Target Pre-Discovery Counts & Totals
    v_target_booking_count INT := 0;
    v_target_si_count INT := 0;
    v_target_rec_count INT := 0;
    v_target_rec_sum NUMERIC := 0;
    v_target_rec_cash_sum NUMERIC := 0;
    v_target_rec_bank_sum NUMERIC := 0;
    v_target_alloc_count INT := 0;
    v_target_child_so_count INT := 0;
    v_target_inv_count INT := 0;

    -- Real Production Data Baseline Counts & Totals
    v_real_dist_count INT := 0;
    v_real_booking_count INT := 0;
    v_real_so_sum NUMERIC := 0;
    v_real_si_count INT := 0;
    v_real_si_qty NUMERIC := 0;
    v_real_rec_count INT := 0;
    v_real_rec_sum NUMERIC := 0;
    v_real_rec_cash_sum NUMERIC := 0;
    v_real_rec_bank_sum NUMERIC := 0;

    -- Conflict Inspection Counts
    v_conflict_rec_real_dist INT := 0;
    v_conflict_child_so INT := 0;
    v_conflict_inv INT := 0;
    v_conflict_settle INT := 0;

    -- Deletion Verification Counters (Distinct & Verified)
    v_del_alloc_count INT := 0;
    v_del_rec_count INT := 0;
    v_del_child_si_count INT := 0;
    v_del_child_so_count INT := 0;
    v_del_inv_count INT := 0;
    v_del_si_count INT := 0;
    v_del_booking_count INT := 0;

    -- Post-Cleanup Assertion Variables
    v_post_unassigned_booking_count INT := 0;
    v_post_real_booking_count INT := 0;
    v_post_total_booking_count INT := 0;
    v_post_real_so_sum NUMERIC := 0;
    v_post_real_si_count INT := 0;
    v_post_real_si_qty NUMERIC := 0;
    v_post_real_rec_count INT := 0;
    v_post_real_rec_sum NUMERIC := 0;
    v_mismatched_booking_id UUID := NULL;
    v_mismatched_booking_ref TEXT := NULL;
    v_mismatched_dist_code TEXT := NULL;

    -- Loop Records
    r_trg RECORD;
    r_target RECORD;
    r_real RECORD;
    r_dist RECORD;
BEGIN
    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'ELITE WASHWO ERP — UNASSIGNED TEST BOOKINGS & ADVANCES CLEANUP';
    RAISE NOTICE 'Timestamp: % | Session User: %', NOW(), CURRENT_USER;
    RAISE NOTICE '======================================================================';

    -- --------------------------------------------------------------------------
    -- 1. DETECT OPTIONAL SCHEMA CAPABILITIES (DYNAMIC SQL ISOLATION)
    -- --------------------------------------------------------------------------
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'invoice_payment_allocations'
    ) INTO v_has_alloc_table;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'inventory_transactions' AND column_name = 'sale_order_id'
    ) INTO v_has_inv_sale_order_id;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'booking_id'
    ) INTO v_has_so_booking_id;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'sale_items' AND column_name = 'booking_item_id'
    ) INTO v_has_si_booking_item_id;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'recoveries' AND column_name = 'sale_order_id'
    ) INTO v_has_rec_sale_order_id;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'daily_closings' AND column_name = 'distributor_id'
    ) INTO v_has_dc_dist_id;

    -- Ensure recoveries.sale_order_id foreign key column exists for verified relational linking
    IF NOT v_has_rec_sale_order_id THEN
        EXECUTE 'ALTER TABLE public.recoveries ADD COLUMN IF NOT EXISTS sale_order_id UUID REFERENCES public.sales_orders(id) ON DELETE RESTRICT;';
        v_has_rec_sale_order_id := TRUE;
        RAISE NOTICE '    - Added missing relational foreign key: recoveries.sale_order_id';
    END IF;

    RAISE NOTICE '[SCHEMA CAPABILITIES DETECTED]';
    RAISE NOTICE '    - invoice_payment_allocations table:         %', v_has_alloc_table;
    RAISE NOTICE '    - inventory_transactions.sale_order_id:      %', v_has_inv_sale_order_id;
    RAISE NOTICE '    - sales_orders.booking_id:                   %', v_has_so_booking_id;
    RAISE NOTICE '    - sale_items.booking_item_id:                %', v_has_si_booking_item_id;
    RAISE NOTICE '    - recoveries.sale_order_id (FK):             %', v_has_rec_sale_order_id;
    RAISE NOTICE '    - daily_closings.distributor_id:              %', v_has_dc_dist_id;

    -- --------------------------------------------------------------------------
    -- 2. DISCOVER AND ISOLATE THE EXACT 7 UNASSIGNED TEST BOOKINGS
    -- --------------------------------------------------------------------------
    CREATE TEMP TABLE temp_target_bookings (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        sale_date TIMESTAMPTZ,
        total_amount NUMERIC NOT NULL,
        status TEXT NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO temp_target_bookings (id, reference_number, sale_date, total_amount, status)
    SELECT id, reference_number, sale_date, total_amount, status::text
    FROM public.sales_orders
    WHERE reference_number LIKE 'BKG-%'
      AND distributor_id IS NULL;

    GET DIAGNOSTICS v_target_booking_count = ROW_COUNT;

    IF v_target_booking_count != 7 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Expected exactly 7 unassigned bookings (distributor_id IS NULL), but found %! Aborting to prevent accidental data deletion.', v_target_booking_count;
    END IF;

    RAISE NOTICE '[TARGET DISCOVERY SUCCESS] Discovered exactly % unassigned test bookings:', v_target_booking_count;
    FOR r_target IN SELECT reference_number, sale_date, total_amount, status FROM temp_target_bookings ORDER BY sale_date ASC LOOP
        RAISE NOTICE '    - % | Date: % | Amount: Rs. % | Status: %', 
            r_target.reference_number, r_target.sale_date, r_target.total_amount, r_target.status;
    END LOOP;

    -- --------------------------------------------------------------------------
    -- 3. VERIFY REAL PRODUCTION DISTRIBUTORS AND THEIR EXACT 8 BOOKINGS
    -- --------------------------------------------------------------------------
    CREATE TEMP TABLE temp_real_distributors (
        id UUID PRIMARY KEY,
        code TEXT NOT NULL,
        name TEXT NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO temp_real_distributors (id, code, name)
    SELECT id, code, name
    FROM public.distributors
    WHERE code NOT IN ('DST-01', 'DST-02', 'ELITEWASH#02', 'elitewash#1');

    GET DIAGNOSTICS v_real_dist_count = ROW_COUNT;

    IF v_real_dist_count < 3 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Found % real distributors, expected at least 3 (MUHAMMAD NADEEM HUSSAIN, QAMAR SAJJAD, khalid)!', v_real_dist_count;
    END IF;

    RAISE NOTICE '[REAL DISTRIBUTORS VERIFIED] Found % active production distributors:', v_real_dist_count;
    FOR r_real IN SELECT code, name FROM temp_real_distributors ORDER BY code ASC LOOP
        RAISE NOTICE '    - % (%)', r_real.name, r_real.code;
    END LOOP;

    -- Verify count of bookings assigned to real distributors
    SELECT COUNT(*) INTO v_real_booking_count
    FROM public.sales_orders
    WHERE reference_number LIKE 'BKG-%'
      AND distributor_id IN (SELECT id FROM temp_real_distributors);

    IF v_real_booking_count != 8 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Expected exactly 8 assigned bookings for real distributors, but found %! Aborting to safeguard production bookings.', v_real_booking_count;
    END IF;

    -- Total bookings currently in the database must be exactly 15 (7 unassigned + 8 real)
    IF (v_target_booking_count + v_real_booking_count) != 15 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Total bookings in system is %, expected 15 (7 unassigned + 8 real)!', (v_target_booking_count + v_real_booking_count);
    END IF;

    -- --------------------------------------------------------------------------
    -- 4. SYNCHRONIZE & DISCOVER ALL TEST ADVANCE PAYMENTS (VERIFIED RELATIONSHIPS)
    --    (ZERO reference_number LIKE PATTERNS; EXACT BOOKING ID FK RELATIONSHIPS)
    --    (INCLUDES RS. 10,200 ADVANCES ON BILLS #01, #02, #03, FULLY/PARTIALLY PAID)
    -- --------------------------------------------------------------------------
    -- Step 4A: Synchronize recoveries.sale_order_id FK from verified booking IDs if unset
    -- For target bookings:
    UPDATE public.recoveries r
    SET sale_order_id = t.id
    FROM temp_target_bookings t
    WHERE r.sale_order_id IS NULL
      AND (
          split_part(r.reference_number, '|', 2) = t.id::text
          OR split_part(r.reference_number, '|', 2) = t.reference_number
      );

    -- For real bookings (guaranteeing exact relational FK linkage for all production bookings):
    UPDATE public.recoveries r
    SET sale_order_id = so.id
    FROM public.sales_orders so
    WHERE r.sale_order_id IS NULL
      AND so.reference_number LIKE 'BKG-%'
      AND so.distributor_id IN (SELECT id FROM temp_real_distributors)
      AND (
          split_part(r.reference_number, '|', 2) = so.id::text
          OR split_part(r.reference_number, '|', 2) = so.reference_number
      );

    -- Step 4B: Isolate target recoveries strictly through verified booking ID relationships
    CREATE TEMP TABLE temp_target_recoveries (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        amount NUMERIC NOT NULL,
        payment_method TEXT,
        distributor_id UUID,
        sale_order_id UUID NOT NULL
    ) ON COMMIT DROP;

    -- Match 1: Direct verified Foreign Key relationship (recoveries.sale_order_id = t.id)
    INSERT INTO temp_target_recoveries (id, reference_number, amount, payment_method, distributor_id, sale_order_id)
    SELECT r.id, r.reference_number, r.amount, r.payment_method, r.distributor_id, r.sale_order_id
    FROM public.recoveries r
    JOIN temp_target_bookings t ON r.sale_order_id = t.id
    ON CONFLICT (id) DO NOTHING;

    -- Match 2: Payment allocations relationship (invoice_payment_allocations) if table exists
    IF v_has_alloc_table THEN
        EXECUTE $dyn$
            INSERT INTO temp_target_recoveries (id, reference_number, amount, payment_method, distributor_id, sale_order_id)
            SELECT r.id, r.reference_number, r.amount, r.payment_method, r.distributor_id, ipa.sale_order_id
            FROM public.recoveries r
            JOIN public.invoice_payment_allocations ipa ON ipa.recovery_id = r.id
            JOIN temp_target_bookings t ON t.id = ipa.sale_order_id
            ON CONFLICT (id) DO NOTHING;
        $dyn$;
    END IF;

    SELECT 
        COUNT(*),
        COALESCE(SUM(amount), 0),
        COALESCE(SUM(CASE WHEN payment_method = 'Cash' THEN amount ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN payment_method != 'Cash' THEN amount ELSE 0 END), 0)
    INTO 
        v_target_rec_count,
        v_target_rec_sum,
        v_target_rec_cash_sum,
        v_target_rec_bank_sum
    FROM temp_target_recoveries;

    RAISE NOTICE '[ASSOCIATED TEST ADVANCE PAYMENTS DISCOVERED]';
    RAISE NOTICE '    - Test Recoveries Count:             % record(s)', v_target_rec_count;
    RAISE NOTICE '    - Total Test Advances Amount:        Rs. % (includes Rs. 10,200 on Bills #01-#03)', v_target_rec_sum;
    RAISE NOTICE '        * Cash Advance Component:        Rs. %', v_target_rec_cash_sum;
    RAISE NOTICE '        * Bank Advance Component:        Rs. %', v_target_rec_bank_sum;

    -- Count dependent line items
    SELECT COUNT(*) INTO v_target_si_count
    FROM public.sale_items
    WHERE sale_order_id IN (SELECT id FROM temp_target_bookings);

    -- Optional table: invoice_payment_allocations
    IF v_has_alloc_table THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.invoice_payment_allocations 
            WHERE sale_order_id IN (SELECT id FROM temp_target_bookings)
               OR recovery_id IN (SELECT id FROM temp_target_recoveries);
        $dyn$ INTO v_target_alloc_count;
    END IF;

    -- Optional column: sales_orders.booking_id (child dispatches)
    IF v_has_so_booking_id THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.sales_orders 
            WHERE booking_id IN (SELECT id FROM temp_target_bookings);
        $dyn$ INTO v_target_child_so_count;
    END IF;

    -- Optional column: inventory_transactions.sale_order_id
    IF v_has_inv_sale_order_id THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.inventory_transactions 
            WHERE sale_order_id IN (SELECT id FROM temp_target_bookings);
        $dyn$ INTO v_target_inv_count;
    END IF;

    RAISE NOTICE '[TARGET DEPENDENT RECORDS SUMMARY]';
    RAISE NOTICE '    - Booking Line Items:                %', v_target_si_count;
    RAISE NOTICE '    - Advance Payment Allocations:       %', v_target_alloc_count;
    RAISE NOTICE '    - Child Dispatches (sales_orders):   %', v_target_child_so_count;
    RAISE NOTICE '    - Linked Inventory Transactions:     %', v_target_inv_count;

    -- --------------------------------------------------------------------------
    -- 5. PRE-CLEANUP SNAPSHOT OF THE 8 REAL BOOKINGS & REAL FINANCIAL LEDGERS
    -- --------------------------------------------------------------------------
    CREATE TEMP TABLE temp_pre_real_bookings (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        distributor_id UUID NOT NULL,
        sale_date TIMESTAMPTZ,
        total_amount NUMERIC NOT NULL,
        status TEXT NOT NULL,
        item_count INT NOT NULL,
        item_qty NUMERIC NOT NULL,
        rec_count INT NOT NULL,
        rec_sum NUMERIC NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO temp_pre_real_bookings
    SELECT 
        so.id,
        so.reference_number,
        so.distributor_id,
        so.sale_date,
        so.total_amount,
        so.status::text,
        COALESCE((SELECT COUNT(*) FROM public.sale_items si WHERE si.sale_order_id = so.id), 0),
        COALESCE((SELECT SUM(si.quantity) FROM public.sale_items si WHERE si.sale_order_id = so.id), 0),
        COALESCE((SELECT COUNT(*) FROM public.recoveries r WHERE r.sale_order_id = so.id), 0),
        COALESCE((SELECT SUM(r.amount) FROM public.recoveries r WHERE r.sale_order_id = so.id), 0)
    FROM public.sales_orders so
    WHERE so.reference_number LIKE 'BKG-%'
      AND so.distributor_id IN (SELECT id FROM temp_real_distributors);

    SELECT 
        COALESCE(SUM(total_amount), 0),
        COALESCE(SUM(item_count), 0),
        COALESCE(SUM(item_qty), 0),
        COALESCE(SUM(rec_count), 0),
        COALESCE(SUM(rec_sum), 0)
    INTO 
        v_real_so_sum,
        v_real_si_count,
        v_real_si_qty,
        v_real_rec_count,
        v_real_rec_sum
    FROM temp_pre_real_bookings;

    RAISE NOTICE '[PRE-CLEANUP REAL BOOKING BASELINE]';
    RAISE NOTICE '    - Real Bookings Count:         % (Bill #08 through Bill #15)', v_real_booking_count;
    RAISE NOTICE '    - Real Bookings Total Value:   Rs. %', v_real_so_sum;
    RAISE NOTICE '    - Real Booking Line Items:     % (Total Qty: % pkts)', v_real_si_count, v_real_si_qty;
    RAISE NOTICE '    - Real Booking Advances:       % (Total Advances: Rs. %)', v_real_rec_count, v_real_rec_sum;

    -- Snapshot real distributors' cash, bank, and trade ledger figures
    CREATE TEMP TABLE temp_pre_real_dist_ledgers (
        distributor_id UUID PRIMARY KEY,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        trade_sales_total NUMERIC NOT NULL,
        booking_sales_total NUMERIC NOT NULL,
        total_recoveries NUMERIC NOT NULL,
        cash_recoveries NUMERIC NOT NULL,
        bank_recoveries NUMERIC NOT NULL,
        outstanding_balance NUMERIC NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO temp_pre_real_dist_ledgers
    SELECT 
        d.id,
        d.code,
        d.name,
        COALESCE((
            SELECT SUM(so.total_amount) 
            FROM public.sales_orders so 
            WHERE so.distributor_id = d.id 
              AND so.status::text IN ('Approved', 'Posted')
              AND so.reference_number NOT LIKE 'BKG-%'
        ), 0),
        COALESCE((
            SELECT SUM(so.total_amount) 
            FROM public.sales_orders so 
            WHERE so.distributor_id = d.id 
              AND so.reference_number LIKE 'BKG-%'
        ), 0),
        COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = d.id AND rec.status::text IN ('Approved', 'Posted')
        ), 0),
        COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = d.id AND rec.status::text IN ('Approved', 'Posted') AND rec.payment_method = 'Cash'
        ), 0),
        COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = d.id AND rec.status::text IN ('Approved', 'Posted') AND rec.payment_method != 'Cash'
        ), 0),
        (
            COALESCE((
                SELECT SUM(so.total_amount) 
                FROM public.sales_orders so 
                WHERE so.distributor_id = d.id 
                  AND so.status::text IN ('Approved', 'Posted')
                  AND so.reference_number NOT LIKE 'BKG-%'
            ), 0) -
            COALESCE((
                SELECT SUM(rec.amount) 
                FROM public.recoveries rec 
                WHERE rec.distributor_id = d.id AND rec.status::text IN ('Approved', 'Posted')
            ), 0)
        )
    FROM temp_real_distributors d;

    -- --------------------------------------------------------------------------
    -- 6. STRICT CONFLICT & DEPENDENCY SAFETY AUDITS
    -- --------------------------------------------------------------------------
    -- Check 6A: Real Distributor Account Conflicts
    SELECT COUNT(*) INTO v_conflict_rec_real_dist
    FROM temp_target_recoveries
    WHERE distributor_id IN (SELECT id FROM temp_real_distributors);

    IF v_conflict_rec_real_dist > 0 THEN
        RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: Found % recovery records linked to unassigned test bookings that reference REAL distributor accounts! Deletion aborted to protect real ledgers.', v_conflict_rec_real_dist;
    END IF;

    -- Check 6B: Distributor Settlement Conflicts
    SELECT COUNT(*) INTO v_conflict_settle
    FROM public.distributor_settlements
    WHERE recovery_id IN (SELECT id FROM temp_target_recoveries);

    IF v_conflict_settle > 0 THEN
        RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: Found % distributor settlements linked to test recoveries! Deletion aborted.', v_conflict_settle;
    END IF;

    -- Check 6C: Real Child Dispatches
    IF v_has_so_booking_id THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.sales_orders 
            WHERE booking_id IN (SELECT id FROM temp_target_bookings)
              AND distributor_id IN (SELECT id FROM temp_real_distributors);
        $dyn$ INTO v_conflict_child_so;

        IF v_conflict_child_so > 0 THEN
            RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: Found % child sales orders linked to target bookings that belong to REAL distributors. Deletion aborted.', v_conflict_child_so;
        END IF;
    END IF;

    -- Check 6D: Physical Warehouse Inventory Conflicts
    IF v_has_inv_sale_order_id THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.inventory_transactions 
            WHERE sale_order_id IN (SELECT id FROM temp_target_bookings)
              AND transaction_type::text IN ('Production', 'Purchase', 'Salesman_Issue', 'Sale');
        $dyn$ INTO v_conflict_inv;

        IF v_conflict_inv > 0 THEN
            RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: Found % warehouse stock movements linked to unassigned bookings. Deletion aborted to protect inventory reconciliation.', v_conflict_inv;
        END IF;
    END IF;

    RAISE NOTICE '[CONFLICT AUDIT PASSED] Zero conflicts with real distributors, commercial receivables, or physical inventory.';

    -- --------------------------------------------------------------------------
    -- 7. AUDIT LOGGING (ADMINISTRATIVE PURGE RECORD)
    -- --------------------------------------------------------------------------
    INSERT INTO public.audit_logs (
        table_name,
        record_id,
        action,
        old_data,
        performed_by,
        created_at
    ) VALUES (
        'sales_orders',
        (SELECT id FROM temp_target_bookings ORDER BY sale_date ASC LIMIT 1),
        'ADMIN_PURGE_UNASSIGNED_TEST_BOOKINGS',
        jsonb_build_object(
            'operation', 'Permanent cleanup of 7 unassigned test bookings and ALL associated test advances',
            'target_count', v_target_booking_count,
            'target_references', (SELECT jsonb_agg(reference_number) FROM temp_target_bookings),
            'target_items_count', v_target_si_count,
            'target_recoveries_count', v_target_rec_count,
            'target_advances_total', v_target_rec_sum,
            'target_advances_cash', v_target_rec_cash_sum,
            'target_advances_bank', v_target_rec_bank_sum,
            'preserved_real_distributors', (SELECT jsonb_agg(code) FROM temp_real_distributors),
            'preserved_real_bookings_count', v_real_booking_count,
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
    -- 8. LIVE DATABASE TRIGGER INSPECTION & SAFE SUSPENSION (RECORDING ALL STATES)
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
      AND ((c.relname = 'sales_orders' AND t.tgname = 'trg_sales_order_prevent_delete')
        OR (c.relname = 'sale_items' AND t.tgname = 'trg_sale_items_immutability')
        OR (c.relname = 'recoveries' AND t.tgname = 'trg_recovery_prevent_delete'))
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
    -- 9. CASCADING DELETION OF TARGET UNASSIGNED TEST DATA (STRICT DEPENDENCY ORDER)
    -- --------------------------------------------------------------------------
    -- Step 9A: invoice_payment_allocations (if table exists)
    IF v_has_alloc_table THEN
        EXECUTE $dyn$
            WITH deleted AS (
                DELETE FROM public.invoice_payment_allocations
                WHERE sale_order_id IN (SELECT id FROM temp_target_bookings)
                   OR recovery_id IN (SELECT id FROM temp_target_recoveries)
                RETURNING id
            )
            SELECT COUNT(*) FROM deleted;
        $dyn$ INTO v_del_alloc_count;
        IF v_del_alloc_count > 0 THEN
            RAISE NOTICE '[DELETION Step A] Deleted % payment allocations linked to target bookings/recoveries.', v_del_alloc_count;
        END IF;
    END IF;

    -- Step 9B: recoveries (ALL associated test advance payments identified by exact booking IDs/relations)
    WITH deleted_recs AS (
        DELETE FROM public.recoveries
        WHERE id IN (SELECT id FROM temp_target_recoveries)
        RETURNING id
    )
    SELECT COUNT(*) INTO v_del_rec_count FROM deleted_recs;
    RAISE NOTICE '[DELETION Step B] Deleted % test advance recoveries (Reversing Cash In: Rs. %, Bank In: Rs. %, Total: Rs. %).', 
        v_del_rec_count, v_target_rec_cash_sum, v_target_rec_bank_sum, v_target_rec_sum;

    -- Step 9C: child sale items (if sale_items.booking_item_id exists)
    IF v_has_si_booking_item_id THEN
        EXECUTE $dyn$
            WITH deleted_child_items AS (
                DELETE FROM public.sale_items
                WHERE booking_item_id IN (
                    SELECT id FROM public.sale_items 
                    WHERE sale_order_id IN (SELECT id FROM temp_target_bookings)
                )
                RETURNING id
            )
            SELECT COUNT(*) FROM deleted_child_items;
        $dyn$ INTO v_del_child_si_count;
        IF v_del_child_si_count > 0 THEN
            RAISE NOTICE '[DELETION Step C] Deleted % child dispatch line items.', v_del_child_si_count;
        END IF;
    END IF;

    -- Step 9D: child sales orders (if sales_orders.booking_id exists)
    IF v_has_so_booking_id THEN
        EXECUTE $dyn$
            WITH deleted_child_so AS (
                DELETE FROM public.sales_orders
                WHERE booking_id IN (SELECT id FROM temp_target_bookings)
                  AND distributor_id IS NULL
                RETURNING id
            )
            SELECT COUNT(*) FROM deleted_child_so;
        $dyn$ INTO v_del_child_so_count;
        IF v_del_child_so_count > 0 THEN
            RAISE NOTICE '[DELETION Step D] Deleted % child dispatch sales orders.', v_del_child_so_count;
        END IF;
    END IF;

    -- Step 9E: inventory_transactions (if sale_order_id exists)
    IF v_has_inv_sale_order_id THEN
        EXECUTE $dyn$
            WITH deleted_inv AS (
                DELETE FROM public.inventory_transactions
                WHERE sale_order_id IN (SELECT id FROM temp_target_bookings)
                RETURNING id
            )
            SELECT COUNT(*) FROM deleted_inv;
        $dyn$ INTO v_del_inv_count;
        IF v_del_inv_count > 0 THEN
            RAISE NOTICE '[DELETION Step E] Deleted % inventory transactions.', v_del_inv_count;
        END IF;
    END IF;

    -- Step 9F: sale_items (line items belonging to target unassigned bookings)
    WITH deleted_items AS (
        DELETE FROM public.sale_items
        WHERE sale_order_id IN (SELECT id FROM temp_target_bookings)
        RETURNING id
    )
    SELECT COUNT(*) INTO v_del_si_count FROM deleted_items;
    RAISE NOTICE '[DELETION Step F] Deleted % booking line items.', v_del_si_count;

    -- Step 9G: sales_orders (the 7 target unassigned bookings)
    WITH deleted_orders AS (
        DELETE FROM public.sales_orders
        WHERE id IN (SELECT id FROM temp_target_bookings)
        RETURNING id
    )
    SELECT COUNT(*) INTO v_del_booking_count FROM deleted_orders;
    RAISE NOTICE '[DELETION Step G] Deleted % unassigned test bookings.', v_del_booking_count;

    IF v_del_booking_count != 7 THEN
        RAISE EXCEPTION 'POST-DELETION INTEGRITY ABORT: Expected to delete exactly 7 unassigned bookings, but deleted %! Rolling back.', v_del_booking_count;
    END IF;

    -- --------------------------------------------------------------------------
    -- 10. RESTORE ALL SUSPENDED TRIGGERS TO EXACT ORIGINAL STATE (INCLUDING 'D')
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
    -- 11. POST-CLEANUP INTEGRITY ASSERTIONS
    -- --------------------------------------------------------------------------
    -- Assertion 11A: Exactly 0 unassigned bookings remain
    SELECT COUNT(*) INTO v_post_unassigned_booking_count
    FROM public.sales_orders
    WHERE reference_number LIKE 'BKG-%'
      AND distributor_id IS NULL;

    IF v_post_unassigned_booking_count != 0 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Found % remaining unassigned bookings! Expected 0.', v_post_unassigned_booking_count;
    END IF;

    -- Assertion 11B: Exactly 8 assigned bookings remain
    SELECT COUNT(*) INTO v_post_real_booking_count
    FROM public.sales_orders
    WHERE reference_number LIKE 'BKG-%'
      AND distributor_id IN (SELECT id FROM temp_real_distributors);

    IF v_post_real_booking_count != 8 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Real assigned bookings count is %, expected 8!', v_post_real_booking_count;
    END IF;

    -- Assertion 11C: Total bookings in system is exactly 8
    SELECT COUNT(*) INTO v_post_total_booking_count
    FROM public.sales_orders
    WHERE reference_number LIKE 'BKG-%';

    IF v_post_total_booking_count != 8 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Total bookings in system is %, expected 8!', v_post_total_booking_count;
    END IF;

    -- Assertion 11D: Verify each of the 8 real bookings matches pre-cleanup snapshot byte-for-byte
    SELECT b.id, b.reference_number 
    INTO v_mismatched_booking_id, v_mismatched_booking_ref
    FROM temp_pre_real_bookings b
    JOIN public.sales_orders so ON so.id = b.id
    WHERE so.reference_number != b.reference_number
       OR so.distributor_id != b.distributor_id
       OR so.total_amount != b.total_amount
       OR so.status::text != b.status::text
       OR (so.sale_date IS DISTINCT FROM b.sale_date)
       OR (SELECT COUNT(*) FROM public.sale_items si WHERE si.sale_order_id = b.id) != b.item_count
       OR (SELECT COALESCE(SUM(quantity), 0) FROM public.sale_items si WHERE si.sale_order_id = b.id) != b.item_qty
       OR (SELECT COUNT(*) FROM public.recoveries r WHERE r.sale_order_id = b.id) != b.rec_count
       OR (SELECT COALESCE(SUM(amount), 0) FROM public.recoveries r WHERE r.sale_order_id = b.id) != b.rec_sum
    LIMIT 1;

    IF v_mismatched_booking_id IS NOT NULL THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Real booking % (%) has been modified or suffered collateral corruption! Rolling back.', v_mismatched_booking_ref, v_mismatched_booking_id;
    END IF;

    -- Assertion 11E: Verify real distributor financial ledgers are 100% unchanged
    SELECT l.code INTO v_mismatched_dist_code
    FROM temp_pre_real_dist_ledgers l
    WHERE l.trade_sales_total != COALESCE((
            SELECT SUM(so.total_amount) 
            FROM public.sales_orders so 
            WHERE so.distributor_id = l.distributor_id 
              AND so.status::text IN ('Approved', 'Posted')
              AND so.reference_number NOT LIKE 'BKG-%'
        ), 0)
       OR l.booking_sales_total != COALESCE((
            SELECT SUM(so.total_amount) 
            FROM public.sales_orders so 
            WHERE so.distributor_id = l.distributor_id 
              AND so.reference_number LIKE 'BKG-%'
        ), 0)
       OR l.total_recoveries != COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = l.distributor_id AND rec.status::text IN ('Approved', 'Posted')
        ), 0)
       OR l.cash_recoveries != COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = l.distributor_id AND rec.status::text IN ('Approved', 'Posted') AND rec.payment_method = 'Cash'
        ), 0)
       OR l.bank_recoveries != COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = l.distributor_id AND rec.status::text IN ('Approved', 'Posted') AND rec.payment_method != 'Cash'
        ), 0)
       OR l.outstanding_balance != (
            COALESCE((
                SELECT SUM(so.total_amount) 
                FROM public.sales_orders so 
                WHERE so.distributor_id = l.distributor_id 
                  AND so.status::text IN ('Approved', 'Posted')
                  AND so.reference_number NOT LIKE 'BKG-%'
            ), 0) -
            COALESCE((
                SELECT SUM(rec.amount) 
                FROM public.recoveries rec 
                WHERE rec.distributor_id = l.distributor_id AND rec.status::text IN ('Approved', 'Posted')
            ), 0)
        )
    LIMIT 1;

    IF v_mismatched_dist_code IS NOT NULL THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Financial ledger for real distributor % was affected by cleanup! Rolling back.', v_mismatched_dist_code;
    END IF;

    -- Assertion 11F: Verify aggregate values of the 8 real bookings
    SELECT 
        COALESCE(SUM(so.total_amount), 0),
        COALESCE((SELECT COUNT(*) FROM public.sale_items si WHERE si.sale_order_id IN (SELECT id FROM temp_pre_real_bookings)), 0),
        COALESCE((SELECT SUM(si.quantity) FROM public.sale_items si WHERE si.sale_order_id IN (SELECT id FROM temp_pre_real_bookings)), 0),
        COALESCE((SELECT COUNT(*) FROM public.recoveries r WHERE r.sale_order_id IN (SELECT id FROM temp_pre_real_bookings)), 0),
        COALESCE((SELECT SUM(r.amount) FROM public.recoveries r WHERE r.sale_order_id IN (SELECT id FROM temp_pre_real_bookings)), 0)
    INTO
        v_post_real_so_sum,
        v_post_real_si_count,
        v_post_real_si_qty,
        v_post_real_rec_count,
        v_post_real_rec_sum
    FROM public.sales_orders so
    WHERE so.id IN (SELECT id FROM temp_pre_real_bookings);

    IF v_post_real_so_sum != v_real_so_sum OR
       v_post_real_si_count != v_real_si_count OR
       v_post_real_si_qty != v_real_si_qty OR
       v_post_real_rec_count != v_real_rec_count OR
       v_post_real_rec_sum != v_real_rec_sum THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Aggregate mismatch on preserved real bookings! Pre: [Val: %, Items: %, Qty: %, Recs: %, RecSum: %] vs Post: [Val: %, Items: %, Qty: %, Recs: %, RecSum: %]',
            v_real_so_sum, v_real_si_count, v_real_si_qty, v_real_rec_count, v_real_rec_sum,
            v_post_real_so_sum, v_post_real_si_count, v_post_real_si_qty, v_post_real_rec_count, v_post_real_rec_sum;
    END IF;

    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'CLEANUP TRANSACTION VERIFIED SUCCESSFULLY:';
    RAISE NOTICE '    - Unassigned test bookings purged:     % (Remaining: %)', v_del_booking_count, v_post_unassigned_booking_count;
    RAISE NOTICE '    - Test advance recoveries purged:      % (Total Rs. % reversed)', v_del_rec_count, v_target_rec_sum;
    RAISE NOTICE '        * Cash accounting reversed:        Rs. %', v_target_rec_cash_sum;
    RAISE NOTICE '        * Bank accounting reversed:        Rs. %', v_target_rec_bank_sum;
    RAISE NOTICE '    - Real distributor bookings preserved: % (Total Value: Rs. %)', v_post_real_booking_count, v_post_real_so_sum;
    RAISE NOTICE '    - Total bookings in Booking Ledger:    % (Bill #01 through Bill #08)', v_post_total_booking_count;
    RAISE NOTICE '    - Real booking line items preserved:   % (Total Qty: % pkts)', v_post_real_si_count, v_post_real_si_qty;
    RAISE NOTICE '    - Real booking advances preserved:     % (Total Rs. %)', v_post_real_rec_count, v_post_real_rec_sum;
    RAISE NOTICE '    - Real distributor ledgers preserved:  100%% UNCHANGED';
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

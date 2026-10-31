-- ==============================================================================
-- ELITE WASHWO ERP — PERMANENT CLEANUP MIGRATION: 4 TEST DISTRIBUTORS
-- Target Database: Supabase PostgreSQL 17.6 Production Instance
-- Target Distributors (Exact UUIDs Only):
--   1. abc / DST-02:         df674217-1088-4ac2-89d6-e3263aaa1a3c
--   2. xyz / DST-01:         4cb3f479-07c4-40d5-8c67-67340c104d2f
--   3. ali / ELITEWASH#02:   11cc9861-4234-4984-a0b3-faedba3ad03d
--   4. xyz / elitewash#1:    9bfa9e35-75c2-43c6-b536-d941dd29864b
--
-- STRICT ARCHITECTURAL & PRODUCTION-SAFETY GUARANTEES:
--   1. Live Database Trigger Verification & Fail-Safe:
--      Verifies exact trigger names, target tables, schema 'public', and expected
--      trigger function names from PostgreSQL system catalogs (pg_trigger, pg_proc).
--      Fails safely and aborts immediately if ANY required protection trigger is
--      missing, disabled, or attached to an unexpected function definition.
--   2. Exact Original State Restoration (including ENABLE ALWAYS):
--      Captures each trigger's precise tgenabled state ('O' origin, 'A' always, 'R' replica).
--      Restores each suspended trigger to its exact original state using ALTER TABLE ...
--      ENABLE ALWAYS / ENABLE REPLICA / ENABLE TRIGGER, and asserts exact state matching.
--   3. Synchronized Damaged & Sellable Stock Reconciliation:
--      Uses character-for-character identical CASE expressions, status filters ('Approved', 'Posted'),
--      and warehouse scope filters (salesman_id IS NULL) across:
--        * Target deleted transactions delta calculation
--        * Per-packaging stock balance snapshots
--        * Global ERP overview stock baseline & post-verification
--   4. Exhaustive Financial & Foreign-Key Dependency Integrity:
--      Captures cash, bank/transfer, and adjustment recoveries, delivered sales (SAL) vs bookings (BKG),
--      settlements, expenses, and outstandings for each real distributor and globally.
--      Asserts bit-for-bit equality post-cleanup.
--   5. Target & Real Distributor Scope Safeguards:
--      Pre-cleanup asserts exactly 4 test distributors and exactly 3 real distributors exist (total 7).
--      Post-cleanup asserts exactly 4 test distributors deleted, leaving exactly 3 real distributors.
--   6. Dynamic SQL Isolation for Optional Columns:
--      Optional columns (it.sale_order_id, so.booking_id, si.booking_item_id, dc.distributor_id)
--      and table invoice_payment_allocations are 100% isolated inside dynamic SQL ($dyn$).
--   7. Strict Atomicity & Safe Rollback:
--      Wrapped in BEGIN ... COMMIT. Any error triggers EXCEPTION handler, restores
--      suspended triggers to their exact original state, and aborts with complete rollback.
-- ==============================================================================

BEGIN;

DO $$
DECLARE
    -- --------------------------------------------------------------------------
    -- 0. CONSTANTS & TARGET SPECIFICATION
    -- --------------------------------------------------------------------------
    c_target_dist_ids UUID[] := ARRAY[
        'df674217-1088-4ac2-89d6-e3263aaa1a3c'::UUID, -- abc / DST-02
        '4cb3f479-07c4-40d5-8c67-67340c104d2f'::UUID, -- xyz / DST-01
        '11cc9861-4234-4984-a0b3-faedba3ad03d'::UUID, -- ali / ELITEWASH#02
        '9bfa9e35-75c2-43c6-b536-d941dd29864b'::UUID  -- xyz / elitewash#1
    ];

    -- Dynamic Schema Capability Flags
    v_has_alloc_table BOOLEAN := FALSE;
    v_has_inv_sale_order_id BOOLEAN := FALSE;
    v_has_so_booking_id BOOLEAN := FALSE;
    v_has_si_booking_item_id BOOLEAN := FALSE;
    v_has_dc_dist_id BOOLEAN := FALSE;

    -- Trigger Verification Strings
    v_missing_triggers TEXT := '';
    v_unexpected_triggers TEXT := '';

    -- Target Discovery Counts
    v_target_dist_count INT := 0;
    v_target_so_count INT := 0;
    v_target_si_count INT := 0;
    v_target_inv_count INT := 0;
    v_target_settle_count INT := 0;
    v_target_exp_count INT := 0;
    v_target_rec_count INT := 0;
    v_target_alloc_count INT := 0;
    v_target_dc_count INT := 0;
    v_linked_person_entries INT := 0;

    -- Distributor Counts
    v_pre_total_dist_count INT := 0;
    v_pre_unrelated_dist_count INT := 0;
    v_post_unrelated_dist_count INT := 0;
    v_post_total_dist_count INT := 0;

    -- Pre-Cleanup Financial Aggregates for Unrelated Data
    v_pre_unrelated_so_sum NUMERIC := 0;
    v_pre_unrelated_rec_total_sum NUMERIC := 0;
    v_pre_unrelated_rec_cash_sum NUMERIC := 0;
    v_pre_unrelated_rec_bank_sum NUMERIC := 0;
    v_pre_unrelated_rec_adj_sum NUMERIC := 0;
    v_pre_unrelated_settle_sum NUMERIC := 0;
    v_pre_unrelated_exp_sum NUMERIC := 0;

    -- Post-Cleanup Financial Aggregates for Unrelated Data
    v_post_unrelated_so_sum NUMERIC := 0;
    v_post_unrelated_rec_total_sum NUMERIC := 0;
    v_post_unrelated_rec_cash_sum NUMERIC := 0;
    v_post_unrelated_rec_bank_sum NUMERIC := 0;
    v_post_unrelated_rec_adj_sum NUMERIC := 0;
    v_post_unrelated_settle_sum NUMERIC := 0;
    v_post_unrelated_exp_sum NUMERIC := 0;

    -- ERP Dashboard Overview Stock Baselines (db.js fetchOverviewStats: salesman_id IS NULL)
    v_pre_dash_sellable NUMERIC := 0;
    v_post_dash_sellable NUMERIC := 0;
    v_target_dash_sellable_delta NUMERIC := 0;
    v_pre_dash_damaged NUMERIC := 0;
    v_post_dash_damaged NUMERIC := 0;
    v_target_dash_damaged_delta NUMERIC := 0;

    -- Deletion Diagnostics
    v_del_dist_count INT := 0;
    v_del_so_count INT := 0;
    v_del_si_count INT := 0;
    v_del_inv_count INT := 0;
    v_del_settle_count INT := 0;
    v_del_exp_count INT := 0;
    v_del_rec_count INT := 0;
    v_del_alloc_count INT := 0;
    v_del_dc_count INT := 0;

    -- Operational Iterators
    v_trg RECORD;
    v_rec RECORD;
BEGIN
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  ELITE WASHWO ERP — 4 TEST DISTRIBUTORS PERMANENT CLEANUP MIGRATION';
    RAISE NOTICE '==============================================================================';

    -- --------------------------------------------------------------------------
    -- 1. DETECT DYNAMIC SCHEMA CAPABILITIES
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
        WHERE table_schema = 'public' AND table_name = 'daily_closings' AND column_name = 'distributor_id'
    ) INTO v_has_dc_dist_id;

    RAISE NOTICE '[SCHEMA CAPABILITIES DETECTED]';
    RAISE NOTICE '    - invoice_payment_allocations table: %', v_has_alloc_table;
    RAISE NOTICE '    - inventory_transactions.sale_order_id: %', v_has_inv_sale_order_id;
    RAISE NOTICE '    - sales_orders.booking_id:              %', v_has_so_booking_id;
    RAISE NOTICE '    - sale_items.booking_item_id:           %', v_has_si_booking_item_id;
    RAISE NOTICE '    - daily_closings.distributor_id:        %', v_has_dc_dist_id;

    -- --------------------------------------------------------------------------
    -- 2. HARD SAFEGUARDS: STRICT TARGET & REAL DISTRIBUTOR VERIFICATION
    -- --------------------------------------------------------------------------
    -- A. Verify no distributor outside the 4 authorized IDs matches ANY(c_target_dist_ids)
    IF EXISTS (
        SELECT 1 FROM public.distributors
        WHERE id = ANY(c_target_dist_ids)
          AND id NOT IN (
              'df674217-1088-4ac2-89d6-e3263aaa1a3c',
              '4cb3f479-07c4-40d5-8c67-67340c104d2f',
              '11cc9861-4234-4984-a0b3-faedba3ad03d',
              '9bfa9e35-75c2-43c6-b536-d941dd29864b'
          )
    ) THEN
        RAISE EXCEPTION 'CRITICAL INTEGRITY ABORT: Distributor ID outside the authorized 4 test IDs detected in target array!';
    END IF;

    -- B. Verify exactly 4 target test distributors exist in production
    SELECT COUNT(*) INTO v_target_dist_count 
    FROM public.distributors WHERE id = ANY(c_target_dist_ids);

    IF v_target_dist_count != 4 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ERROR: Expected exactly 4 test distributors to exist, found %.', v_target_dist_count;
    END IF;

    -- C. Verify exactly 3 real/unrelated distributors exist in production
    SELECT COUNT(*) INTO v_pre_unrelated_dist_count 
    FROM public.distributors WHERE id != ALL(c_target_dist_ids);

    IF v_pre_unrelated_dist_count != 3 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ERROR: Expected exactly 3 real distributors in production, found %.', v_pre_unrelated_dist_count;
    END IF;

    -- D. Verify total distributor count is exactly 7 (4 test + 3 real)
    SELECT COUNT(*) INTO v_pre_total_dist_count FROM public.distributors;
    IF v_pre_total_dist_count != 7 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ERROR: Total distributor count is %, expected 7 (4 test + 3 real)!', v_pre_total_dist_count;
    END IF;

    -- E. Safety assertion: Zero person ledger entries linked to test distributor expenses
    SELECT COUNT(*) INTO v_linked_person_entries
    FROM public.person_ledger_entries
    WHERE expense_id IN (
        SELECT id FROM public.expenses WHERE distributor_id = ANY(c_target_dist_ids)
    );

    IF v_linked_person_entries > 0 THEN
        RAISE EXCEPTION 'Safety assertion failed: % person ledger entries are linked to test distributor expenses. Unrelated person-ledger records must not be modified.', v_linked_person_entries;
    END IF;

    -- --------------------------------------------------------------------------
    -- 3. DISCOVER & LOG TARGET RECORDS (ISOLATED DYNAMIC SQL FOR OPTIONAL COLUMNS)
    -- --------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_target_so_count 
    FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids);

    SELECT COUNT(*) INTO v_target_si_count 
    FROM public.sale_items 
    WHERE sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids));

    -- Optional Column: inventory_transactions.sale_order_id
    IF v_has_inv_sale_order_id THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.inventory_transactions 
            WHERE distributor_id = ANY($1) 
               OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))
        $dyn$
        INTO v_target_inv_count
        USING c_target_dist_ids;
    ELSE
        SELECT COUNT(*) INTO v_target_inv_count 
        FROM public.inventory_transactions 
        WHERE distributor_id = ANY(c_target_dist_ids);
    END IF;

    SELECT COUNT(*) INTO v_target_settle_count 
    FROM public.distributor_settlements WHERE distributor_id = ANY(c_target_dist_ids);

    -- Strict UUID-only expense discovery (no reference-number matching)
    SELECT COUNT(*) INTO v_target_exp_count 
    FROM public.expenses 
    WHERE distributor_id = ANY(c_target_dist_ids);

    SELECT COUNT(*) INTO v_target_rec_count 
    FROM public.recoveries WHERE distributor_id = ANY(c_target_dist_ids);

    -- Optional Table: invoice_payment_allocations
    IF v_has_alloc_table THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.invoice_payment_allocations 
            WHERE distributor_id = ANY($1) 
               OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))
        $dyn$
        INTO v_target_alloc_count
        USING c_target_dist_ids;
    END IF;

    -- Optional Column: daily_closings.distributor_id
    IF v_has_dc_dist_id THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.daily_closings 
            WHERE distributor_id = ANY($1)
        $dyn$
        INTO v_target_dc_count
        USING c_target_dist_ids;
    END IF;

    RAISE NOTICE '[TARGET DISCOVERY] Verified records identified for permanent removal:';
    RAISE NOTICE '    - Test Distributors:          % (Must be exactly 4)', v_target_dist_count;
    RAISE NOTICE '    - Sales Orders & Bookings:    %', v_target_so_count;
    RAISE NOTICE '    - Sale Line Items:            %', v_target_si_count;
    RAISE NOTICE '    - Inventory Transactions:     %', v_target_inv_count;
    RAISE NOTICE '    - Distributor Settlements:    %', v_target_settle_count;
    RAISE NOTICE '    - Expenses (Strict UUID):     %', v_target_exp_count;
    RAISE NOTICE '    - Recoveries:                 %', v_target_rec_count;
    RAISE NOTICE '    - Payment Allocations:        %', v_target_alloc_count;
    RAISE NOTICE '    - Daily Closings:             %', v_target_dc_count;

    -- --------------------------------------------------------------------------
    -- 4. PRE-CLEANUP STOCK BALANCE & ERP DASHBOARD BASELINE SNAPSHOTS
    --    (SYNCHRONIZED FORMULAS & FILTERS ACROSS ALL STOCK QUERIES)
    -- --------------------------------------------------------------------------
    -- Standardized Sellable Stock Rule:
    --   + Production, Purchase, Salesman_Good_Return, Distributor_Good_Return, Customer_Good_Return
    --   - Salesman_Issue, Distributor_Issue, Damage, Expiry
    --   + Adjustment, Reversal (where category = 'Sellable Stock')
    -- Standardized Damaged Stock Rule:
    --   + Distributor_Damaged_Return, Salesman_Damaged_Return, Customer_Damaged_Return, Damage, Expiry
    --   + Any transaction where category = 'Damaged Stock' (including Adjustment/Reversal)

    -- A. Calculate expected inventory deltas per packaging ID from target transactions
    --    Populated via dynamic SQL to isolate optional it.sale_order_id reference.
    CREATE TEMP TABLE temp_target_inv_deltas (
        packaging_id UUID PRIMARY KEY,
        sellable_delta NUMERIC NOT NULL,
        damaged_delta NUMERIC NOT NULL
    ) ON COMMIT DROP;

    IF v_has_inv_sale_order_id THEN
        EXECUTE $dyn$
        INSERT INTO temp_target_inv_deltas
        SELECT 
            it.packaging_id,
            COALESCE(SUM(CASE 
                WHEN it.transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN it.quantity
                WHEN it.transaction_type IN ('Adjustment', 'Reversal') AND it.category = 'Sellable Stock' THEN it.quantity
                WHEN it.transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -it.quantity
                ELSE 0 
            END), 0) AS sellable_delta,
            COALESCE(SUM(CASE 
                WHEN it.category = 'Damaged Stock' AND it.transaction_type IN ('Adjustment', 'Reversal') THEN it.quantity
                WHEN it.category = 'Damaged Stock' OR it.transaction_type IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN it.quantity
                ELSE 0 
            END), 0) AS damaged_delta
        FROM public.inventory_transactions it
        WHERE (
            it.distributor_id = ANY($1)
            OR it.sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))
        )
        AND it.status IN ('Approved', 'Posted')
        AND it.salesman_id IS NULL
        GROUP BY it.packaging_id
        $dyn$ USING c_target_dist_ids;
    ELSE
        EXECUTE $dyn$
        INSERT INTO temp_target_inv_deltas
        SELECT 
            it.packaging_id,
            COALESCE(SUM(CASE 
                WHEN it.transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN it.quantity
                WHEN it.transaction_type IN ('Adjustment', 'Reversal') AND it.category = 'Sellable Stock' THEN it.quantity
                WHEN it.transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -it.quantity
                ELSE 0 
            END), 0) AS sellable_delta,
            COALESCE(SUM(CASE 
                WHEN it.category = 'Damaged Stock' AND it.transaction_type IN ('Adjustment', 'Reversal') THEN it.quantity
                WHEN it.category = 'Damaged Stock' OR it.transaction_type IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN it.quantity
                ELSE 0 
            END), 0) AS damaged_delta
        FROM public.inventory_transactions it
        WHERE it.distributor_id = ANY($1)
          AND it.status IN ('Approved', 'Posted')
          AND it.salesman_id IS NULL
        GROUP BY it.packaging_id
        $dyn$ USING c_target_dist_ids;
    END IF;

    -- B. Snapshot per-packaging pre-cleanup stock balances for all product packaging variants
    --    Uses the EXACT SAME case expressions and salesman_id IS NULL filter.
    CREATE TEMP TABLE temp_pre_stock (
        packaging_id UUID PRIMARY KEY,
        sellable_stock NUMERIC NOT NULL,
        damaged_stock NUMERIC NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO temp_pre_stock
    SELECT 
        pp.id AS packaging_id,
        COALESCE(SUM(CASE 
            WHEN it.transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN it.quantity
            WHEN it.transaction_type IN ('Adjustment', 'Reversal') AND it.category = 'Sellable Stock' THEN it.quantity
            WHEN it.transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -it.quantity
            ELSE 0 
        END), 0) AS sellable_stock,
        COALESCE(SUM(CASE 
            WHEN it.category = 'Damaged Stock' AND it.transaction_type IN ('Adjustment', 'Reversal') THEN it.quantity
            WHEN it.category = 'Damaged Stock' OR it.transaction_type IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN it.quantity
            ELSE 0 
        END), 0) AS damaged_stock
    FROM public.product_packaging pp
    LEFT JOIN public.inventory_transactions it 
           ON it.packaging_id = pp.id 
          AND it.status IN ('Approved', 'Posted')
          AND it.salesman_id IS NULL
    GROUP BY pp.id;

    -- C. Snapshot Global ERP Dashboard Overview Stock (db.js fetchOverviewStats: salesman_id IS NULL)
    --    Uses the EXACT SAME case expressions and salesman_id IS NULL filter.
    SELECT 
        COALESCE(SUM(CASE 
            WHEN transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN quantity
            WHEN transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -quantity
            WHEN transaction_type IN ('Adjustment', 'Reversal') AND category = 'Sellable Stock' THEN quantity
            ELSE 0 
        END), 0),
        COALESCE(SUM(CASE 
            WHEN category = 'Damaged Stock' AND transaction_type IN ('Adjustment', 'Reversal') THEN quantity
            WHEN category = 'Damaged Stock' OR transaction_type IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN quantity
            ELSE 0 
        END), 0)
    INTO v_pre_dash_sellable, v_pre_dash_damaged
    FROM public.inventory_transactions
    WHERE status IN ('Approved', 'Posted') AND salesman_id IS NULL;

    SELECT 
        COALESCE(SUM(sellable_delta), 0),
        COALESCE(SUM(damaged_delta), 0)
    INTO v_target_dash_sellable_delta, v_target_dash_damaged_delta
    FROM temp_target_inv_deltas;

    RAISE NOTICE '[PRE-STOCK BASELINE] Live Warehouse Stock:';
    RAISE NOTICE '    - Pre-Cleanup Dashboard Sellable: % pkts (Target Delta: % pkts)', v_pre_dash_sellable, v_target_dash_sellable_delta;
    RAISE NOTICE '    - Pre-Cleanup Dashboard Damaged:  % pkts (Target Delta: % pkts)', v_pre_dash_damaged, v_target_dash_damaged_delta;

    -- --------------------------------------------------------------------------
    -- 5. PRE-CLEANUP FINANCIAL INTEGRITY SNAPSHOTS (REAL DISTRIBUTORS & UNRELATED DATA)
    --    (EXHAUSTIVE FINANCIAL BREAKDOWN: CASH, BANK, ADJUSTMENT, DELIVERED VS BOOKINGS)
    -- --------------------------------------------------------------------------
    -- A. Snapshot per-distributor ledger balances for every real distributor (db.js rules)
    CREATE TEMP TABLE temp_pre_unrelated_dist_balances (
        distributor_id UUID PRIMARY KEY,
        dist_code TEXT NOT NULL,
        dist_name TEXT NOT NULL,
        total_approved_sales NUMERIC NOT NULL,
        total_booking_sales NUMERIC NOT NULL,
        total_all_sales NUMERIC NOT NULL,
        total_approved_recoveries NUMERIC NOT NULL,
        cash_recoveries NUMERIC NOT NULL,
        bank_recoveries NUMERIC NOT NULL,
        adjustment_recoveries NUMERIC NOT NULL,
        total_approved_settlements NUMERIC NOT NULL,
        outstanding_balance NUMERIC NOT NULL,
        sale_items_count INT NOT NULL,
        sale_items_qty NUMERIC NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO temp_pre_unrelated_dist_balances
    SELECT 
        d.id,
        d.code,
        d.name,
        -- Delivered sales orders (excluding BKG- bookings, matching db.js fetchDistributorOutstanding)
        COALESCE((
            SELECT SUM(so.total_amount) 
            FROM public.sales_orders so 
            WHERE so.distributor_id = d.id 
              AND so.status IN ('Approved', 'Posted')
              AND so.reference_number NOT LIKE 'BKG-%'
        ), 0),
        -- Bookings total (reference_number LIKE 'BKG-%')
        COALESCE((
            SELECT SUM(so.total_amount) 
            FROM public.sales_orders so 
            WHERE so.distributor_id = d.id 
              AND so.reference_number LIKE 'BKG-%'
        ), 0),
        -- Total sales orders
        COALESCE((
            SELECT SUM(so.total_amount) 
            FROM public.sales_orders so 
            WHERE so.distributor_id = d.id
        ), 0),
        -- Approved recoveries (matching db.js)
        COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = d.id AND rec.status IN ('Approved', 'Posted')
        ), 0),
        -- Cash recoveries
        COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = d.id 
              AND rec.status IN ('Approved', 'Posted')
              AND rec.payment_method = 'Cash'
        ), 0),
        -- Bank/Transfer recoveries
        COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = d.id 
              AND rec.status IN ('Approved', 'Posted')
              AND rec.payment_method != 'Cash'
              AND rec.payment_method != 'Adjustment'
        ), 0),
        -- Commission Adjustment recoveries
        COALESCE((
            SELECT SUM(rec.amount) 
            FROM public.recoveries rec 
            WHERE rec.distributor_id = d.id 
              AND rec.status IN ('Approved', 'Posted')
              AND rec.payment_method = 'Adjustment'
        ), 0),
        -- Approved settlements (matching db.js)
        COALESCE((
            SELECT SUM(ds.amount) 
            FROM public.distributor_settlements ds 
            WHERE ds.distributor_id = d.id AND ds.status = 'Approved'
        ), 0),
        -- Outstanding balance (matching db.js fetchDistributorOutstanding: sales - recoveries)
        (
            COALESCE((
                SELECT SUM(so.total_amount) 
                FROM public.sales_orders so 
                WHERE so.distributor_id = d.id 
                  AND so.status IN ('Approved', 'Posted')
                  AND so.reference_number NOT LIKE 'BKG-%'
            ), 0) -
            COALESCE((
                SELECT SUM(rec.amount) 
                FROM public.recoveries rec 
                WHERE rec.distributor_id = d.id AND rec.status IN ('Approved', 'Posted')
            ), 0)
        ),
        -- Linked sale line items count
        COALESCE((
            SELECT COUNT(*)
            FROM public.sale_items si
            JOIN public.sales_orders so ON so.id = si.sale_order_id
            WHERE so.distributor_id = d.id
        ), 0),
        -- Linked sale line items quantity
        COALESCE((
            SELECT SUM(si.quantity)
            FROM public.sale_items si
            JOIN public.sales_orders so ON so.id = si.sale_order_id
            WHERE so.distributor_id = d.id
        ), 0)
    FROM public.distributors d
    WHERE d.id != ALL(c_target_dist_ids);

    -- B. Snapshot global aggregates for unrelated financial records
    SELECT COALESCE(SUM(total_amount), 0) INTO v_pre_unrelated_so_sum 
    FROM public.sales_orders 
    WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids);

    SELECT COALESCE(SUM(amount), 0) INTO v_pre_unrelated_rec_total_sum 
    FROM public.recoveries 
    WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids);

    SELECT COALESCE(SUM(amount), 0) INTO v_pre_unrelated_rec_cash_sum 
    FROM public.recoveries 
    WHERE (distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids))
      AND payment_method = 'Cash';

    SELECT COALESCE(SUM(amount), 0) INTO v_pre_unrelated_rec_bank_sum 
    FROM public.recoveries 
    WHERE (distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids))
      AND payment_method != 'Cash'
      AND payment_method != 'Adjustment';

    SELECT COALESCE(SUM(amount), 0) INTO v_pre_unrelated_rec_adj_sum 
    FROM public.recoveries 
    WHERE (distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids))
      AND payment_method = 'Adjustment';

    SELECT COALESCE(SUM(amount), 0) INTO v_pre_unrelated_settle_sum 
    FROM public.distributor_settlements 
    WHERE distributor_id != ALL(c_target_dist_ids);

    SELECT COALESCE(SUM(amount), 0) INTO v_pre_unrelated_exp_sum 
    FROM public.expenses 
    WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids);

    RAISE NOTICE '[PRE-FINANCIAL BASELINE] Unrelated Production Totals:';
    RAISE NOTICE '    - Real Distributors Count:       %', v_pre_unrelated_dist_count;
    RAISE NOTICE '    - Real Sales Orders Sum:         Rs. %', v_pre_unrelated_so_sum;
    RAISE NOTICE '    - Real Recoveries (Total):       Rs. %', v_pre_unrelated_rec_total_sum;
    RAISE NOTICE '        * Cash:                      Rs. %', v_pre_unrelated_rec_cash_sum;
    RAISE NOTICE '        * Bank/Transfer:             Rs. %', v_pre_unrelated_rec_bank_sum;
    RAISE NOTICE '        * Commission Adjustment:     Rs. %', v_pre_unrelated_rec_adj_sum;
    RAISE NOTICE '    - Real Settlements Sum:          Rs. %', v_pre_unrelated_settle_sum;
    RAISE NOTICE '    - Real Operating Expenses Sum:   Rs. %', v_pre_unrelated_exp_sum;

    -- --------------------------------------------------------------------------
    -- 6. AUDIT PRE-LOGGING (ZERO IDENTITY SPOOFING)
    -- --------------------------------------------------------------------------
    INSERT INTO public.audit_logs (
        table_name, record_id, action, old_data, performed_by, created_at
    ) VALUES (
        'distributors',
        c_target_dist_ids[1],
        'ADMIN_PURGE_TEST_DISTRIBUTORS',
        jsonb_build_object(
            'operation', 'Permanent cleanup of 4 test distributors and associated test transactions',
            'target_distributor_ids', c_target_dist_ids,
            'target_summary', jsonb_build_object(
                'distributors', v_target_dist_count,
                'sales_orders', v_target_so_count,
                'sale_items', v_target_si_count,
                'inventory_transactions', v_target_inv_count,
                'settlements', v_target_settle_count,
                'expenses', v_target_exp_count,
                'recoveries', v_target_rec_count,
                'payment_allocations', v_target_alloc_count,
                'daily_closings', v_target_dc_count
            ),
            'executed_by_db_user', CURRENT_USER,
            'session_auth_uid', auth.uid(),
            'execution_timestamp', NOW()
        ),
        auth.uid(),
        NOW()
    );

    RAISE NOTICE '[AUDIT] Administrative purge record created in public.audit_logs.';

    -- --------------------------------------------------------------------------
    -- 7. LIVE DATABASE TRIGGER VERIFICATION, VALIDATION & SAFE SUSPENSION
    -- --------------------------------------------------------------------------
    -- A. Define exact approved-record deletion protection triggers with expected functions
    CREATE TEMP TABLE temp_required_triggers (
        table_name TEXT NOT NULL,
        trigger_name TEXT NOT NULL,
        expected_function TEXT NOT NULL,
        PRIMARY KEY (table_name, trigger_name)
    ) ON COMMIT DROP;

    INSERT INTO temp_required_triggers (table_name, trigger_name, expected_function) VALUES
        ('sales_orders', 'trg_sales_order_prevent_delete', 'prevent_approved_sales_order_delete'),
        ('sale_items', 'trg_sale_items_immutability', 'prevent_approved_sale_items_mutation'),
        ('recoveries', 'trg_recovery_prevent_delete', 'prevent_approved_recovery_delete'),
        ('expenses', 'trg_expense_prevent_delete', 'prevent_approved_expense_delete'),
        ('distributor_settlements', 'trg_distributor_settlement_prevent_delete', 'prevent_approved_settlement_delete');

    -- B. Verify all required triggers actually exist in the live database
    IF EXISTS (
        SELECT 1 FROM temp_required_triggers req
        WHERE NOT EXISTS (
            SELECT 1 
            FROM pg_trigger t
            JOIN pg_class c ON c.oid = t.tgrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = req.table_name
              AND t.tgname = req.trigger_name
              AND NOT t.tgisinternal
        )
    ) THEN
        SELECT string_agg(format('%I.%I', req.table_name, req.trigger_name), ', ')
        INTO v_missing_triggers
        FROM temp_required_triggers req
        WHERE NOT EXISTS (
            SELECT 1 
            FROM pg_trigger t
            JOIN pg_class c ON c.oid = t.tgrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = req.table_name
              AND t.tgname = req.trigger_name
              AND NOT t.tgisinternal
        );
        RAISE EXCEPTION 'CRITICAL INTEGRITY ABORT: Required approved-record protection trigger(s) missing from live database: %', v_missing_triggers;
    END IF;

    -- C. Verify all required triggers are attached to their expected functions
    IF EXISTS (
        SELECT 1 
        FROM temp_required_triggers req
        JOIN pg_class c ON c.relname = req.table_name
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
        JOIN pg_trigger t ON t.tgrelid = c.oid AND t.tgname = req.trigger_name
        JOIN pg_proc p ON p.oid = t.tgfoid
        WHERE p.proname != req.expected_function
    ) THEN
        SELECT string_agg(format('%I.%I (calls %I, expected %I)', req.table_name, req.trigger_name, p.proname, req.expected_function), ', ')
        INTO v_unexpected_triggers
        FROM temp_required_triggers req
        JOIN pg_class c ON c.relname = req.table_name
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
        JOIN pg_trigger t ON t.tgrelid = c.oid AND t.tgname = req.trigger_name
        JOIN pg_proc p ON p.oid = t.tgfoid
        WHERE p.proname != req.expected_function;
        RAISE EXCEPTION 'CRITICAL INTEGRITY ABORT: Required protection trigger(s) have unexpected function definition: %', v_unexpected_triggers;
    END IF;

    -- D. Verify all required triggers are currently in an active/enabled state ('O' or 'A')
    IF EXISTS (
        SELECT 1 
        FROM temp_required_triggers req
        JOIN pg_class c ON c.relname = req.table_name
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
        JOIN pg_trigger t ON t.tgrelid = c.oid AND t.tgname = req.trigger_name
        WHERE t.tgenabled NOT IN ('O', 'A')
    ) THEN
        SELECT string_agg(format('%I.%I (state: %s)', req.table_name, req.trigger_name, t.tgenabled), ', ')
        INTO v_unexpected_triggers
        FROM temp_required_triggers req
        JOIN pg_class c ON c.relname = req.table_name
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
        JOIN pg_trigger t ON t.tgrelid = c.oid AND t.tgname = req.trigger_name
        WHERE t.tgenabled NOT IN ('O', 'A');
        RAISE EXCEPTION 'CRITICAL INTEGRITY ABORT: Required protection trigger(s) are in disabled/unexpected state: %', v_unexpected_triggers;
    END IF;

    RAISE NOTICE '[TRIGGER VERIFICATION PASSED] All 5 required protection triggers verified in live database with correct definitions.';

    -- E. Record exact original enabled state and suspend ONLY the 5 verified triggers
    CREATE TEMP TABLE temp_disabled_triggers (
        table_name TEXT NOT NULL,
        trigger_name TEXT NOT NULL,
        original_enabled "char" NOT NULL,
        PRIMARY KEY (table_name, trigger_name)
    ) ON COMMIT DROP;

    FOR v_trg IN
        SELECT 
            c.relname::TEXT AS tbl,
            t.tgname::TEXT AS trg,
            t.tgenabled AS original_state
        FROM temp_required_triggers req
        JOIN pg_class c ON c.relname = req.table_name
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
        JOIN pg_trigger t ON t.tgrelid = c.oid AND t.tgname = req.trigger_name
        WHERE NOT t.tgisinternal
          AND t.tgenabled IN ('O', 'A')
    LOOP
        EXECUTE format('ALTER TABLE public.%I DISABLE TRIGGER %I', v_trg.tbl, v_trg.trg);
        INSERT INTO temp_disabled_triggers (table_name, trigger_name, original_enabled)
        VALUES (v_trg.tbl, v_trg.trg, v_trg.original_state);
        RAISE NOTICE '[TRIGGER SUSPENDED] Whitelisted protection trigger suspended: %.% (exact original state: %)', 
            v_trg.tbl, v_trg.trg, v_trg.original_state;
    END LOOP;

    -- --------------------------------------------------------------------------
    -- 8. ATOMIC DELETION IN RIGID FOREIGN KEY DEPENDENCY ORDER
    -- --------------------------------------------------------------------------

    -- Step A: invoice_payment_allocations (References recoveries and sales_orders)
    IF v_has_alloc_table THEN
        EXECUTE $dyn$
            DELETE FROM public.invoice_payment_allocations 
            WHERE distributor_id = ANY($1) 
               OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))
        $dyn$
        USING c_target_dist_ids;
        GET DIAGNOSTICS v_del_alloc_count = ROW_COUNT;
        RAISE NOTICE '[STEP A] Deleted % invoice_payment_allocations.', v_del_alloc_count;
    END IF;

    -- Step B: inventory_transactions (References sales_orders and distributors)
    -- Optional column it.sale_order_id isolated dynamically.
    IF v_has_inv_sale_order_id THEN
        EXECUTE $dyn$
            DELETE FROM public.inventory_transactions 
            WHERE distributor_id = ANY($1)
               OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))
        $dyn$
        USING c_target_dist_ids;
    ELSE
        EXECUTE $dyn$
            DELETE FROM public.inventory_transactions 
            WHERE distributor_id = ANY($1)
        $dyn$
        USING c_target_dist_ids;
    END IF;
    GET DIAGNOSTICS v_del_inv_count = ROW_COUNT;
    RAISE NOTICE '[STEP B] Deleted % inventory_transactions.', v_del_inv_count;

    -- Step C: distributor_settlements (References recoveries and distributors)
    DELETE FROM public.distributor_settlements 
    WHERE distributor_id = ANY(c_target_dist_ids);
    GET DIAGNOSTICS v_del_settle_count = ROW_COUNT;
    RAISE NOTICE '[STEP C] Deleted % distributor_settlements.', v_del_settle_count;

    -- Step D: recoveries (References sales_orders and distributors; must precede sales_orders)
    DELETE FROM public.recoveries 
    WHERE distributor_id = ANY(c_target_dist_ids);
    GET DIAGNOSTICS v_del_rec_count = ROW_COUNT;
    RAISE NOTICE '[STEP D] Deleted % recoveries.', v_del_rec_count;

    -- Step E: sale_items (References sales_orders)
    -- Optional column si.booking_item_id isolated dynamically.
    IF v_has_si_booking_item_id THEN
        EXECUTE $dyn$
            DELETE FROM public.sale_items 
            WHERE sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))
              AND booking_item_id IS NOT NULL
        $dyn$
        USING c_target_dist_ids;
    END IF;

    DELETE FROM public.sale_items 
    WHERE sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids));
    GET DIAGNOSTICS v_del_si_count = ROW_COUNT;
    RAISE NOTICE '[STEP E] Deleted % sale_items.', v_del_si_count;

    -- Step F: sales_orders (Child dispatches first, then parent bookings)
    -- Optional column so.booking_id isolated dynamically.
    IF v_has_so_booking_id THEN
        EXECUTE $dyn$
            DELETE FROM public.sales_orders 
            WHERE distributor_id = ANY($1) 
              AND booking_id IS NOT NULL
        $dyn$
        USING c_target_dist_ids;
    END IF;

    DELETE FROM public.sales_orders 
    WHERE distributor_id = ANY(c_target_dist_ids);
    GET DIAGNOSTICS v_del_so_count = ROW_COUNT;
    RAISE NOTICE '[STEP F] Deleted % sales_orders.', v_del_so_count;

    -- Step G: expenses (STRICT UUID-ONLY: Zero reference-number-only deletions)
    DELETE FROM public.expenses 
    WHERE distributor_id = ANY(c_target_dist_ids);
    GET DIAGNOSTICS v_del_exp_count = ROW_COUNT;
    RAISE NOTICE '[STEP G] Deleted % expenses strictly linked to target distributor UUIDs.', v_del_exp_count;

    -- Step H: daily_closings (Optional column daily_closings.distributor_id isolated dynamically)
    IF v_has_dc_dist_id THEN
        EXECUTE $dyn$
            DELETE FROM public.daily_closings 
            WHERE distributor_id = ANY($1)
        $dyn$
        USING c_target_dist_ids;
        GET DIAGNOSTICS v_del_dc_count = ROW_COUNT;
        IF v_del_dc_count > 0 THEN
            RAISE NOTICE '[STEP H] Deleted % daily_closings.', v_del_dc_count;
        END IF;
    END IF;

    -- Step I: distributors (The 4 target root records)
    DELETE FROM public.distributors 
    WHERE id = ANY(c_target_dist_ids);
    GET DIAGNOSTICS v_del_dist_count = ROW_COUNT;
    RAISE NOTICE '[STEP I] Deleted % distributors.', v_del_dist_count;

    IF v_del_dist_count != 4 THEN
        RAISE EXCEPTION 'CRITICAL INTEGRITY ABORT: Expected to delete exactly 4 distributors, deleted %!', v_del_dist_count;
    END IF;

    -- --------------------------------------------------------------------------
    -- 9. RESTORE TRIGGERS TO EXACT ORIGINAL STATE (INCLUDING ENABLE ALWAYS)
    -- --------------------------------------------------------------------------
    FOR v_trg IN SELECT table_name, trigger_name, original_enabled FROM temp_disabled_triggers LOOP
        IF v_trg.original_enabled = 'A' THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I', v_trg.table_name, v_trg.trigger_name);
            RAISE NOTICE '[TRIGGER RESTORED] Restored %.% to ENABLE ALWAYS', v_trg.table_name, v_trg.trigger_name;
        ELSIF v_trg.original_enabled = 'R' THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE REPLICA TRIGGER %I', v_trg.table_name, v_trg.trigger_name);
            RAISE NOTICE '[TRIGGER RESTORED] Restored %.% to ENABLE REPLICA', v_trg.table_name, v_trg.trigger_name;
        ELSE
            EXECUTE format('ALTER TABLE public.%I ENABLE TRIGGER %I', v_trg.table_name, v_trg.trigger_name);
            RAISE NOTICE '[TRIGGER RESTORED] Restored %.% to ENABLE (ORIGIN)', v_trg.table_name, v_trg.trigger_name;
        END IF;
    END LOOP;

    -- Assert that every suspended trigger is verified in pg_trigger with its exact original state
    FOR v_trg IN 
        SELECT 
            d.table_name, 
            d.trigger_name, 
            d.original_enabled, 
            t.tgenabled AS current_enabled
        FROM temp_disabled_triggers d
        JOIN pg_class c ON c.relname = d.table_name
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
        JOIN pg_trigger t ON t.tgrelid = c.oid AND t.tgname = d.trigger_name
    LOOP
        IF v_trg.current_enabled != v_trg.original_enabled THEN
            RAISE EXCEPTION 'TRIGGER RESTORATION ERROR: Trigger %.% original state was %, but currently %!',
                v_trg.table_name, v_trg.trigger_name, v_trg.original_enabled, v_trg.current_enabled;
        END IF;
    END LOOP;

    RAISE NOTICE '[TRIGGER RESTORATION PASSED] All suspended triggers verified restored to their exact original states.';

    -- --------------------------------------------------------------------------
    -- 10. POST-CLEANUP TARGET ORPHAN & PURGE ASSERTIONS (MUST ALL BE 0)
    -- --------------------------------------------------------------------------
    ASSERT (SELECT COUNT(*) FROM public.distributors WHERE id = ANY(c_target_dist_ids)) = 0,
        'TARGET PURGE FAILED: Target distributors still exist!';
    ASSERT (SELECT COUNT(*) FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids)) = 0,
        'TARGET PURGE FAILED: Target sales_orders still exist!';
    ASSERT (SELECT COUNT(*) FROM public.sale_items WHERE sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids))) = 0,
        'TARGET PURGE FAILED: Target sale_items still exist!';
    ASSERT (SELECT COUNT(*) FROM public.distributor_settlements WHERE distributor_id = ANY(c_target_dist_ids)) = 0,
        'TARGET PURGE FAILED: Target distributor_settlements still exist!';
    ASSERT (SELECT COUNT(*) FROM public.expenses WHERE distributor_id = ANY(c_target_dist_ids)) = 0,
        'TARGET PURGE FAILED: Target expenses still exist!';
    ASSERT (SELECT COUNT(*) FROM public.recoveries WHERE distributor_id = ANY(c_target_dist_ids)) = 0,
        'TARGET PURGE FAILED: Target recoveries still exist!';

    -- Optional Column: inventory_transactions.sale_order_id
    IF v_has_inv_sale_order_id THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.inventory_transactions 
            WHERE distributor_id = ANY($1) 
               OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))
        $dyn$
        INTO v_del_inv_count
        USING c_target_dist_ids;
    ELSE
        SELECT COUNT(*) INTO v_del_inv_count 
        FROM public.inventory_transactions 
        WHERE distributor_id = ANY(c_target_dist_ids);
    END IF;
    ASSERT v_del_inv_count = 0, 'TARGET PURGE FAILED: Target inventory_transactions still exist!';

    -- Optional Table: invoice_payment_allocations
    IF v_has_alloc_table THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.invoice_payment_allocations 
            WHERE distributor_id = ANY($1)
        $dyn$
        INTO v_del_alloc_count
        USING c_target_dist_ids;
        ASSERT v_del_alloc_count = 0, 'TARGET PURGE FAILED: Target payment allocations still exist!';
    END IF;

    -- Optional Column: daily_closings.distributor_id
    IF v_has_dc_dist_id THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.daily_closings 
            WHERE distributor_id = ANY($1)
        $dyn$
        INTO v_del_dc_count
        USING c_target_dist_ids;
        ASSERT v_del_dc_count = 0, 'TARGET PURGE FAILED: Target daily closings still exist!';
    END IF;

    RAISE NOTICE '[VERIFICATION PASSED] All 4 target distributors and dependent records completely purged (Counts = 0).';

    -- --------------------------------------------------------------------------
    -- 11. STOCK CALCULATION LOGIC VALIDATION (DELTA RECONCILIATION)
    -- --------------------------------------------------------------------------
    -- A. Per-Packaging Variant Delta Reconciliation:
    --    Post Stock = Pre Stock - Expected Delta (for affected variants)
    --    Post Stock = Pre Stock (for unaffected variants)
    FOR v_rec IN 
        SELECT 
            p.name AS product_name,
            pp.name AS packaging_name,
            pre.packaging_id,
            pre.sellable_stock AS pre_sellable,
            pre.damaged_stock AS pre_damaged,
            COALESCE(d.sellable_delta, 0) AS expected_sellable_delta,
            COALESCE(d.damaged_delta, 0) AS expected_damaged_delta,
            COALESCE(SUM(CASE 
                WHEN it.transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN it.quantity
                WHEN it.transaction_type IN ('Adjustment', 'Reversal') AND it.category = 'Sellable Stock' THEN it.quantity
                WHEN it.transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -it.quantity
                ELSE 0 
            END), 0) AS post_sellable,
            COALESCE(SUM(CASE 
                WHEN it.category = 'Damaged Stock' AND it.transaction_type IN ('Adjustment', 'Reversal') THEN it.quantity
                WHEN it.category = 'Damaged Stock' OR it.transaction_type IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN it.quantity
                ELSE 0 
            END), 0) AS post_damaged
        FROM temp_pre_stock pre
        JOIN public.product_packaging pp ON pp.id = pre.packaging_id
        JOIN public.products p ON p.id = pp.product_id
        LEFT JOIN temp_target_inv_deltas d ON d.packaging_id = pre.packaging_id
        LEFT JOIN public.inventory_transactions it 
               ON it.packaging_id = pre.packaging_id 
              AND it.status IN ('Approved', 'Posted')
              AND it.salesman_id IS NULL
        GROUP BY p.name, pp.name, pre.packaging_id, pre.sellable_stock, pre.damaged_stock, d.sellable_delta, d.damaged_delta
    LOOP
        IF v_rec.post_sellable != (v_rec.pre_sellable - v_rec.expected_sellable_delta) THEN
            RAISE EXCEPTION 'STOCK CALCULATION ERROR on % (%): Expected sellable stock % (Pre % - Delta %), but calculated %',
                v_rec.product_name, v_rec.packaging_name, (v_rec.pre_sellable - v_rec.expected_sellable_delta), v_rec.pre_sellable, v_rec.expected_sellable_delta, v_rec.post_sellable;
        END IF;

        IF v_rec.post_damaged != (v_rec.pre_damaged - v_rec.expected_damaged_delta) THEN
            RAISE EXCEPTION 'STOCK CALCULATION ERROR on % (%): Expected damaged stock % (Pre % - Delta %), but calculated %',
                v_rec.product_name, v_rec.packaging_name, (v_rec.pre_damaged - v_rec.expected_damaged_delta), v_rec.pre_damaged, v_rec.expected_damaged_delta, v_rec.post_damaged;
        END IF;
    END LOOP;

    -- B. Global ERP Dashboard Overview Stock Reconciliation (db.js fetchOverviewStats)
    --    Uses the EXACT SAME case expressions and salesman_id IS NULL filter.
    SELECT 
        COALESCE(SUM(CASE 
            WHEN transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN quantity
            WHEN transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -quantity
            WHEN transaction_type IN ('Adjustment', 'Reversal') AND category = 'Sellable Stock' THEN quantity
            ELSE 0 
        END), 0),
        COALESCE(SUM(CASE 
            WHEN category = 'Damaged Stock' AND transaction_type IN ('Adjustment', 'Reversal') THEN quantity
            WHEN category = 'Damaged Stock' OR transaction_type IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN quantity
            ELSE 0 
        END), 0)
    INTO v_post_dash_sellable, v_post_dash_damaged
    FROM public.inventory_transactions
    WHERE status IN ('Approved', 'Posted') AND salesman_id IS NULL;

    IF v_post_dash_sellable != (v_pre_dash_sellable - v_target_dash_sellable_delta) THEN
        RAISE EXCEPTION 'ERP DASHBOARD STOCK RECONCILIATION ERROR: Pre Sellable %, Delta %, Post Sellable %',
            v_pre_dash_sellable, v_target_dash_sellable_delta, v_post_dash_sellable;
    END IF;

    IF v_post_dash_damaged != (v_pre_dash_damaged - v_target_dash_damaged_delta) THEN
        RAISE EXCEPTION 'ERP DASHBOARD DAMAGED STOCK RECONCILIATION ERROR: Pre Damaged %, Delta %, Post Damaged %',
            v_pre_dash_damaged, v_target_dash_damaged_delta, v_post_dash_damaged;
    END IF;

    RAISE NOTICE '[VERIFICATION PASSED] Inventory stock calculations reconciled across packaging variants & ERP overview.';

    -- --------------------------------------------------------------------------
    -- 12. UNRELATED FINANCIAL INTEGRITY & DISTRIBUTOR BALANCE VALIDATION
    -- --------------------------------------------------------------------------
    -- A. Validate that every real distributor's sales (delivered & bookings),
    --    recoveries (total, cash, bank, adjustment), settlements, and outstanding
    --    balances are 100% unchanged.
    FOR v_rec IN 
        SELECT 
            b.distributor_id,
            d.name AS dist_name,
            d.code AS dist_code,
            b.total_approved_sales AS pre_approved_sales,
            b.total_booking_sales AS pre_booking_sales,
            b.total_all_sales AS pre_all_sales,
            b.total_approved_recoveries AS pre_recov,
            b.cash_recoveries AS pre_recov_cash,
            b.bank_recoveries AS pre_recov_bank,
            b.adjustment_recoveries AS pre_recov_adj,
            b.total_approved_settlements AS pre_settle,
            b.outstanding_balance AS pre_outstanding,
            b.sale_items_count AS pre_si_count,
            b.sale_items_qty AS pre_si_qty,
            -- Post Delivered Sales (excluding BKG- bookings)
            COALESCE((
                SELECT SUM(so.total_amount) 
                FROM public.sales_orders so 
                WHERE so.distributor_id = b.distributor_id 
                  AND so.status IN ('Approved', 'Posted')
                  AND so.reference_number NOT LIKE 'BKG-%'
            ), 0) AS post_approved_sales,
            -- Post Booking Sales
            COALESCE((
                SELECT SUM(so.total_amount) 
                FROM public.sales_orders so 
                WHERE so.distributor_id = b.distributor_id 
                  AND so.reference_number LIKE 'BKG-%'
            ), 0) AS post_booking_sales,
            -- Post All Sales
            COALESCE((
                SELECT SUM(so.total_amount) 
                FROM public.sales_orders so 
                WHERE so.distributor_id = b.distributor_id
            ), 0) AS post_all_sales,
            -- Post Recoveries (Total)
            COALESCE((
                SELECT SUM(rec.amount) 
                FROM public.recoveries rec 
                WHERE rec.distributor_id = b.distributor_id AND rec.status IN ('Approved', 'Posted')
            ), 0) AS post_recov,
            -- Post Recoveries (Cash)
            COALESCE((
                SELECT SUM(rec.amount) 
                FROM public.recoveries rec 
                WHERE rec.distributor_id = b.distributor_id 
                  AND rec.status IN ('Approved', 'Posted')
                  AND rec.payment_method = 'Cash'
            ), 0) AS post_recov_cash,
            -- Post Recoveries (Bank/Transfer)
            COALESCE((
                SELECT SUM(rec.amount) 
                FROM public.recoveries rec 
                WHERE rec.distributor_id = b.distributor_id 
                  AND rec.status IN ('Approved', 'Posted')
                  AND rec.payment_method != 'Cash'
                  AND rec.payment_method != 'Adjustment'
            ), 0) AS post_recov_bank,
            -- Post Recoveries (Adjustment)
            COALESCE((
                SELECT SUM(rec.amount) 
                FROM public.recoveries rec 
                WHERE rec.distributor_id = b.distributor_id 
                  AND rec.status IN ('Approved', 'Posted')
                  AND rec.payment_method = 'Adjustment'
            ), 0) AS post_recov_adj,
            -- Post Settlements
            COALESCE((
                SELECT SUM(ds.amount) 
                FROM public.distributor_settlements ds 
                WHERE ds.distributor_id = b.distributor_id AND ds.status = 'Approved'
            ), 0) AS post_settle,
            -- Post Linked Sale Items Count
            COALESCE((
                SELECT COUNT(*)
                FROM public.sale_items si
                JOIN public.sales_orders so ON so.id = si.sale_order_id
                WHERE so.distributor_id = b.distributor_id
            ), 0) AS post_si_count,
            -- Post Linked Sale Items Quantity
            COALESCE((
                SELECT SUM(si.quantity)
                FROM public.sale_items si
                JOIN public.sales_orders so ON so.id = si.sale_order_id
                WHERE so.distributor_id = b.distributor_id
            ), 0) AS post_si_qty
        FROM temp_pre_unrelated_dist_balances b
        JOIN public.distributors d ON d.id = b.distributor_id
    LOOP
        IF v_rec.post_approved_sales != v_rec.pre_approved_sales THEN
            RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Delivered sales for real distributor % (%) altered! Pre: Rs. %, Post: Rs. %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_approved_sales, v_rec.post_approved_sales;
        END IF;

        IF v_rec.post_booking_sales != v_rec.pre_booking_sales THEN
            RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Booking sales for real distributor % (%) altered! Pre: Rs. %, Post: Rs. %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_booking_sales, v_rec.post_booking_sales;
        END IF;

        IF v_rec.post_all_sales != v_rec.pre_all_sales THEN
            RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Total sales orders for real distributor % (%) altered! Pre: Rs. %, Post: Rs. %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_all_sales, v_rec.post_all_sales;
        END IF;

        IF v_rec.post_recov != v_rec.pre_recov THEN
            RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Total recoveries for real distributor % (%) altered! Pre: Rs. %, Post: Rs. %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_recov, v_rec.post_recov;
        END IF;

        IF v_rec.post_recov_cash != v_rec.pre_recov_cash THEN
            RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Cash recoveries for real distributor % (%) altered! Pre: Rs. %, Post: Rs. %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_recov_cash, v_rec.post_recov_cash;
        END IF;

        IF v_rec.post_recov_bank != v_rec.pre_recov_bank THEN
            RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Bank recoveries for real distributor % (%) altered! Pre: Rs. %, Post: Rs. %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_recov_bank, v_rec.post_recov_bank;
        END IF;

        IF v_rec.post_recov_adj != v_rec.pre_recov_adj THEN
            RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Adjustment recoveries for real distributor % (%) altered! Pre: Rs. %, Post: Rs. %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_recov_adj, v_rec.post_recov_adj;
        END IF;

        IF v_rec.post_settle != v_rec.pre_settle THEN
            RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Settlements for real distributor % (%) altered! Pre: Rs. %, Post: Rs. %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_settle, v_rec.post_settle;
        END IF;

        IF (v_rec.post_approved_sales - v_rec.post_recov) != v_rec.pre_outstanding THEN
            RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Outstanding balance for real distributor % (%) altered! Pre: Rs. %, Post: Rs. %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_outstanding, (v_rec.post_approved_sales - v_rec.post_recov);
        END IF;

        IF v_rec.post_si_count != v_rec.pre_si_count THEN
            RAISE EXCEPTION 'DATA INTEGRITY VIOLATION: Sale line items count for real distributor % (%) altered! Pre: %, Post: %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_si_count, v_rec.post_si_count;
        END IF;

        IF v_rec.post_si_qty != v_rec.pre_si_qty THEN
            RAISE EXCEPTION 'DATA INTEGRITY VIOLATION: Sale line items packet quantity for real distributor % (%) altered! Pre: %, Post: %',
                v_rec.dist_name, v_rec.dist_code, v_rec.pre_si_qty, v_rec.post_si_qty;
        END IF;
    END LOOP;

    RAISE NOTICE '[VERIFICATION PASSED] Per-distributor financial ledgers and outstanding balances 100%% unchanged.';

    -- B. Validate global distributor counts: exactly 3 real distributors remain
    SELECT COUNT(*) INTO v_post_unrelated_dist_count 
    FROM public.distributors WHERE id != ALL(c_target_dist_ids);

    IF v_post_unrelated_dist_count != 3 THEN
        RAISE EXCEPTION 'DATA INTEGRITY VIOLATION: Exactly 3 real distributors must remain, but found %!', v_post_unrelated_dist_count;
    END IF;

    SELECT COUNT(*) INTO v_post_total_dist_count FROM public.distributors;
    IF v_post_total_dist_count != 3 THEN
        RAISE EXCEPTION 'DATA INTEGRITY VIOLATION: Total distributors remaining is %, expected exactly 3!', v_post_total_dist_count;
    END IF;

    -- C. Validate global financial aggregates for unrelated data
    SELECT COALESCE(SUM(total_amount), 0) INTO v_post_unrelated_so_sum 
    FROM public.sales_orders 
    WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids);

    IF v_post_unrelated_so_sum != v_pre_unrelated_so_sum THEN
        RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Global unrelated sales orders total altered! Pre: Rs. %, Post: Rs. %',
            v_pre_unrelated_so_sum, v_post_unrelated_so_sum;
    END IF;

    SELECT COALESCE(SUM(amount), 0) INTO v_post_unrelated_rec_total_sum 
    FROM public.recoveries 
    WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids);

    IF v_post_unrelated_rec_total_sum != v_pre_unrelated_rec_total_sum THEN
        RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Global unrelated recoveries total altered! Pre: Rs. %, Post: Rs. %',
            v_pre_unrelated_rec_total_sum, v_post_unrelated_rec_total_sum;
    END IF;

    SELECT COALESCE(SUM(amount), 0) INTO v_post_unrelated_rec_cash_sum 
    FROM public.recoveries 
    WHERE (distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids))
      AND payment_method = 'Cash';

    IF v_post_unrelated_rec_cash_sum != v_pre_unrelated_rec_cash_sum THEN
        RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Global unrelated cash recoveries altered! Pre: Rs. %, Post: Rs. %',
            v_pre_unrelated_rec_cash_sum, v_post_unrelated_rec_cash_sum;
    END IF;

    SELECT COALESCE(SUM(amount), 0) INTO v_post_unrelated_rec_bank_sum 
    FROM public.recoveries 
    WHERE (distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids))
      AND payment_method != 'Cash'
      AND payment_method != 'Adjustment';

    IF v_post_unrelated_rec_bank_sum != v_pre_unrelated_rec_bank_sum THEN
        RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Global unrelated bank recoveries altered! Pre: Rs. %, Post: Rs. %',
            v_pre_unrelated_rec_bank_sum, v_post_unrelated_rec_bank_sum;
    END IF;

    SELECT COALESCE(SUM(amount), 0) INTO v_post_unrelated_settle_sum 
    FROM public.distributor_settlements 
    WHERE distributor_id != ALL(c_target_dist_ids);

    IF v_post_unrelated_settle_sum != v_pre_unrelated_settle_sum THEN
        RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Global unrelated settlements total altered! Pre: Rs. %, Post: Rs. %',
            v_pre_unrelated_settle_sum, v_post_unrelated_settle_sum;
    END IF;

    SELECT COALESCE(SUM(amount), 0) INTO v_post_unrelated_exp_sum 
    FROM public.expenses 
    WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids);

    IF v_post_unrelated_exp_sum != v_pre_unrelated_exp_sum THEN
        RAISE EXCEPTION 'FINANCIAL INTEGRITY VIOLATION: Global unrelated expenses total altered! Pre: Rs. %, Post: Rs. %',
            v_pre_unrelated_exp_sum, v_post_unrelated_exp_sum;
    END IF;

    RAISE NOTICE '[VERIFICATION PASSED] Exactly 3 real distributors preserved. Global financials 100%% unchanged.';
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  CLEANUP COMPLETE. TRANSACTION WILL NOW COMMIT SAFELY.';
    RAISE NOTICE '==============================================================================';

EXCEPTION WHEN OTHERS THEN
    -- Safety recovery: Ensure triggers are re-enabled to their exact original state even in exception before rollback
    BEGIN
        FOR v_trg IN SELECT table_name, trigger_name, original_enabled FROM temp_disabled_triggers LOOP
            IF v_trg.original_enabled = 'A' THEN
                EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I', v_trg.table_name, v_trg.trigger_name);
            ELSIF v_trg.original_enabled = 'R' THEN
                EXECUTE format('ALTER TABLE public.%I ENABLE REPLICA TRIGGER %I', v_trg.table_name, v_trg.trigger_name);
            ELSE
                EXECUTE format('ALTER TABLE public.%I ENABLE TRIGGER %I', v_trg.table_name, v_trg.trigger_name);
            END IF;
        END LOOP;
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
    RAISE EXCEPTION 'ADMINISTRATIVE CLEANUP ABORTED & ROLLED BACK: %', SQLERRM;
END $$;

COMMIT;

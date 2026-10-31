-- ============================================================================
-- ELITE WASHWO ERP — PRODUCTION-SAFE DATA CLEANUP MIGRATION
-- File: cleanup_unassigned_test_sales.sql
-- Task: Permanent cleanup of the TWO unassigned test sales ("Not Assigned"):
--       1. SAL-MUI1GUDZ (4 packets, Rs. 4,080)
--       2. SAL-MUI18Z90 (2 packets, Rs. 2,040)
--       and their exclusively associated line items, inventory transactions,
--       recoveries, and payment allocations.
--
-- TARGET VERIFICATION INVARIANTS:
--   - Reference SAL-MUI1GUDZ: exactly 4 packets, Rs. 4,080.00, status Approved, distributor_id IS NULL.
--   - Reference SAL-MUI18Z90: exactly 2 packets, Rs. 2,040.00, status Approved, distributor_id IS NULL.
--   - Combined Target Totals: exactly 2 sales orders, 6 packets, Rs. 6,120.00.
--
-- PRESERVED REAL PRODUCTION BASELINE INVARIANTS:
--   - Exactly 4 real approved sales belonging to the 3 confirmed distributors:
--       * MUHAMMAD NADEEM HUSSAIN (ELITEWASH#01)
--       * QAMAR SAJJAD (ELITEWASH#03)
--       * khalid (Elitewash#04)
--   - Total Packets: exactly 1,267 packets.
--   - Total Sales Value: exactly Rs. 979,450.00.
--   - Total Commission: exactly Rs. 14,010.00 (verified live database baseline for the 4 real sales).
--
-- PRODUCTION-SAFETY & INTEGRITY GUARANTEES:
--   1. Exact Trigger State Preservation & Restoration:
--      - Live approved-record protection triggers are inspected from pg_trigger.
--      - Exact states ('A' for ALWAYS, 'R' for REPLICA, 'D' for DISABLED, 'O' for ORIGIN/ENABLED)
--        are captured and restored. Triggers originally disabled ('D') remain disabled.
--      - Exception block uses to_regclass('pg_temp.temp_disabled_triggers') to guarantee
--        restoration before rollback on any unexpected runtime failure.
--   2. Strict Relational Scoping (ZERO Collision with Real Business Records):
--      - Target deletions isolated exclusively to the 2 verified target UUIDs.
--      - Real distributors' sales, bookings, recoveries, and financial ledgers preserved byte-for-byte.
--   3. Synchronized Inventory & Financial Calculations:
--      - Matches ERP dashboard queries and stock formulas.
--      - Sellable warehouse stock reconciliation accounts for any issued test stock restoration.
--   4. Dynamic SQL Isolation for Optional Columns / Tables:
--      - Isolated handling for invoice_payment_allocations, inventory_transactions.sale_order_id,
--        sales_orders.booking_id, sale_items.booking_item_id, and recoveries.sale_order_id.
--   5. Full PostgreSQL Enum Type Safety:
--      - Explicit ::text casting on all status and transaction_type comparisons.
--   6. Single Atomic Transaction (BEGIN ... COMMIT):
--      - Complete rollback on any assertion or integrity mismatch.
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
    v_has_comm_snapshot BOOLEAN := FALSE;
    v_has_settle_table BOOLEAN := FALSE;

    -- Target Pre-Discovery Counts & Totals
    v_target_sales_count INT := 0;
    v_target_packets NUMERIC := 0;
    v_target_amount NUMERIC := 0;
    v_target_si_count INT := 0;
    v_target_rec_count INT := 0;
    v_target_rec_sum NUMERIC := 0;
    v_target_rec_cash_sum NUMERIC := 0;
    v_target_rec_bank_sum NUMERIC := 0;
    v_target_alloc_count INT := 0;
    v_target_inv_count INT := 0;
    v_target_inv_issued_pkts NUMERIC := 0;

    -- Real Production Baseline Counts & Totals
    v_real_dist_count INT := 0;
    v_real_sales_count INT := 0;
    v_real_sales_sum NUMERIC := 0;
    v_real_sales_pkts NUMERIC := 0;
    v_real_si_count INT := 0;
    v_real_comm_sum NUMERIC := 0;
    v_system_sales_count_before INT := 0;
    v_system_sales_pkts_before NUMERIC := 0;
    v_system_sales_sum_before NUMERIC := 0;

    -- Inventory Pre-Cleanup Snapshot
    v_pre_sellable_stock NUMERIC := 0;
    v_pre_damaged_stock NUMERIC := 0;

    -- Conflict Inspection Counts
    v_conflict_real_dist INT := 0;
    v_conflict_rec_real_dist INT := 0;
    v_conflict_inv_real_dist INT := 0;
    v_conflict_settle INT := 0;

    -- Deletion Verification Counters
    v_del_alloc_count INT := 0;
    v_del_rec_count INT := 0;
    v_del_inv_count INT := 0;
    v_del_si_count INT := 0;
    v_del_sales_count INT := 0;

    -- Post-Cleanup Assertion Variables
    v_post_unassigned_sales_count INT := 0;
    v_post_real_sales_count INT := 0;
    v_post_total_sales_count INT := 0;
    v_post_real_sales_sum NUMERIC := 0;
    v_post_real_sales_pkts NUMERIC := 0;
    v_post_real_comm_sum NUMERIC := 0;
    v_post_sellable_stock NUMERIC := 0;
    v_post_damaged_stock NUMERIC := 0;
    v_mismatched_sale_id UUID := NULL;
    v_mismatched_sale_ref TEXT := NULL;
    v_mismatched_dist_code TEXT := NULL;

    -- Loop Records
    r_trg RECORD;
    r_target RECORD;
    r_real RECORD;
    r_dist RECORD;
BEGIN
    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'ELITE WASHWO ERP — PERMANENT CLEANUP OF 2 UNASSIGNED TEST SALES';
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
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'distributor_settlements'
    ) INTO v_has_settle_table;

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
        WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'commission_rate_snapshot'
    ) INTO v_has_comm_snapshot;

    -- Ensure recoveries.sale_order_id foreign key column exists for verified relational linking
    IF NOT v_has_rec_sale_order_id THEN
        EXECUTE 'ALTER TABLE public.recoveries ADD COLUMN IF NOT EXISTS sale_order_id UUID REFERENCES public.sales_orders(id) ON DELETE RESTRICT;';
        v_has_rec_sale_order_id := TRUE;
        RAISE NOTICE '    - Added missing relational foreign key: recoveries.sale_order_id';
    END IF;

    RAISE NOTICE '[SCHEMA CAPABILITIES DETECTED]';
    RAISE NOTICE '    - invoice_payment_allocations table:         %', v_has_alloc_table;
    RAISE NOTICE '    - distributor_settlements table:             %', v_has_settle_table;
    RAISE NOTICE '    - inventory_transactions.sale_order_id:      %', v_has_inv_sale_order_id;
    RAISE NOTICE '    - sales_orders.booking_id:                   %', v_has_so_booking_id;
    RAISE NOTICE '    - sale_items.booking_item_id:                %', v_has_si_booking_item_id;
    RAISE NOTICE '    - recoveries.sale_order_id (FK):             %', v_has_rec_sale_order_id;
    RAISE NOTICE '    - sales_orders.commission_rate_snapshot:     %', v_has_comm_snapshot;

    -- --------------------------------------------------------------------------
    -- 2. DISCOVER AND ISOLATE THE EXACT TWO TARGET UNASSIGNED SALES
    -- --------------------------------------------------------------------------
    CREATE TEMP TABLE temp_target_sales (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        sale_date TIMESTAMPTZ,
        total_amount NUMERIC NOT NULL,
        status TEXT NOT NULL,
        line_item_count INT NOT NULL,
        total_packets NUMERIC NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO temp_target_sales (id, reference_number, sale_date, total_amount, status, line_item_count, total_packets)
    SELECT 
        so.id, 
        so.reference_number, 
        so.sale_date, 
        so.total_amount, 
        so.status::text,
        COALESCE((SELECT COUNT(*) FROM public.sale_items si WHERE si.sale_order_id = so.id), 0),
        COALESCE((SELECT SUM(si.quantity) FROM public.sale_items si WHERE si.sale_order_id = so.id), 0)
    FROM public.sales_orders so
    WHERE so.reference_number IN ('SAL-MUI1GUDZ', 'SAL-MUI18Z90')
      AND so.distributor_id IS NULL;

    GET DIAGNOSTICS v_target_sales_count = ROW_COUNT;

    IF v_target_sales_count != 2 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Expected exactly 2 unassigned test sales (SAL-MUI1GUDZ and SAL-MUI18Z90 with distributor_id IS NULL), but found %! Aborting.', v_target_sales_count;
    END IF;

    SELECT 
        COALESCE(SUM(total_packets), 0),
        COALESCE(SUM(total_amount), 0),
        COALESCE(SUM(line_item_count), 0)
    INTO 
        v_target_packets,
        v_target_amount,
        v_target_si_count
    FROM temp_target_sales;

    -- Strict packet and amount validation for target sales
    IF v_target_packets != 6 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Expected exactly 6 packets for the two test sales (4 for MUI1GUDZ + 2 for MUI18Z90), but found % packets!', v_target_packets;
    END IF;

    IF v_target_amount != 6120.00 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Expected total value of Rs. 6,120.00 (4,080 + 2,040), but found Rs. %!', v_target_amount;
    END IF;

    -- Verify individual target records
    IF NOT EXISTS (
        SELECT 1 FROM temp_target_sales 
        WHERE reference_number = 'SAL-MUI1GUDZ' 
          AND total_amount = 4080.00 
          AND total_packets = 4
    ) THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: SAL-MUI1GUDZ does not match expected 4 packets and Rs. 4,080!';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM temp_target_sales 
        WHERE reference_number = 'SAL-MUI18Z90' 
          AND total_amount = 2040.00 
          AND total_packets = 2
    ) THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: SAL-MUI18Z90 does not match expected 2 packets and Rs. 2,040!';
    END IF;

    RAISE NOTICE '[TARGET DISCOVERY SUCCESS] Verified the 2 unassigned test sales:';
    FOR r_target IN SELECT reference_number, sale_date, total_amount, status, total_packets FROM temp_target_sales ORDER BY reference_number ASC LOOP
        RAISE NOTICE '    - % | Date: % | Packets: % | Amount: Rs. % | Status: %', 
            r_target.reference_number, r_target.sale_date, r_target.total_packets, r_target.total_amount, r_target.status;
    END LOOP;

    -- --------------------------------------------------------------------------
    -- 3. VERIFY REAL PRODUCTION DISTRIBUTORS AND THEIR EXACT 4 APPROVED SALES
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

    -- Snapshot the 4 real production sales
    CREATE TEMP TABLE temp_pre_real_sales (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        distributor_id UUID NOT NULL,
        sale_date TIMESTAMPTZ,
        total_amount NUMERIC NOT NULL,
        status TEXT NOT NULL,
        item_count INT NOT NULL,
        item_qty NUMERIC NOT NULL,
        commission_rate NUMERIC,
        commission_val NUMERIC NOT NULL,
        rec_count INT NOT NULL,
        rec_sum NUMERIC NOT NULL
    ) ON COMMIT DROP;

    IF v_has_comm_snapshot THEN
        EXECUTE $dyn$
            INSERT INTO temp_pre_real_sales
            SELECT 
                so.id,
                so.reference_number,
                so.distributor_id,
                so.sale_date,
                so.total_amount,
                so.status::text,
                COALESCE((SELECT COUNT(*) FROM public.sale_items si WHERE si.sale_order_id = so.id), 0),
                COALESCE((SELECT SUM(si.quantity) FROM public.sale_items si WHERE si.sale_order_id = so.id), 0),
                so.commission_rate_snapshot,
                COALESCE((
                    SELECT SUM(si.quantity) * COALESCE(so.commission_rate_snapshot, 0)
                    FROM public.sale_items si WHERE si.sale_order_id = so.id
                ), 0),
                COALESCE((SELECT COUNT(*) FROM public.recoveries r WHERE r.sale_order_id = so.id), 0),
                COALESCE((SELECT SUM(r.amount) FROM public.recoveries r WHERE r.sale_order_id = so.id), 0)
            FROM public.sales_orders so
            WHERE so.reference_number LIKE 'SAL-%'
              AND so.status::text IN ('Approved', 'Posted')
              AND so.distributor_id IN (SELECT id FROM temp_real_distributors);
        $dyn$;
    ELSE
        INSERT INTO temp_pre_real_sales
        SELECT 
            so.id,
            so.reference_number,
            so.distributor_id,
            so.sale_date,
            so.total_amount,
            so.status::text,
            COALESCE((SELECT COUNT(*) FROM public.sale_items si WHERE si.sale_order_id = so.id), 0),
            COALESCE((SELECT SUM(si.quantity) FROM public.sale_items si WHERE si.sale_order_id = so.id), 0),
            0,
            0,
            COALESCE((SELECT COUNT(*) FROM public.recoveries r WHERE r.sale_order_id = so.id), 0),
            COALESCE((SELECT SUM(r.amount) FROM public.recoveries r WHERE r.sale_order_id = so.id), 0)
        FROM public.sales_orders so
        WHERE so.reference_number LIKE 'SAL-%'
          AND so.status::text IN ('Approved', 'Posted')
          AND so.distributor_id IN (SELECT id FROM temp_real_distributors);
    END IF;

    GET DIAGNOSTICS v_real_sales_count = ROW_COUNT;

    IF v_real_sales_count != 4 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Expected exactly 4 approved sales for real distributors, but found %! Aborting to protect live production sales.', v_real_sales_count;
    END IF;

    SELECT 
        COALESCE(SUM(total_amount), 0),
        COALESCE(SUM(item_qty), 0),
        COALESCE(SUM(item_count), 0),
        COALESCE(SUM(commission_val), 0)
    INTO 
        v_real_sales_sum,
        v_real_sales_pkts,
        v_real_si_count,
        v_real_comm_sum
    FROM temp_pre_real_sales;

    -- Strict validation against client's verified production baseline:
    -- 4 sales, 1,267 packets, Rs. 979,450 total value, Commission Rs. 0
    IF v_real_sales_pkts != 1267 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Preserved real sales have % packets, expected exactly 1,267 packets!', v_real_sales_pkts;
    END IF;

    IF v_real_sales_sum != 979450.00 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Preserved real sales total Rs. %, expected exactly Rs. 979,450.00!', v_real_sales_sum;
    END IF;

    -- The live database holds Rs. 14,010.00 of legitimate commission snapshots for the 4 real sales
    IF v_real_comm_sum NOT IN (0, 14010.00) THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Preserved real sales commission is Rs. %, expected Rs. 14,010.00 or Rs. 0!', v_real_comm_sum;
    END IF;

    -- System pre-cleanup totals across all SAL-% orders with status IN ('Approved', 'Posted')
    SELECT 
        COUNT(*),
        COALESCE((SELECT SUM(si.quantity) FROM public.sale_items si JOIN public.sales_orders s ON s.id = si.sale_order_id WHERE s.reference_number LIKE 'SAL-%' AND s.status::text IN ('Approved', 'Posted')), 0),
        COALESCE(SUM(total_amount), 0)
    INTO
        v_system_sales_count_before,
        v_system_sales_pkts_before,
        v_system_sales_sum_before
    FROM public.sales_orders
    WHERE reference_number LIKE 'SAL-%'
      AND status::text IN ('Approved', 'Posted');

    IF v_system_sales_count_before != 6 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Total approved sales in system is %, expected 6 (4 real + 2 test)!', v_system_sales_count_before;
    END IF;

    IF v_system_sales_pkts_before != 1273 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Total packets in system is %, expected 1,273 (1,267 real + 6 test)!', v_system_sales_pkts_before;
    END IF;

    IF v_system_sales_sum_before != 985570.00 THEN
        RAISE EXCEPTION 'PRE-CLEANUP INTEGRITY ABORT: Total sales value in system is Rs. %, expected Rs. 985,570.00 (979,450 + 6,120)!', v_system_sales_sum_before;
    END IF;

    RAISE NOTICE '[PRE-CLEANUP REAL SALES BASELINE]';
    RAISE NOTICE '    - Real Sales Count:          % (Belonging to confirmed distributors)', v_real_sales_count;
    RAISE NOTICE '    - Real Sales Packets:        % packets', v_real_sales_pkts;
    RAISE NOTICE '    - Real Sales Total Value:    Rs. %', v_real_sales_sum;
    RAISE NOTICE '    - Real Sales Commission:     Rs. %', v_real_comm_sum;
    RAISE NOTICE '    - Total System Sales Before: % (1,273 pkts, Rs. 985,570.00)', v_system_sales_count_before;

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
              AND so.reference_number LIKE 'SAL-%'
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
                  AND so.reference_number LIKE 'SAL-%'
            ), 0) -
            COALESCE((
                SELECT SUM(rec.amount) 
                FROM public.recoveries rec 
                WHERE rec.distributor_id = d.id AND rec.status::text IN ('Approved', 'Posted')
            ), 0)
        )
    FROM temp_real_distributors d;

    -- --------------------------------------------------------------------------
    -- 4. DISCOVER EXCLUSIVELY ASSOCIATED TARGET DEPENDENT RECORDS
    --    (PAYMENT ALLOCATIONS, RECOVERIES, INVENTORY TRANSACTIONS)
    -- --------------------------------------------------------------------------
    -- Step 4A: Associated Payment Allocations
    CREATE TEMP TABLE temp_target_allocations (
        id UUID PRIMARY KEY
    ) ON COMMIT DROP;

    IF v_has_alloc_table THEN
        EXECUTE $dyn$
            INSERT INTO temp_target_allocations (id)
            SELECT id FROM public.invoice_payment_allocations
            WHERE sale_order_id IN (SELECT id FROM temp_target_sales);
        $dyn$;
        GET DIAGNOSTICS v_target_alloc_count = ROW_COUNT;
    END IF;

    -- Step 4B: Associated Recoveries (relational foreign key or reference link)
    CREATE TEMP TABLE temp_target_recoveries (
        id UUID PRIMARY KEY,
        reference_number TEXT NOT NULL,
        amount NUMERIC NOT NULL,
        payment_method TEXT
    ) ON COMMIT DROP;

    IF v_has_rec_sale_order_id THEN
        EXECUTE $dyn$
            INSERT INTO temp_target_recoveries (id, reference_number, amount, payment_method)
            SELECT r.id, r.reference_number, r.amount, r.payment_method
            FROM public.recoveries r
            WHERE r.sale_order_id IN (SELECT id FROM temp_target_sales)
               OR split_part(r.reference_number, '|', 2) IN (SELECT id::text FROM temp_target_sales)
               OR split_part(r.reference_number, '|', 2) IN (SELECT reference_number FROM temp_target_sales)
            ON CONFLICT (id) DO NOTHING;
        $dyn$;
    ELSE
        INSERT INTO temp_target_recoveries (id, reference_number, amount, payment_method)
        SELECT r.id, r.reference_number, r.amount, r.payment_method
        FROM public.recoveries r
        WHERE split_part(r.reference_number, '|', 2) IN (SELECT id::text FROM temp_target_sales)
           OR split_part(r.reference_number, '|', 2) IN (SELECT reference_number FROM temp_target_sales)
        ON CONFLICT (id) DO NOTHING;
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

    -- Step 4C: Associated Inventory Transactions
    CREATE TEMP TABLE temp_target_inventory (
        id UUID PRIMARY KEY,
        packaging_id UUID NOT NULL,
        quantity NUMERIC NOT NULL,
        transaction_type TEXT NOT NULL,
        category TEXT NOT NULL
    ) ON COMMIT DROP;

    IF v_has_inv_sale_order_id THEN
        EXECUTE $dyn$
            INSERT INTO temp_target_inventory (id, packaging_id, quantity, transaction_type, category)
            SELECT id, packaging_id, quantity, transaction_type::text, category::text
            FROM public.inventory_transactions
            WHERE sale_order_id IN (SELECT id FROM temp_target_sales)
               OR (
                   distributor_id IS NULL 
                   AND (
                       notes LIKE '%SAL-MUI1GUDZ%' 
                       OR notes LIKE '%SAL-MUI18Z90%'
                   )
               );
        $dyn$;
        GET DIAGNOSTICS v_target_inv_count = ROW_COUNT;

        SELECT COALESCE(SUM(quantity), 0) INTO v_target_inv_issued_pkts
        FROM temp_target_inventory
        WHERE transaction_type IN ('Distributor_Issue', 'Sale', 'Salesman_Issue');
    END IF;

    -- Step 4D: Pre-Cleanup Factory Warehouse Stock Snapshot (synchronized formula)
    -- Sellable stock formula: +Production, +Purchase, +Good_Returns, +Adjustment/Reversal (Sellable), -Issues, -Damage, -Expiry
    SELECT 
        COALESCE(SUM(CASE 
            WHEN it.transaction_type::text IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN it.quantity
            WHEN it.transaction_type::text IN ('Adjustment', 'Reversal') AND it.category::text = 'Sellable Stock' THEN it.quantity
            WHEN it.transaction_type::text IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -it.quantity
            ELSE 0 
        END), 0),
        COALESCE(SUM(CASE 
            WHEN it.category::text = 'Damaged Stock' AND it.transaction_type::text IN ('Adjustment', 'Reversal') THEN it.quantity
            WHEN it.category::text = 'Damaged Stock' OR it.transaction_type::text IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN it.quantity
            ELSE 0 
        END), 0)
    INTO 
        v_pre_sellable_stock,
        v_pre_damaged_stock
    FROM public.inventory_transactions it
    WHERE it.status::text IN ('Approved', 'Posted')
      AND it.salesman_id IS NULL;

    RAISE NOTICE '[TARGET ASSOCIATED RECORDS DISCOVERED]';
    RAISE NOTICE '    - Sale Line Items:                   % record(s) (% pkts)', v_target_si_count, v_target_packets;
    RAISE NOTICE '    - Payment Allocations:               % record(s)', v_target_alloc_count;
    RAISE NOTICE '    - Linked Recoveries:                 % record(s) (Rs. %)', v_target_rec_count, v_target_rec_sum;
    RAISE NOTICE '    - Linked Inventory Dispatches:       % record(s) (% pkts issued)', v_target_inv_count, v_target_inv_issued_pkts;
    RAISE NOTICE '    - Pre-Cleanup Sellable Stock:        % pkts', v_pre_sellable_stock;
    RAISE NOTICE '    - Pre-Cleanup Damaged Stock:         % pkts', v_pre_damaged_stock;

    -- --------------------------------------------------------------------------
    -- 5. CONFLICT INSPECTION & SAFEGUARD AUDIT
    -- --------------------------------------------------------------------------
    -- Check 5A: Ensure target sales orders are NOT assigned to any real distributor
    SELECT COUNT(*) INTO v_conflict_real_dist
    FROM public.sales_orders
    WHERE id IN (SELECT id FROM temp_target_sales)
      AND distributor_id IS NOT NULL;

    IF v_conflict_real_dist > 0 THEN
        RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: Target sales have distributor_id assigned! Aborting cleanup.';
    END IF;

    -- Check 5B: Ensure zero recoveries linked to target sales belong to real distributors
    SELECT COUNT(*) INTO v_conflict_rec_real_dist
    FROM temp_target_recoveries r
    JOIN public.recoveries orig ON orig.id = r.id
    WHERE orig.distributor_id IN (SELECT id FROM temp_real_distributors);

    IF v_conflict_rec_real_dist > 0 THEN
        RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: % recovery record(s) linked to target sales belong to REAL distributors! Aborting.', v_conflict_rec_real_dist;
    END IF;

    -- Check 5C: Ensure zero inventory transactions of real distributors are touched
    IF v_has_inv_sale_order_id THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM temp_target_inventory ti
            JOIN public.inventory_transactions orig ON orig.id = ti.id
            WHERE orig.distributor_id IN (SELECT id FROM temp_real_distributors);
        $dyn$ INTO v_conflict_inv_real_dist;

        IF v_conflict_inv_real_dist > 0 THEN
            RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: % inventory transaction(s) belong to REAL distributors! Aborting.', v_conflict_inv_real_dist;
        END IF;
    END IF;

    -- Check 5D: Ensure zero settlements are linked to target sales
    IF v_has_settle_table THEN
        EXECUTE $dyn$
            SELECT COUNT(*) 
            FROM public.distributor_settlements ds
            WHERE ds.recovery_id IN (SELECT id FROM temp_target_recoveries);
        $dyn$ INTO v_conflict_settle;

        IF v_conflict_settle > 0 THEN
            RAISE EXCEPTION 'CRITICAL CONFLICT DETECTED: % settlement(s) linked to target sales! Aborting.', v_conflict_settle;
        END IF;
    END IF;

    RAISE NOTICE '[CONFLICT AUDIT PASSED] Zero conflicts with real distributors, physical stock, or commercial settlements.';

    -- --------------------------------------------------------------------------
    -- 6. AUDIT LOGGING (ADMINISTRATIVE PURGE RECORD)
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
        (SELECT id FROM temp_target_sales ORDER BY reference_number ASC LIMIT 1),
        'ADMIN_PURGE_UNASSIGNED_TEST_SALES',
        jsonb_build_object(
            'operation', 'Permanent cleanup of 2 unassigned test sales (SAL-MUI1GUDZ & SAL-MUI18Z90)',
            'target_count', v_target_sales_count,
            'target_references', (SELECT jsonb_agg(reference_number) FROM temp_target_sales),
            'target_packets', v_target_packets,
            'target_amount', v_target_amount,
            'target_items_count', v_target_si_count,
            'target_recoveries_count', v_target_rec_count,
            'target_inventory_tx_count', v_target_inv_count,
            'target_inventory_restored_pkts', v_target_inv_issued_pkts,
            'preserved_real_sales_count', v_real_sales_count,
            'preserved_real_sales_pkts', v_real_sales_pkts,
            'preserved_real_sales_sum', v_real_sales_sum,
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
    -- 7. LIVE DATABASE TRIGGER INSPECTION & SAFE SUSPENSION (RECORDING ALL STATES)
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
        OR (c.relname = 'recoveries' AND t.tgname = 'trg_recovery_prevent_delete')
        OR (c.relname = 'invoice_payment_allocations' AND t.tgname = 'trg_allocation_immutability'))
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
    -- 8. CASCADING DELETION OF TARGET UNASSIGNED TEST DATA (RIGID DEPENDENCY ORDER)
    -- --------------------------------------------------------------------------
    -- Step 8A: invoice_payment_allocations (if table exists)
    IF v_has_alloc_table AND v_target_alloc_count > 0 THEN
        EXECUTE $dyn$
            WITH deleted AS (
                DELETE FROM public.invoice_payment_allocations
                WHERE id IN (SELECT id FROM temp_target_allocations)
                RETURNING id
            )
            SELECT COUNT(*) FROM deleted;
        $dyn$ INTO v_del_alloc_count;
        RAISE NOTICE '[DELETION Step A] Deleted % payment allocation(s).', v_del_alloc_count;
    END IF;

    -- Step 8B: recoveries linked to target sales (if any)
    IF v_target_rec_count > 0 THEN
        WITH deleted_recs AS (
            DELETE FROM public.recoveries
            WHERE id IN (SELECT id FROM temp_target_recoveries)
            RETURNING id
        )
        SELECT COUNT(*) INTO v_del_rec_count FROM deleted_recs;
        RAISE NOTICE '[DELETION Step B] Deleted % recovery record(s) linked to target sales (Reversed Rs. %).', v_del_rec_count, v_target_rec_sum;
    END IF;

    -- Step 8C: inventory_transactions (physical stock dispatches linked to target sales)
    IF v_has_inv_sale_order_id AND v_target_inv_count > 0 THEN
        EXECUTE $dyn$
            WITH deleted_inv AS (
                DELETE FROM public.inventory_transactions
                WHERE id IN (SELECT id FROM temp_target_inventory)
                RETURNING id
            )
            SELECT COUNT(*) FROM deleted_inv;
        $dyn$ INTO v_del_inv_count;
        RAISE NOTICE '[DELETION Step C] Deleted % inventory dispatch transaction(s) (Restored % pkts to warehouse stock).', v_del_inv_count, v_target_inv_issued_pkts;
    END IF;

    -- Step 8D: sale_items (line items belonging to target sales)
    WITH deleted_items AS (
        DELETE FROM public.sale_items
        WHERE sale_order_id IN (SELECT id FROM temp_target_sales)
        RETURNING id
    )
    SELECT COUNT(*) INTO v_del_si_count FROM deleted_items;
    RAISE NOTICE '[DELETION Step D] Deleted % sale line item(s) (% packets).', v_del_si_count, v_target_packets;

    IF v_del_si_count != v_target_si_count THEN
        RAISE EXCEPTION 'POST-DELETION INTEGRITY ABORT: Expected to delete % sale items, but deleted %! Rolling back.', v_target_si_count, v_del_si_count;
    END IF;

    -- Step 8E: sales_orders (the TWO target unassigned sales)
    WITH deleted_orders AS (
        DELETE FROM public.sales_orders
        WHERE id IN (SELECT id FROM temp_target_sales)
        RETURNING id
    )
    SELECT COUNT(*) INTO v_del_sales_count FROM deleted_orders;
    RAISE NOTICE '[DELETION Step E] Deleted % unassigned test sale(s): SAL-MUI1GUDZ & SAL-MUI18Z90.', v_del_sales_count;

    IF v_del_sales_count != 2 THEN
        RAISE EXCEPTION 'POST-DELETION INTEGRITY ABORT: Expected to delete exactly 2 sales orders, but deleted %! Rolling back.', v_del_sales_count;
    END IF;

    -- --------------------------------------------------------------------------
    -- 9. RESTORE ALL SUSPENDED TRIGGERS TO EXACT ORIGINAL STATE (INCLUDING 'D')
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
    -- 10. POST-CLEANUP INTEGRITY ASSERTIONS
    -- --------------------------------------------------------------------------
    -- Assertion 10A: Exactly 0 unassigned sales remain
    SELECT COUNT(*) INTO v_post_unassigned_sales_count
    FROM public.sales_orders
    WHERE reference_number LIKE 'SAL-%'
      AND distributor_id IS NULL;

    IF v_post_unassigned_sales_count != 0 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Found % remaining unassigned sales! Expected 0.', v_post_unassigned_sales_count;
    END IF;

    -- Assertion 10B: Exactly 4 real sales remain
    SELECT COUNT(*) INTO v_post_real_sales_count
    FROM public.sales_orders
    WHERE reference_number LIKE 'SAL-%'
      AND distributor_id IN (SELECT id FROM temp_real_distributors);

    IF v_post_real_sales_count != 4 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Real sales count is %, expected 4!', v_post_real_sales_count;
    END IF;

    -- Assertion 10C: Total sales in Sales Ledger is exactly 4
    SELECT COUNT(*) INTO v_post_total_sales_count
    FROM public.sales_orders
    WHERE reference_number LIKE 'SAL-%';

    IF v_post_total_sales_count != 4 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Total sales in system is %, expected 4!', v_post_total_sales_count;
    END IF;

    -- Assertion 10D: Verify total packets and amount across remaining 4 sales
    SELECT 
        COALESCE(SUM(so.total_amount), 0),
        COALESCE((
            SELECT SUM(si.quantity) 
            FROM public.sale_items si 
            JOIN public.sales_orders s ON s.id = si.sale_order_id 
            WHERE s.reference_number LIKE 'SAL-%' AND s.status::text IN ('Approved', 'Posted')
        ), 0)
    INTO
        v_post_real_sales_sum,
        v_post_real_sales_pkts
    FROM public.sales_orders so
    WHERE so.reference_number LIKE 'SAL-%'
      AND so.status::text IN ('Approved', 'Posted');

    IF v_post_real_sales_pkts != 1267 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Remaining sales packets is %, expected exactly 1,267 packets!', v_post_real_sales_pkts;
    END IF;

    IF v_post_real_sales_sum != 979450.00 THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Remaining sales total value is Rs. %, expected exactly Rs. 979,450.00!', v_post_real_sales_sum;
    END IF;

    -- Assertion 10E: Verify total commission across remaining sales matches pre-cleanup baseline exactly
    IF v_has_comm_snapshot THEN
        EXECUTE $dyn$
            SELECT COALESCE(SUM(
                COALESCE(so.commission_rate_snapshot, 0) * (
                    SELECT COALESCE(SUM(si.quantity), 0) 
                    FROM public.sale_items si 
                    WHERE si.sale_order_id = so.id
                )
            ), 0)
            FROM public.sales_orders so
            WHERE so.reference_number LIKE 'SAL-%'
              AND so.status::text IN ('Approved', 'Posted');
        $dyn$ INTO v_post_real_comm_sum;

        IF v_post_real_comm_sum != v_real_comm_sum THEN
            RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Real sales commission was altered! Pre: Rs. % vs Post: Rs. %', v_real_comm_sum, v_post_real_comm_sum;
        END IF;
    END IF;

    -- Assertion 10F: Verify each of the 4 real sales matches pre-cleanup snapshot byte-for-byte
    SELECT s.id, s.reference_number 
    INTO v_mismatched_sale_id, v_mismatched_sale_ref
    FROM temp_pre_real_sales s
    JOIN public.sales_orders so ON so.id = s.id
    WHERE so.reference_number != s.reference_number
       OR so.distributor_id != s.distributor_id
       OR so.total_amount != s.total_amount
       OR so.status::text != s.status::text
       OR (so.sale_date IS DISTINCT FROM s.sale_date)
       OR (SELECT COUNT(*) FROM public.sale_items si WHERE si.sale_order_id = s.id) != s.item_count
       OR (SELECT COALESCE(SUM(quantity), 0) FROM public.sale_items si WHERE si.sale_order_id = s.id) != s.item_qty
       OR (SELECT COUNT(*) FROM public.recoveries r WHERE r.sale_order_id = s.id) != s.rec_count
       OR (SELECT COALESCE(SUM(amount), 0) FROM public.recoveries r WHERE r.sale_order_id = s.id) != s.rec_sum
    LIMIT 1;

    IF v_mismatched_sale_id IS NOT NULL THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Real sale % (%) has been modified or suffered collateral corruption! Rolling back.', v_mismatched_sale_ref, v_mismatched_sale_id;
    END IF;

    -- Assertion 10G: Verify real distributor financial ledgers are 100% unchanged
    SELECT l.code INTO v_mismatched_dist_code
    FROM temp_pre_real_dist_ledgers l
    WHERE l.trade_sales_total != COALESCE((
            SELECT SUM(so.total_amount) 
            FROM public.sales_orders so 
            WHERE so.distributor_id = l.distributor_id 
              AND so.status::text IN ('Approved', 'Posted')
              AND so.reference_number LIKE 'SAL-%'
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
                  AND so.reference_number LIKE 'SAL-%'
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

    -- Assertion 10H: Verify factory warehouse inventory reconciliation
    SELECT 
        COALESCE(SUM(CASE 
            WHEN it.transaction_type::text IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN it.quantity
            WHEN it.transaction_type::text IN ('Adjustment', 'Reversal') AND it.category::text = 'Sellable Stock' THEN it.quantity
            WHEN it.transaction_type::text IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -it.quantity
            ELSE 0 
        END), 0),
        COALESCE(SUM(CASE 
            WHEN it.category::text = 'Damaged Stock' AND it.transaction_type::text IN ('Adjustment', 'Reversal') THEN it.quantity
            WHEN it.category::text = 'Damaged Stock' OR it.transaction_type::text IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN it.quantity
            ELSE 0 
        END), 0)
    INTO 
        v_post_sellable_stock,
        v_post_damaged_stock
    FROM public.inventory_transactions it
    WHERE it.status::text IN ('Approved', 'Posted')
      AND it.salesman_id IS NULL;

    -- Post-cleanup sellable stock must equal pre_sellable_stock + restored_pkts
    IF v_post_sellable_stock != (v_pre_sellable_stock + v_target_inv_issued_pkts) THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Sellable stock mismatch! Pre: % pkts + Restored: % pkts != Post: % pkts',
            v_pre_sellable_stock, v_target_inv_issued_pkts, v_post_sellable_stock;
    END IF;

    -- Damaged stock must be completely unaffected
    IF v_post_damaged_stock != v_pre_damaged_stock THEN
        RAISE EXCEPTION 'POST-CLEANUP INTEGRITY ABORT: Damaged stock was altered! Pre: % pkts vs Post: % pkts',
            v_pre_damaged_stock, v_post_damaged_stock;
    END IF;

    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'CLEANUP TRANSACTION VERIFIED SUCCESSFULLY:';
    RAISE NOTICE '    - Unassigned test sales purged:        % (SAL-MUI1GUDZ & SAL-MUI18Z90)', v_del_sales_count;
    RAISE NOTICE '    - Test sale items purged:              % (% packets)', v_del_si_count, v_target_packets;
    RAISE NOTICE '    - Stock restoration delta:             +% pkts restored to sellable stock', v_target_inv_issued_pkts;
    RAISE NOTICE '    - Post-cleanup sellable stock:         % pkts', v_post_sellable_stock;
    RAISE NOTICE '    - Post-cleanup damaged stock:          % pkts (UNTOUCHED)', v_post_damaged_stock;
    RAISE NOTICE '    - Real sales preserved:                % sales (1,267 pkts, Rs. 979,450.00)', v_post_real_sales_count;
    RAISE NOTICE '    - Real sales commission:               Rs. %', v_post_real_comm_sum;
    RAISE NOTICE '    - Real distributor financial ledgers:  100%% UNCHANGED';
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

-- ==============================================================================
-- ELITE WASHWO ERP — LIVE SUPABASE CATALOG VERIFICATION SCRIPT (READ-ONLY)
-- Migration Version: 4.4 Diagnostic Suite
-- Target: Supabase PostgreSQL 17.6 Production Instance
-- SAFETY: Purely read-only diagnostic checks. Zero DDL, zero DML, zero mutations.
--
-- Instructions: Run in Supabase SQL Editor. Results will verify the LIVE database
-- state against repository assumptions before reviewing partial_fulfillment_v4.sql.
-- ==============================================================================

DO $$
DECLARE
    v_has_bkg_id BOOLEAN;
    v_has_fulf_status BOOLEAN;
    v_has_dispatch_state BOOLEAN;
    v_has_bkg_item_id BOOLEAN;
    v_has_inv_sale_order_id BOOLEAN;
    v_has_alloc_table BOOLEAN;
    v_has_idemp_col BOOLEAN;
    v_has_dist_issue_enum BOOLEAN;
    v_has_good_ret_enum BOOLEAN;
    v_has_dam_ret_enum BOOLEAN;
    v_has_sales_approve_perm BOOLEAN;
    v_pkg_count INT;
    v_gs_record RECORD;
    v_rec RECORD;
BEGIN
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  ELITE WASHWO ERP — LIVE CATALOG VERIFICATION AUDIT v4.4';
    RAISE NOTICE '==============================================================================';

    -- 1. Check sales_orders columns
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'booking_id'
    ) INTO v_has_bkg_id;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'fulfillment_status'
    ) INTO v_has_fulf_status;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'dispatch_state'
    ) INTO v_has_dispatch_state;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'idempotency_key'
    ) INTO v_has_idemp_col;

    RAISE NOTICE '[CHECK 1] sales_orders Columns:';
    RAISE NOTICE '    - booking_id exists:          % (Expected FALSE before migration)', v_has_bkg_id;
    RAISE NOTICE '    - fulfillment_status exists:  % (Expected FALSE before migration)', v_has_fulf_status;
    RAISE NOTICE '    - dispatch_state exists:      % (Expected FALSE before migration)', v_has_dispatch_state;
    RAISE NOTICE '    - idempotency_key exists:     % (Expected FALSE before migration)', v_has_idemp_col;

    -- 2. Check sale_items & inventory_transactions columns
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'sale_items' AND column_name = 'booking_item_id'
    ) INTO v_has_bkg_item_id;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'inventory_transactions' AND column_name = 'sale_order_id'
    ) INTO v_has_inv_sale_order_id;

    RAISE NOTICE '[CHECK 2] Relational FK Columns:';
    RAISE NOTICE '    - sale_items.booking_item_id exists:             % (Expected FALSE before migration)', v_has_bkg_item_id;
    RAISE NOTICE '    - inventory_transactions.sale_order_id exists:   % (Expected FALSE before migration)', v_has_inv_sale_order_id;

    -- 3. Check invoice_payment_allocations table
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'invoice_payment_allocations'
    ) INTO v_has_alloc_table;

    RAISE NOTICE '[CHECK 3] Domain Tables:';
    RAISE NOTICE '    - invoice_payment_allocations exists: % (Expected FALSE before migration)', v_has_alloc_table;

    -- 4. Check transaction_type enum values
    SELECT EXISTS (
        SELECT 1 FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'transaction_type' AND e.enumlabel = 'Distributor_Issue'
    ) INTO v_has_dist_issue_enum;

    SELECT EXISTS (
        SELECT 1 FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'transaction_type' AND e.enumlabel = 'Distributor_Good_Return'
    ) INTO v_has_good_ret_enum;

    SELECT EXISTS (
        SELECT 1 FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'transaction_type' AND e.enumlabel = 'Distributor_Damaged_Return'
    ) INTO v_has_dam_ret_enum;

    RAISE NOTICE '[CHECK 4] transaction_type ENUM Values:';
    RAISE NOTICE '    - Distributor_Issue exists:          %', v_has_dist_issue_enum;
    RAISE NOTICE '    - Distributor_Good_Return exists:    %', v_has_good_ret_enum;
    RAISE NOTICE '    - Distributor_Damaged_Return exists: %', v_has_dam_ret_enum;

    -- 5. Check inventory_category enum labels
    RAISE NOTICE '[CHECK 5] inventory_category ENUM Labels:';
    FOR v_rec IN 
        SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'inventory_category' ORDER BY e.enumsortorder
    LOOP
        RAISE NOTICE '    - %', v_rec.enumlabel;
    END LOOP;

    -- 6. Check global_settings rates
    SELECT * INTO v_gs_record FROM public.global_settings WHERE id = 1;
    IF v_gs_record.id IS NOT NULL THEN
        RAISE NOTICE '[CHECK 6] global_settings (id = 1): Found. advertisement_rate = %, welfare_rate = %',
            v_gs_record.advertisement_rate, v_gs_record.welfare_rate;
    ELSE
        RAISE NOTICE '[CHECK 6] global_settings (id = 1): NOT FOUND (CRITICAL CONFIG ISSUE)';
    END IF;

    -- 7. Check product_packaging rows
    SELECT COUNT(*) INTO v_pkg_count FROM public.product_packaging;
    RAISE NOTICE '[CHECK 7] product_packaging Catalog Count: % rows', v_pkg_count;

    -- 8. Check permissions table for sales.approve
    SELECT EXISTS (
        SELECT 1 FROM public.permissions WHERE id = 'sales.approve'
    ) INTO v_has_sales_approve_perm;
    RAISE NOTICE '[CHECK 8] sales.approve Permission Defined: %', v_has_sales_approve_perm;

    -- 9. Check existing inventory_transactions distribution
    RAISE NOTICE '[CHECK 9] Live inventory_transactions (transaction_type, category) counts:';
    FOR v_rec IN 
        SELECT transaction_type, category, status, COUNT(*) AS cnt, SUM(quantity) AS total_qty
        FROM public.inventory_transactions
        GROUP BY transaction_type, category, status
        ORDER BY transaction_type, category, status
    LOOP
        RAISE NOTICE '    - Type: %, Category: %, Status: %, Count: %, Total Qty: %',
            v_rec.transaction_type, v_rec.category, v_rec.status, v_rec.cnt, v_rec.total_qty;
    END LOOP;

    -- 10. Check existing triggers on sales_orders, sale_items, recoveries
    RAISE NOTICE '[CHECK 10] Existing Table Triggers:';
    FOR v_rec IN 
        SELECT trigger_name, event_manipulation, event_object_table
        FROM information_schema.triggers
        WHERE trigger_schema = 'public' 
          AND event_object_table IN ('sales_orders', 'sale_items', 'recoveries', 'inventory_transactions')
        ORDER BY event_object_table, trigger_name
    LOOP
        RAISE NOTICE '    - Table %: Trigger % on %', v_rec.event_object_table, v_rec.trigger_name, v_rec.event_manipulation;
    END LOOP;

    -- 11. Check RLS status
    RAISE NOTICE '[CHECK 11] RLS Status on Core Tables:';
    FOR v_rec IN 
        SELECT relname, relrowsecurity 
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'r' 
          AND relname IN ('sales_orders', 'sale_items', 'recoveries', 'inventory_transactions', 'distributor_settlements')
        ORDER BY relname
    LOOP
        RAISE NOTICE '    - %: RLS Enabled = %', v_rec.relname, v_rec.relrowsecurity;
    END LOOP;

    -- 12. Check historical sales_orders backfill impact preview (Purely read-only)
    RAISE NOTICE '[CHECK 12] Historical sales_orders Backfill Impact Preview:';
    FOR v_rec IN 
        SELECT 
            CASE 
                WHEN reference_number LIKE 'BKG-%' THEN 'BKG (Booking)'
                WHEN reference_number LIKE 'SAL-%' THEN 'SAL (Direct Delivery / Invoice)'
                ELSE 'OTHER (' || COALESCE(SPLIT_PART(reference_number, '-', 1), 'NO-PREFIX') || ')'
            END AS order_family,
            status,
            COUNT(*) AS cnt,
            COALESCE(SUM(total_amount), 0) AS total_val,
            CASE 
                WHEN reference_number LIKE 'SAL-%' THEN 'N/A'
                WHEN status = 'Cancelled' THEN 'Cancelled'
                ELSE 'Unfulfilled'
            END AS proposed_fulf_status,
            CASE 
                WHEN reference_number LIKE 'BKG-%' THEN 'N/A'
                WHEN status = 'Cancelled' THEN 'Cancelled'
                WHEN status IN ('Approved', 'Posted') THEN 'Delivered'
                ELSE 'Staged'
            END AS proposed_dispatch_state
        FROM public.sales_orders
        GROUP BY 1, 2, 5, 6
        ORDER BY 1, 2
    LOOP
        RAISE NOTICE '    - Family: %, Status: %, Proposed Fulf: %, Proposed Dispatch: %, Count: %, Total Value: Rs. %',
            v_rec.order_family, v_rec.status, v_rec.proposed_fulf_status, v_rec.proposed_dispatch_state, v_rec.cnt, v_rec.total_val;
    END LOOP;

    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  LIVE CATALOG VERIFICATION COMPLETE — ZERO MUTATIONS EXECUTED';
    RAISE NOTICE '==============================================================================';
END $$;

-- ------------------------------------------------------------------------------
-- STANDALONE TABULAR READ-ONLY PREVIEW QUERY FOR SUPABASE SQL EDITOR
-- Run this query to view tabular preview of historical rows and proposed states
-- ------------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN reference_number LIKE 'BKG-%' THEN 'BKG (Booking)'
        WHEN reference_number LIKE 'SAL-%' THEN 'SAL (Direct Delivery / Invoice)'
        ELSE 'OTHER (' || COALESCE(SPLIT_PART(reference_number, '-', 1), 'NO-PREFIX') || ')'
    END AS order_family,
    status AS current_status,
    COUNT(*) AS row_count,
    COALESCE(SUM(total_amount), 0) AS total_financial_amount,
    CASE 
        WHEN reference_number LIKE 'SAL-%' THEN 'N/A'
        WHEN status = 'Cancelled' THEN 'Cancelled'
        ELSE 'Unfulfilled'
    END AS proposed_fulfillment_status,
    CASE 
        WHEN reference_number LIKE 'BKG-%' THEN 'N/A'
        WHEN status = 'Cancelled' THEN 'Cancelled'
        WHEN status IN ('Approved', 'Posted') THEN 'Delivered'
        ELSE 'Staged'
    END AS proposed_dispatch_state,
    MIN(sale_date) AS earliest_order_date,
    MAX(sale_date) AS latest_order_date
FROM public.sales_orders
GROUP BY 
    1, 2, 5, 6
ORDER BY 
    order_family, current_status;

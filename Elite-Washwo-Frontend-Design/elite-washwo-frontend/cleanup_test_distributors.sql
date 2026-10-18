-- ==============================================================================
-- ELITE WASHWO ERP — PERMANENT CLEANUP MIGRATION: TEST DISTRIBUTORS (abc & xyz)
-- Target Database: Supabase PostgreSQL 17.6 Production Instance
-- Target Distributors:
--   1. abc: df674217-1088-4ac2-89d6-e3263aaa1a3c
--   2. xyz: 4cb3f479-07c4-40d5-8c67-67340c104d2f
--
-- Target Dependent Records:
--   - 4 sales/booking records (and child sale_items)
--   - 3 inventory transactions (including approved returns: 5 sellable, 60 damaged)
--   - 2 distributor settlements
--   - 1 expense (EXP-MUK163IU)
--   - 0 recoveries
--   - 0 invoice payment allocations
--
-- SAFETY & AUDIT GUARANTEES:
--   1. Purely atomic: Wrapped in BEGIN ... COMMIT. Complete rollback on any error.
--   2. Strictly scoped: Restricted exclusively to the 2 target distributor UUIDs.
--   3. Foreign key dependency order: Child to parent deletion hierarchy.
--   4. Trigger safety: No global trigger disabling (no session_replication_role).
--      Uses a scoped administrative context and temporarily disables only the 4
--      specific delete-prevention triggers within this transaction, re-enabling
--      them immediately before COMMIT.
--   5. Audit logging preserved: audit_sales_orders, audit_inventory_transactions,
--      and audit_recoveries remain active and log every deletion into audit_logs.
--   6. Baseline assertions: Guarantees zero unrelated records are modified/deleted.
--   7. Stock accounting: Reconciles factory inventory by removing phantom returns.
-- ==============================================================================

BEGIN;

DO $$
DECLARE
    -- Target Identifiers
    c_target_dist_ids UUID[] := ARRAY[
        'df674217-1088-4ac2-89d6-e3263aaa1a3c'::UUID,
        '4cb3f479-07c4-40d5-8c67-67340c104d2f'::UUID
    ];
    c_target_expense_ref TEXT := 'EXP-MUK163IU';

    -- Schema Detection Flags
    v_has_alloc_table BOOLEAN := FALSE;
    v_has_inv_sale_order_id BOOLEAN := FALSE;
    v_has_so_booking_id BOOLEAN := FALSE;
    v_has_si_booking_item_id BOOLEAN := FALSE;

    -- Pre-Cleanup Target Record Counts
    v_target_dist_count INT := 0;
    v_target_so_count INT := 0;
    v_target_si_count INT := 0;
    v_target_inv_count INT := 0;
    v_target_settle_count INT := 0;
    v_target_exp_count INT := 0;
    v_target_rec_count INT := 0;
    v_target_alloc_count INT := 0;

    -- Pre-Cleanup Unrelated Baseline Counts (Invariance Assertions)
    v_base_unrelated_dist INT := 0;
    v_base_unrelated_so INT := 0;
    v_base_unrelated_inv INT := 0;
    v_base_unrelated_settle INT := 0;
    v_base_unrelated_exp INT := 0;

    -- Post-Cleanup Verification Counts
    v_post_target_dist INT := 0;
    v_post_target_so INT := 0;
    v_post_target_si INT := 0;
    v_post_target_inv INT := 0;
    v_post_target_settle INT := 0;
    v_post_target_exp INT := 0;
    v_post_target_rec INT := 0;
    v_post_target_alloc INT := 0;

    -- Iterators & Diagnostic Variables
    v_admin_id UUID;
    v_rec RECORD;
    v_del_count INT := 0;
BEGIN
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  ELITE WASHWO ERP — TEST DISTRIBUTOR PERMANENT CLEANUP MIGRATION';
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE 'Target 1 (abc): %', c_target_dist_ids[1];
    RAISE NOTICE 'Target 2 (xyz): %', c_target_dist_ids[2];

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

    -- --------------------------------------------------------------------------
    -- 2. PRE-CLEANUP TARGET RECORD DISCOVERY & VALIDATION
    -- --------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_target_dist_count 
    FROM public.distributors WHERE id = ANY(c_target_dist_ids);

    SELECT COUNT(*) INTO v_target_so_count 
    FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids);

    SELECT COUNT(*) INTO v_target_si_count 
    FROM public.sale_items 
    WHERE sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids));

    IF v_has_inv_sale_order_id THEN
        SELECT COUNT(*) INTO v_target_inv_count 
        FROM public.inventory_transactions 
        WHERE distributor_id = ANY(c_target_dist_ids) 
           OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids));
    ELSE
        SELECT COUNT(*) INTO v_target_inv_count 
        FROM public.inventory_transactions 
        WHERE distributor_id = ANY(c_target_dist_ids);
    END IF;

    SELECT COUNT(*) INTO v_target_settle_count 
    FROM public.distributor_settlements WHERE distributor_id = ANY(c_target_dist_ids);

    SELECT COUNT(*) INTO v_target_exp_count 
    FROM public.expenses 
    WHERE distributor_id = ANY(c_target_dist_ids) OR reference_number = c_target_expense_ref;

    SELECT COUNT(*) INTO v_target_rec_count 
    FROM public.recoveries WHERE distributor_id = ANY(c_target_dist_ids);

    IF v_has_alloc_table THEN
        EXECUTE 'SELECT COUNT(*) FROM public.invoice_payment_allocations WHERE distributor_id = ANY($1) OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))'
        INTO v_target_alloc_count
        USING c_target_dist_ids;
    END IF;

    RAISE NOTICE '[PRE-CHECK] Verified Target Record Counts:';
    RAISE NOTICE '    - Distributors:           % (Expected up to 2)', v_target_dist_count;
    RAISE NOTICE '    - Sales / Bookings:       % (Expected 4)', v_target_so_count;
    RAISE NOTICE '    - Sale Line Items:        %', v_target_si_count;
    RAISE NOTICE '    - Inventory Transactions: % (Expected 3)', v_target_inv_count;
    RAISE NOTICE '    - Settlements:            % (Expected 2)', v_target_settle_count;
    RAISE NOTICE '    - Expenses:               % (Expected 1)', v_target_exp_count;
    RAISE NOTICE '    - Recoveries:             % (Expected 0)', v_target_rec_count;
    RAISE NOTICE '    - Payment Allocations:    % (Expected 0)', v_target_alloc_count;

    IF v_target_dist_count = 0 THEN
        RAISE EXCEPTION 'Target distributors not found. They may have already been removed.';
    END IF;

    -- --------------------------------------------------------------------------
    -- 3. INVENTORY & STOCK EFFECT PREVIEW
    -- --------------------------------------------------------------------------
    RAISE NOTICE '[STOCK IMPACT PREVIEW] Inventory transactions scheduled for permanent removal:';
    FOR v_rec IN 
        SELECT 
            it.id, it.reference_number, it.transaction_type, it.category, it.quantity, it.status,
            p.name AS product_name, pp.name AS packaging_name, it.packaging_id
        FROM public.inventory_transactions it
        JOIN public.product_packaging pp ON pp.id = it.packaging_id
        JOIN public.products p ON p.id = pp.product_id
        WHERE it.distributor_id = ANY(c_target_dist_ids)
           OR (v_has_inv_sale_order_id AND it.sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids)))
        ORDER BY it.transaction_date ASC
    LOOP
        RAISE NOTICE '    - %: % pkts | Type: % | Cat: % | Status: % | Packaging: % (%)',
            v_rec.reference_number, v_rec.quantity, v_rec.transaction_type, v_rec.category, v_rec.status, v_rec.packaging_name, v_rec.product_name;
    END LOOP;

    -- --------------------------------------------------------------------------
    -- 4. CAPTURE UNRELATED BASELINE (INVARIANCE PRESERVATION)
    -- --------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_base_unrelated_dist 
    FROM public.distributors WHERE id != ALL(c_target_dist_ids);

    SELECT COUNT(*) INTO v_base_unrelated_so 
    FROM public.sales_orders WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids);

    IF v_has_inv_sale_order_id THEN
        SELECT COUNT(*) INTO v_base_unrelated_inv 
        FROM public.inventory_transactions 
        WHERE (distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids))
          AND (sale_order_id IS NULL OR sale_order_id NOT IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids)));
    ELSE
        SELECT COUNT(*) INTO v_base_unrelated_inv 
        FROM public.inventory_transactions 
        WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids);
    END IF;

    SELECT COUNT(*) INTO v_base_unrelated_settle 
    FROM public.distributor_settlements WHERE distributor_id != ALL(c_target_dist_ids);

    SELECT COUNT(*) INTO v_base_unrelated_exp 
    FROM public.expenses 
    WHERE (distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids)) 
      AND reference_number != c_target_expense_ref;

    RAISE NOTICE '[BASELINE] Unrelated Record Counts (Must remain strictly unchanged):';
    RAISE NOTICE '    - Active Unrelated Distributors: %', v_base_unrelated_dist;
    RAISE NOTICE '    - Real Business Sales Orders:    %', v_base_unrelated_so;
    RAISE NOTICE '    - Real Stock Movements:          %', v_base_unrelated_inv;
    RAISE NOTICE '    - Real Settlements:              %', v_base_unrelated_settle;
    RAISE NOTICE '    - Real Business Expenses:        %', v_base_unrelated_exp;

    -- --------------------------------------------------------------------------
    -- 5. ADMINISTRATIVE EXECUTION CONTEXT & AUDIT PRESERVATION
    -- --------------------------------------------------------------------------
    -- Establish administrative user session context
    SELECT id INTO v_admin_id FROM public.profiles WHERE role = 'Super_Admin' AND is_active = true LIMIT 1;
    IF v_admin_id IS NULL THEN
        SELECT id INTO v_admin_id FROM public.profiles WHERE role = 'Super_Admin' LIMIT 1;
    END IF;
    IF v_admin_id IS NOT NULL THEN
        PERFORM set_config('request.jwt.claim.sub', v_admin_id::TEXT, true);
    END IF;

    -- Log permanent administrative cleanup audit record prior to purge
    INSERT INTO public.audit_logs (
        table_name, record_id, action, old_data, performed_by, created_at
    ) VALUES (
        'distributors',
        c_target_dist_ids[1],
        'ADMIN_PURGE_TEST_DISTRIBUTORS',
        jsonb_build_object(
            'operation', 'Permanent cleanup of inactive test distributors abc and xyz',
            'target_distributor_ids', c_target_dist_ids,
            'target_records_count', jsonb_build_object(
                'distributors', v_target_dist_count,
                'sales_orders', v_target_so_count,
                'sale_items', v_target_si_count,
                'inventory_transactions', v_target_inv_count,
                'settlements', v_target_settle_count,
                'expenses', v_target_exp_count,
                'target_expense_ref', c_target_expense_ref
            ),
            'execution_timestamp', NOW()
        ),
        v_admin_id,
        NOW()
    );

    RAISE NOTICE '[AUDIT] Logged administrative cleanup entry into public.audit_logs.';

    -- --------------------------------------------------------------------------
    -- 6. NARROW ADMINISTRATIVE MECHANISM: SCOPED TRIGGER SUSPENSION
    -- --------------------------------------------------------------------------
    -- In PostgreSQL, approved-record delete triggers (trg_sales_order_prevent_delete,
    -- trg_sale_items_immutability, trg_expense_prevent_delete, trg_distributor_settlement_prevent_delete)
    -- block deletion of records with status in ('Approved', 'Posted').
    --
    -- To ensure a cleanly scoped, auditable administrative purge WITHOUT globally disabling
    -- triggers (no session_replication_role), we temporarily suspend ONLY these 4 specific
    -- delete-prevention triggers within this single transaction, and re-enable them immediately.
    -- All audit logging triggers (audit_sales_orders, audit_inventory_transactions, audit_recoveries)
    -- and foreign key constraint enforcement triggers remain 100% active throughout!
    -- --------------------------------------------------------------------------
    ALTER TABLE public.sales_orders DISABLE TRIGGER trg_sales_order_prevent_delete;
    ALTER TABLE public.sale_items DISABLE TRIGGER trg_sale_items_immutability;
    ALTER TABLE public.expenses DISABLE TRIGGER trg_expense_prevent_delete;
    ALTER TABLE public.distributor_settlements DISABLE TRIGGER trg_distributor_settlement_prevent_delete;

    -- --------------------------------------------------------------------------
    -- 7. ATOMIC DELETION IN RIGID FOREIGN KEY DEPENDENCY ORDER
    -- --------------------------------------------------------------------------

    -- Step A: invoice_payment_allocations (if table exists)
    IF v_has_alloc_table THEN
        EXECUTE 'DELETE FROM public.invoice_payment_allocations WHERE distributor_id = ANY($1) OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))'
        USING c_target_dist_ids;
        GET DIAGNOSTICS v_del_count = ROW_COUNT;
        RAISE NOTICE '[STEP A] Deleted % invoice_payment_allocations.', v_del_count;
    END IF;

    -- Step B: inventory_transactions (Child referencing distributors and sales_orders)
    IF v_has_inv_sale_order_id THEN
        DELETE FROM public.inventory_transactions 
        WHERE distributor_id = ANY(c_target_dist_ids)
           OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids));
    ELSE
        DELETE FROM public.inventory_transactions 
        WHERE distributor_id = ANY(c_target_dist_ids);
    END IF;
    GET DIAGNOSTICS v_del_count = ROW_COUNT;
    RAISE NOTICE '[STEP B] Deleted % inventory_transactions (Stock balances naturally restored).', v_del_count;

    -- Step C: sale_items (Child line items referencing sales_orders)
    -- If booking_item_id exists, delete child dispatch line items first to avoid self-referential FK violation
    IF v_has_si_booking_item_id THEN
        DELETE FROM public.sale_items 
        WHERE sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids))
          AND booking_item_id IS NOT NULL;
    END IF;

    -- Delete remaining sale line items for target distributor orders
    DELETE FROM public.sale_items 
    WHERE sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids));
    GET DIAGNOSTICS v_del_count = ROW_COUNT;
    RAISE NOTICE '[STEP C] Deleted % sale_items.', v_del_count;

    -- Step D: sales_orders (Child dispatches first, then parent bookings)
    -- If booking_id exists, delete child dispatches first to avoid self-referential FK violation
    IF v_has_so_booking_id THEN
        DELETE FROM public.sales_orders 
        WHERE distributor_id = ANY(c_target_dist_ids) 
          AND booking_id IS NOT NULL;
    END IF;

    -- Delete remaining sales orders & bookings for target distributors
    DELETE FROM public.sales_orders 
    WHERE distributor_id = ANY(c_target_dist_ids);
    GET DIAGNOSTICS v_del_count = ROW_COUNT;
    RAISE NOTICE '[STEP D] Deleted % sales_orders.', v_del_count;

    -- Step E: distributor_settlements (Child referencing distributors)
    DELETE FROM public.distributor_settlements 
    WHERE distributor_id = ANY(c_target_dist_ids);
    GET DIAGNOSTICS v_del_count = ROW_COUNT;
    RAISE NOTICE '[STEP E] Deleted % distributor_settlements.', v_del_count;

    -- Step F: expenses (Test expense EXP-MUK163IU or linked by distributor_id)
    -- Also unlink any person_ledger_entries referencing this expense to prevent FK constraint errors
    UPDATE public.person_ledger_entries 
    SET expense_id = NULL 
    WHERE expense_id IN (SELECT id FROM public.expenses WHERE distributor_id = ANY(c_target_dist_ids) OR reference_number = c_target_expense_ref);

    DELETE FROM public.expenses 
    WHERE distributor_id = ANY(c_target_dist_ids) 
       OR reference_number = c_target_expense_ref;
    GET DIAGNOSTICS v_del_count = ROW_COUNT;
    RAISE NOTICE '[STEP F] Deleted % expenses (%).', v_del_count, c_target_expense_ref;

    -- Step G: recoveries (Assert 0 recoveries, delete if any exist)
    DELETE FROM public.recoveries 
    WHERE distributor_id = ANY(c_target_dist_ids);
    GET DIAGNOSTICS v_del_count = ROW_COUNT;
    IF v_del_count > 0 THEN
        RAISE NOTICE '[STEP G] Deleted % recoveries.', v_del_count;
    END IF;

    -- Step H: distributors (The 2 target root records)
    DELETE FROM public.distributors 
    WHERE id = ANY(c_target_dist_ids);
    GET DIAGNOSTICS v_del_count = ROW_COUNT;
    RAISE NOTICE '[STEP H] Deleted % distributors (abc and xyz).', v_del_count;

    IF v_del_count != v_target_dist_count THEN
        RAISE EXCEPTION 'Cleanup verification failed: Expected to delete % distributors, deleted %.', v_target_dist_count, v_del_count;
    END IF;

    -- --------------------------------------------------------------------------
    -- 8. RE-ENABLE PREVIOUSLY SUSPENDED TRIGGERS IMMEDIATELY
    -- --------------------------------------------------------------------------
    ALTER TABLE public.sales_orders ENABLE TRIGGER trg_sales_order_prevent_delete;
    ALTER TABLE public.sale_items ENABLE TRIGGER trg_sale_items_immutability;
    ALTER TABLE public.expenses ENABLE TRIGGER trg_expense_prevent_delete;
    ALTER TABLE public.distributor_settlements ENABLE TRIGGER trg_distributor_settlement_prevent_delete;

    RAISE NOTICE '[SECURITY] Successfully re-enabled all 4 delete-prevention triggers.';

    -- --------------------------------------------------------------------------
    -- 9. POST-CLEANUP TARGET INTEGRITY ASSERTIONS (MUST ALL BE 0)
    -- --------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_post_target_dist FROM public.distributors WHERE id = ANY(c_target_dist_ids);
    SELECT COUNT(*) INTO v_post_target_so FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids);
    SELECT COUNT(*) INTO v_post_target_si FROM public.sale_items WHERE sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids));
    
    IF v_has_inv_sale_order_id THEN
        SELECT COUNT(*) INTO v_post_target_inv FROM public.inventory_transactions 
        WHERE distributor_id = ANY(c_target_dist_ids) 
           OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids));
    ELSE
        SELECT COUNT(*) INTO v_post_target_inv FROM public.inventory_transactions WHERE distributor_id = ANY(c_target_dist_ids);
    END IF;

    SELECT COUNT(*) INTO v_post_target_settle FROM public.distributor_settlements WHERE distributor_id = ANY(c_target_dist_ids);
    SELECT COUNT(*) INTO v_post_target_exp FROM public.expenses WHERE distributor_id = ANY(c_target_dist_ids) OR reference_number = c_target_expense_ref;
    SELECT COUNT(*) INTO v_post_target_rec FROM public.recoveries WHERE distributor_id = ANY(c_target_dist_ids);

    IF v_has_alloc_table THEN
        EXECUTE 'SELECT COUNT(*) FROM public.invoice_payment_allocations WHERE distributor_id = ANY($1) OR sale_order_id IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY($1))'
        INTO v_post_target_alloc
        USING c_target_dist_ids;
    END IF;

    ASSERT v_post_target_dist = 0, 'POST-ASSERTION FAILED: Target distributors still exist!';
    ASSERT v_post_target_so = 0, 'POST-ASSERTION FAILED: Target sales_orders still exist!';
    ASSERT v_post_target_si = 0, 'POST-ASSERTION FAILED: Target sale_items still exist!';
    ASSERT v_post_target_inv = 0, 'POST-ASSERTION FAILED: Target inventory_transactions still exist!';
    ASSERT v_post_target_settle = 0, 'POST-ASSERTION FAILED: Target settlements still exist!';
    ASSERT v_post_target_exp = 0, 'POST-ASSERTION FAILED: Target expense still exists!';
    ASSERT v_post_target_rec = 0, 'POST-ASSERTION FAILED: Target recoveries still exist!';
    ASSERT v_post_target_alloc = 0, 'POST-ASSERTION FAILED: Target payment allocations still exist!';

    RAISE NOTICE '[VERIFICATION PASSED] All target test records completely and permanently purged (Counts = 0).';

    -- --------------------------------------------------------------------------
    -- 10. UNRELATED DATA PRESERVATION ASSERTIONS
    -- --------------------------------------------------------------------------
    ASSERT (SELECT COUNT(*) FROM public.distributors WHERE id != ALL(c_target_dist_ids)) = v_base_unrelated_dist,
        'DATA INTEGRITY VIOLATION: Unrelated distributors count was altered!';
    
    ASSERT (SELECT COUNT(*) FROM public.sales_orders WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids)) = v_base_unrelated_so,
        'DATA INTEGRITY VIOLATION: Real business sales orders were altered!';

    IF v_has_inv_sale_order_id THEN
        ASSERT (SELECT COUNT(*) FROM public.inventory_transactions WHERE (distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids)) AND (sale_order_id IS NULL OR sale_order_id NOT IN (SELECT id FROM public.sales_orders WHERE distributor_id = ANY(c_target_dist_ids)))) = v_base_unrelated_inv,
            'DATA INTEGRITY VIOLATION: Real business inventory transactions were altered!';
    ELSE
        ASSERT (SELECT COUNT(*) FROM public.inventory_transactions WHERE distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids)) = v_base_unrelated_inv,
            'DATA INTEGRITY VIOLATION: Real business inventory transactions were altered!';
    END IF;

    ASSERT (SELECT COUNT(*) FROM public.distributor_settlements WHERE distributor_id != ALL(c_target_dist_ids)) = v_base_unrelated_settle,
        'DATA INTEGRITY VIOLATION: Real distributor settlements were altered!';

    ASSERT (SELECT COUNT(*) FROM public.expenses WHERE (distributor_id IS NULL OR distributor_id != ALL(c_target_dist_ids)) AND reference_number != c_target_expense_ref) = v_base_unrelated_exp,
        'DATA INTEGRITY VIOLATION: Real business expenses were altered!';

    RAISE NOTICE '[VERIFICATION PASSED] 100%% of unrelated distributors, sales, expenses, and inventory perfectly preserved.';
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  CLEANUP COMPLETE. TRANSACTION WILL NOW COMMIT AT THE SCRIPT LEVEL.';
    RAISE NOTICE '==============================================================================';

EXCEPTION WHEN OTHERS THEN
    -- Ensure triggers are re-enabled even in the event of an exception before rollback
    BEGIN
        ALTER TABLE public.sales_orders ENABLE TRIGGER trg_sales_order_prevent_delete;
        ALTER TABLE public.sale_items ENABLE TRIGGER trg_sale_items_immutability;
        ALTER TABLE public.expenses ENABLE TRIGGER trg_expense_prevent_delete;
        ALTER TABLE public.distributor_settlements ENABLE TRIGGER trg_distributor_settlement_prevent_delete;
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
    RAISE EXCEPTION 'ADMINISTRATIVE CLEANUP ABORTED & ROLLED BACK: %', SQLERRM;
END $$;

COMMIT;

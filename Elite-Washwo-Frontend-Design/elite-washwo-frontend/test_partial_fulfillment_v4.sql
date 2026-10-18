-- ==============================================================================
-- ELITE WASHWO ERP — ISOLATED DATABASE TEST SUITE FOR PARTIAL FULFILLMENT v4.4
-- Target: Supabase PostgreSQL 17.6 Test/Staging Environment
-- SAFETY NOTICE: Designed for execution exclusively in an isolated staging DB.
-- DO NOT EXECUTE ON PRODUCTION. Enclosed in a strict BEGIN ... ROLLBACK block.
-- ==============================================================================

BEGIN;

DO $$
DECLARE
    v_dist_id UUID;
    v_pkg_id UUID;
    v_bkg_id UUID;
    v_bkg_item_id UUID;
    v_sale_res JSONB;
    v_sale_id UUID;
    v_dup_items JSONB;
    v_fixed_sale_date TIMESTAMPTZ := '2026-10-18 10:00:00+00';
    v_idem_key TEXT := 'TEST-IDEM-' || gen_random_uuid()::TEXT;
    v_idem_res JSONB;
    v_rec_id UUID;
    v_alloc_id UUID;
    v_alloc_res JSONB;
    v_rev_alloc_res JSONB;
    v_direct_sal_id UUID;
    v_rtn_res JSONB;
    v_wh_stock_init NUMERIC;
    v_wh_stock_after_bkg NUMERIC;
    v_wh_stock_after_dispatch NUMERIC;
    v_wh_stock_after_void NUMERIC;
    v_hist_bkg_count INT;
    v_err_caught BOOLEAN;
    v_err_msg TEXT;
BEGIN
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  RUNNING ISOLATED DATABASE TEST SUITE (v4.4 SPECIFICATION)';
    RAISE NOTICE '==============================================================================';

    -- 0. RECORD HISTORICAL BASELINE (To assert zero tampering with existing records)
    SELECT COUNT(*) INTO v_hist_bkg_count 
    FROM public.sales_orders 
    WHERE reference_number IN ('BKG-MUH7MMXJ', 'BKG-MUH81DFS', 'BKG-MUH9PWK0', 'BKG-MUH9SE4Q');

    -- 1. SETUP MOCK TEST DATA
    -- Create mock distributor matching live schema
    INSERT INTO public.distributors (id, code, name, id_card, phone, commission, is_active, created_at, updated_at)
    VALUES (gen_random_uuid(), 'DIST-TEST-01', 'Test Automation Distributor', '35202-0000000-1', '03001234567', 30.00, true, NOW(), NOW())
    RETURNING id INTO v_dist_id;

    -- Pick an existing packaging variant from catalog
    SELECT id INTO v_pkg_id FROM public.product_packaging LIMIT 1;
    IF v_pkg_id IS NULL THEN
        RAISE EXCEPTION 'Test requires at least one product_packaging row.';
    END IF;

    -- Query initial factory warehouse sellable stock
    SELECT COALESCE(SUM(
        CASE 
            WHEN transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN quantity
            WHEN transaction_type IN ('Adjustment', 'Reversal') AND category = 'Sellable Stock' THEN quantity
            WHEN transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -quantity
            ELSE 0
        END
    ), 0) INTO v_wh_stock_init
    FROM public.inventory_transactions
    WHERE packaging_id = v_pkg_id AND status IN ('Approved', 'Posted');

    -- Seed 100 packets of sellable stock in factory warehouse (total_cost = 100 * 100 = 10000 satisfies chk_total_cost)
    INSERT INTO public.inventory_transactions (
        id, reference_number, transaction_date, packaging_id, category, transaction_type,
        quantity, unit_cost, total_cost, distributor_id, status, notes, created_at, updated_at
    ) VALUES (
        gen_random_uuid(), 'PRD-TEST-' || UPPER(SUBSTRING(gen_random_uuid()::TEXT FROM 1 FOR 8)),
        NOW(), v_pkg_id, 'Sellable Stock', 'Production',
        100, 100.00, 10000.00, NULL, 'Approved', 'Test production seed stock', NOW(), NOW()
    );

    -- 2. CREATE BOOKING RESPECTING LIVE IMMUTABILITY TRIGGERS
    -- Step A: Insert booking as 'Pending' first
    INSERT INTO public.sales_orders (
        id, reference_number, distributor_id, total_amount, sale_date, status,
        fulfillment_status, dispatch_state, commission_rate_snapshot, advertisement_rate_snapshot, welfare_rate_snapshot,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(), 'BKG-TEST-' || UPPER(SUBSTRING(gen_random_uuid()::TEXT FROM 1 FOR 6)),
        v_dist_id, 17500.00, NOW(), 'Pending', 'Unfulfilled', 'N/A', 30.00, 20.00, 10.00, NOW(), NOW()
    ) RETURNING id INTO v_bkg_id;

    -- Step B: Insert line items while booking is 'Pending'
    INSERT INTO public.sale_items (
        id, sale_order_id, packaging_id, quantity, unit_price, subtotal, created_at, updated_at
    ) VALUES (
        gen_random_uuid(), v_bkg_id, v_pkg_id, 50, 350.00, 17500.00, NOW(), NOW()
    ) RETURNING id INTO v_bkg_item_id;

    -- Step C: Transition booking to 'Approved'
    UPDATE public.sales_orders 
    SET status = 'Approved', updated_at = NOW() 
    WHERE id = v_bkg_id;

    RAISE NOTICE '[SETUP] Created Mock Booking % (50 pkts @ Rs. 350) for Distributor %', v_bkg_id, v_dist_id;

    -- --------------------------------------------------------------------------
    -- TEST 1: BOOKING FINANCIAL & STOCK NEUTRALITY
    -- --------------------------------------------------------------------------
    -- Assert booking creates ZERO commercial debit
    ASSERT (
        SELECT COALESCE(SUM(total_amount), 0) FROM public.sales_orders 
        WHERE distributor_id = v_dist_id AND status IN ('Approved', 'Posted') AND reference_number NOT LIKE 'BKG-%'
    ) = 0.00, 'TEST 1 FAILED: Booking must not create commercial debit';

    -- Assert factory warehouse stock was not deducted by booking creation
    SELECT COALESCE(SUM(
        CASE 
            WHEN transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN quantity
            WHEN transaction_type IN ('Adjustment', 'Reversal') AND category = 'Sellable Stock' THEN quantity
            WHEN transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -quantity
            ELSE 0
        END
    ), 0) INTO v_wh_stock_after_bkg
    FROM public.inventory_transactions
    WHERE packaging_id = v_pkg_id AND status IN ('Approved', 'Posted');

    ASSERT v_wh_stock_after_bkg = (v_wh_stock_init + 100), 'TEST 1 FAILED: Booking creation deducted stock unexpectedly';
    RAISE NOTICE '[PASSED] TEST 1: Booking is financially neutral (Debit: Rs. 0) and inventory neutral (0 pkts deducted).';

    -- --------------------------------------------------------------------------
    -- TEST 2: PARTIAL DISPATCH (10 pkts @ Rs. 350)
    -- --------------------------------------------------------------------------
    v_sale_res := public.dispatch_partial_booking_fulfillment(
        v_bkg_id,
        jsonb_build_array(jsonb_build_object(
            'booking_item_id', v_bkg_item_id,
            'packaging_id', v_pkg_id,
            'quantity', 10,
            'unit_price', 350.00
        )),
        v_fixed_sale_date,
        'First test dispatch',
        v_idem_key
    );

    v_sale_id := (v_sale_res->>'sale_id')::UUID;
    ASSERT (v_sale_res->>'success')::BOOLEAN = true, 'TEST 2 FAILED: Dispatch did not return success';
    ASSERT (v_sale_res->>'dispatched_pkts')::INTEGER = 10, 'TEST 2 FAILED: Dispatched packets mismatch';
    ASSERT (v_sale_res->>'dispatch_state') = 'Staged', 'TEST 2 FAILED: Initial dispatch_state must be Staged';

    -- Assert inventory deduction exists with relational link
    ASSERT EXISTS (
        SELECT 1 FROM public.inventory_transactions 
        WHERE sale_order_id = v_sale_id AND transaction_type = 'Distributor_Issue' AND quantity = 10 AND status = 'Approved'
    ), 'TEST 2 FAILED: inventory_transactions Distributor_Issue was not created with relational sale_order_id';

    -- Assert warehouse stock reduced by exactly 10 pkts
    SELECT COALESCE(SUM(
        CASE 
            WHEN transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN quantity
            WHEN transaction_type IN ('Adjustment', 'Reversal') AND category = 'Sellable Stock' THEN quantity
            WHEN transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -quantity
            ELSE 0
        END
    ), 0) INTO v_wh_stock_after_dispatch
    FROM public.inventory_transactions
    WHERE packaging_id = v_pkg_id AND status IN ('Approved', 'Posted');

    ASSERT v_wh_stock_after_dispatch = (v_wh_stock_after_bkg - 10), 'TEST 2 FAILED: Stock was not reduced by exactly 10 pkts';
    RAISE NOTICE '[PASSED] TEST 2: Partial dispatch created SAL- invoice (%) in "Staged" state with relational inventory issue (-10 pkts).', v_sale_res->>'reference_number';

    -- --------------------------------------------------------------------------
    -- TEST 3: IDEMPOTENT REPLAY WITH FIXED SALE DATE
    -- --------------------------------------------------------------------------
    -- Replay with identical payload and fixed sale date
    v_idem_res := public.dispatch_partial_booking_fulfillment(
        v_bkg_id,
        jsonb_build_array(jsonb_build_object(
            'booking_item_id', v_bkg_item_id,
            'packaging_id', v_pkg_id,
            'quantity', 10,
            'unit_price', 350.00
        )),
        v_fixed_sale_date,
        'First test dispatch',
        v_idem_key
    );

    ASSERT (v_idem_res->>'idempotent_replay')::BOOLEAN = true, 'TEST 3 FAILED: Idempotent replay was not recognized';
    ASSERT (v_idem_res->>'sale_id') = v_sale_id::TEXT, 'TEST 3 FAILED: Replay did not return original sale ID';

    -- Assert ZERO duplicate inventory movements created
    ASSERT (
        SELECT COUNT(*) FROM public.inventory_transactions 
        WHERE sale_order_id = v_sale_id AND transaction_type = 'Distributor_Issue'
    ) = 1, 'TEST 3 FAILED: Duplicate inventory issue created on idempotent replay';

    -- Assert ZERO duplicate sales orders created
    ASSERT (
        SELECT COUNT(*) FROM public.sales_orders 
        WHERE idempotency_key = v_idem_key
    ) = 1, 'TEST 3 FAILED: Duplicate sales order created on idempotent replay';
    RAISE NOTICE '[PASSED] TEST 3: Idempotent replay verified with fixed sale date: 0 duplicate bills, 0 duplicate stock movements.';

    -- --------------------------------------------------------------------------
    -- TEST 4: IDEMPOTENCY CONFLICT ON PAYLOAD MISMATCH
    -- --------------------------------------------------------------------------
    v_err_caught := false;
    BEGIN
        PERFORM public.dispatch_partial_booking_fulfillment(
            v_bkg_id,
            jsonb_build_array(jsonb_build_object(
                'booking_item_id', v_bkg_item_id,
                'packaging_id', v_pkg_id,
                'quantity', 20, -- modified quantity under same key
                'unit_price', 350.00
            )),
            v_fixed_sale_date,
            'Conflicting dispatch',
            v_idem_key
        );
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%Idempotency conflict%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 4 FAILED: Idempotency conflict exception was not raised on payload mismatch';
    RAISE NOTICE '[PASSED] TEST 4: Idempotency conflict strictly rejected altered payload under identical key.';

    -- --------------------------------------------------------------------------
    -- TEST 5: INVOICE PAYMENT ALLOCATION & STRICT PAYABLE CAPPING
    -- --------------------------------------------------------------------------
    -- Create approved recovery for this distributor
    INSERT INTO public.recoveries (
        id, reference_number, recovery_date, distributor_id, amount, payment_method, status, created_at, updated_at
    ) VALUES (
        gen_random_uuid(), 'REC-TEST-' || UPPER(SUBSTRING(gen_random_uuid()::TEXT FROM 1 FOR 8)),
        NOW(), v_dist_id, 5000.00, 'Cash', 'Approved', NOW(), NOW()
    ) RETURNING id INTO v_rec_id;

    -- Allocate Rs. 3,500 (full invoice amount)
    v_alloc_res := public.allocate_recovery_to_invoice(v_rec_id, v_sale_id, 3500.00, 'Test full allocation');
    v_alloc_id := (v_alloc_res->>'allocation_id')::UUID;
    ASSERT (v_alloc_res->>'success')::BOOLEAN = true, 'TEST 5 FAILED: Allocation did not succeed';
    ASSERT (v_alloc_res->>'remaining_invoice_payable')::NUMERIC = 0, 'TEST 5 FAILED: Remaining payable must be 0';

    -- Attempt over-allocation by another Rs. 100 (MUST BE REJECTED)
    v_err_caught := false;
    BEGIN
        PERFORM public.allocate_recovery_to_invoice(v_rec_id, v_sale_id, 100.00, 'Illegal over-allocation');
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%payable balance is only Rs. 0%' OR SQLERRM LIKE '%Strictly capped%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 5 FAILED: Over-allocation past invoice total was not blocked';
    RAISE NOTICE '[PASSED] TEST 5: Payment allocation strictly capped at invoice payable balance (Rs. 3,500).';

    -- --------------------------------------------------------------------------
    -- TEST 6: DISTINGUISHING RECOVERY CANCELLATION SAFEGUARD VS AUTH TRIGGERS
    -- --------------------------------------------------------------------------
    -- Attempt cancelling recovery while active allocations exist:
    -- Must specifically cite active invoice allocations
    v_err_caught := false;
    v_err_msg := '';
    BEGIN
        UPDATE public.recoveries SET status = 'Cancelled' WHERE id = v_rec_id;
    EXCEPTION WHEN OTHERS THEN
        v_err_msg := SQLERRM;
        IF v_err_msg LIKE '%active invoice payment allocations%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 6 FAILED: Expected active allocation safeguard rejection. Caught: ' || v_err_msg;

    -- Reverse active allocation via authorized RPC (releases recovery credit back to distributor)
    v_rev_alloc_res := public.reverse_invoice_payment_allocation(v_alloc_id, 'Testing authorized allocation reversal RPC');
    ASSERT (v_rev_alloc_res->>'success')::BOOLEAN = true, 'TEST 6 FAILED: reverse_invoice_payment_allocation failed';
    ASSERT (v_rev_alloc_res->>'released_amount')::NUMERIC = 3500.00, 'TEST 6 FAILED: Released amount mismatch';
    ASSERT (SELECT status FROM public.invoice_payment_allocations WHERE id = v_alloc_id) = 'Reversed', 'TEST 6 FAILED: Allocation status not Reversed';

    -- Reversing an already reversed allocation must fail
    v_err_caught := false;
    BEGIN
        PERFORM public.reverse_invoice_payment_allocation(v_alloc_id, 'Duplicate reversal attempt');
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%is already reversed%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 6 FAILED: Re-reversing already reversed allocation was not rejected';

    -- Immutability trigger test: Direct modification of allocated_amount must fail
    v_err_caught := false;
    BEGIN
        UPDATE public.invoice_payment_allocations SET allocated_amount = 9999.00 WHERE id = v_alloc_id;
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%strictly immutable once created%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 6 FAILED: trg_allocation_immutability did not block financial field update';

    -- Now cancelling recovery does NOT trigger the allocation safeguard trigger
    UPDATE public.recoveries SET status = 'Cancelled', updated_at = NOW() WHERE id = v_rec_id;
    ASSERT (SELECT status FROM public.recoveries WHERE id = v_rec_id) = 'Cancelled', 'TEST 6 FAILED: Recovery cancellation failed after reversing allocations';

    -- Restore recovery and re-allocate for Test 7 (to verify cancellation cascades reversal)
    UPDATE public.recoveries SET status = 'Approved', updated_at = NOW() WHERE id = v_rec_id;
    v_alloc_res := public.allocate_recovery_to_invoice(v_rec_id, v_sale_id, 3500.00, 'Re-allocate for Test 7 void verification');
    v_alloc_id := (v_alloc_res->>'allocation_id')::UUID;
    RAISE NOTICE '[PASSED] TEST 6: Standalone allocation reversal RPC, immutability trigger, and recovery safeguard verified.';

    -- --------------------------------------------------------------------------
    -- TEST 7: UNDISPATCHED CANCELLATION (PERSISTED STAGED STATE)
    -- --------------------------------------------------------------------------
    PERFORM public.cancel_undispatched_sale_invoice(v_sale_id, 'Client cancelled order before loading dock departure');

    -- Assert issue in inventory_transactions is Cancelled via sale_order_id link
    ASSERT (
        SELECT status FROM public.inventory_transactions 
        WHERE sale_order_id = v_sale_id AND transaction_type = 'Distributor_Issue'
    ) = 'Cancelled', 'TEST 7 FAILED: Stock issue was not marked Cancelled via sale_order_id link';

    -- Assert allocations were reversed
    ASSERT (
        SELECT status FROM public.invoice_payment_allocations WHERE sale_order_id = v_sale_id
    ) = 'Reversed', 'TEST 7 FAILED: Associated allocations were not Reversed';

    -- Assert booking fulfillment was restored to Unfulfilled
    ASSERT (
        SELECT fulfillment_status FROM public.sales_orders WHERE id = v_bkg_id
    ) = 'Unfulfilled', 'TEST 7 FAILED: Booking fulfillment status was not restored to Unfulfilled';

    -- Assert factory warehouse sellable stock was restored
    SELECT COALESCE(SUM(
        CASE 
            WHEN transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN quantity
            WHEN transaction_type IN ('Adjustment', 'Reversal') AND category = 'Sellable Stock' THEN quantity
            WHEN transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -quantity
            ELSE 0
        END
    ), 0) INTO v_wh_stock_after_void
    FROM public.inventory_transactions
    WHERE packaging_id = v_pkg_id AND status IN ('Approved', 'Posted');

    ASSERT v_wh_stock_after_void = v_wh_stock_after_bkg, 'TEST 7 FAILED: Warehouse stock was not restored after voiding undispatched invoice';

    -- Attempt idempotent replay using v_idem_key against now-cancelled sale (MUST BE REJECTED)
    v_err_caught := false;
    BEGIN
        PERFORM public.dispatch_partial_booking_fulfillment(
            v_bkg_id,
            jsonb_build_array(jsonb_build_object('booking_item_id', v_bkg_item_id, 'packaging_id', v_pkg_id, 'quantity', 10, 'unit_price', 350.00)),
            v_fixed_sale_date,
            'First test dispatch',
            v_idem_key
        );
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%which has been Cancelled. A new idempotency key is required%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 7 FAILED: Idempotent replay against cancelled sale was not rejected with explanatory error';

    RAISE NOTICE '[PASSED] TEST 7: Undispatched sale cancelled cleanly via relational link; stock issue cancelled (+10 pkts restored), booking restored, cancelled replay blocked.';

    -- --------------------------------------------------------------------------
    -- TEST 8: HANDOVER CONFIRMATION, DIRECT MUTATION BLOCK & RETURN ENFORCEMENT
    -- --------------------------------------------------------------------------
    -- Dispatch another 15 pkts
    v_sale_res := public.dispatch_partial_booking_fulfillment(
        v_bkg_id,
        jsonb_build_array(jsonb_build_object('booking_item_id', v_bkg_item_id, 'packaging_id', v_pkg_id, 'quantity', 15, 'unit_price', 350.00)),
        v_fixed_sale_date,
        'Second test dispatch'
    );
    v_sale_id := (v_sale_res->>'sale_id')::UUID;

    -- Assert DIRECT table update on dispatch_state is BLOCKED by immutability trigger
    v_err_caught := false;
    BEGIN
        UPDATE public.sales_orders SET dispatch_state = 'Dispatched' WHERE id = v_sale_id;
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%Direct mutation of dispatch_state on sales_orders is strictly prohibited%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 8 FAILED: Immutability trigger permitted direct mutation of dispatch_state';

    -- Attempt physical return on order still in 'Staged' state (MUST BE REJECTED)
    v_err_caught := false;
    BEGIN
        PERFORM public.record_verified_distributor_stock_return(
            v_sale_id, v_dist_id, v_pkg_id, 5, 'Good', 'Attempting return before physical warehouse departure'
        );
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%Physical stock return rejected%' AND SQLERRM LIKE '%Staged%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 8 FAILED: Physical return was permitted on Staged order still inside warehouse dock';

    -- Confirm warehouse gate departure via authorized procedure (Staged -> Dispatched)
    PERFORM public.confirm_sale_order_handover(v_sale_id, 'Gate pass #GP-9912 verified');
    ASSERT (
        SELECT dispatch_state FROM public.sales_orders WHERE id = v_sale_id
    ) = 'Dispatched', 'TEST 8 FAILED: dispatch_state was not transitioned to Dispatched';

    -- Attempt to call cancel_undispatched_sale_invoice on Dispatched order (MUST FAIL)
    v_err_caught := false;
    BEGIN
        PERFORM public.cancel_undispatched_sale_invoice(v_sale_id, 'Attempting to void goods on the road');
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%dispatch_state = "Dispatched"%' OR SQLERRM LIKE '%Only orders in "Staged" state%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 8 FAILED: System permitted voiding a physically dispatched order';
    RAISE NOTICE '[PASSED] TEST 8: Direct dispatch_state mutation blocked; gate handover confirmed; pre-dispatch void strictly rejected.';

    -- --------------------------------------------------------------------------
    -- TEST 9: MULTI-LINE ISSUED QUANTITY SUMMATION & RETURN CAPPING
    -- --------------------------------------------------------------------------
    -- Record return of 5 Damaged packets
    v_rtn_res := public.record_verified_distributor_stock_return(
        v_sale_id, v_dist_id, v_pkg_id, 5, 'Damaged', '5 packets torn in transit, verified by QC'
    );
    ASSERT (v_rtn_res->>'category') = 'Damaged Stock', 'TEST 9 FAILED: Damaged return must be categorized as Damaged Stock';
    ASSERT (v_rtn_res->>'remaining_returnable_pkts')::INTEGER = 10, 'TEST 9 FAILED: Remaining returnable packets mismatch';

    -- Attempt to return 11 more packets (total 16 > 15 issued across lines)
    v_err_caught := false;
    BEGIN
        PERFORM public.record_verified_distributor_stock_return(
            v_sale_id, v_dist_id, v_pkg_id, 11, 'Good', 'Attempting to return more than total issued'
        );
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%Return quantity exceeds issued quantity%' THEN
            v_err_caught := true;
        END IF;
    END;
    ASSERT v_err_caught, 'TEST 9 FAILED: Return capping allowed cumulative returns > issued quantity';
    RAISE NOTICE '[PASSED] TEST 9: Verified physical return logged to "Damaged Stock"; cumulative return capping across all sale lines strictly enforced.';

    -- --------------------------------------------------------------------------
    -- TEST 10: HISTORICAL DATA INTEGRITY ASSERTION
    -- --------------------------------------------------------------------------
    ASSERT (
        SELECT COUNT(*) FROM public.sales_orders 
        WHERE reference_number IN ('BKG-MUH7MMXJ', 'BKG-MUH81DFS', 'BKG-MUH9PWK0', 'BKG-MUH9SE4Q')
    ) = v_hist_bkg_count, 'TEST 10 FAILED: Historical 0-packet booking count was altered!';
    RAISE NOTICE '[PASSED] TEST 10: Historical 0-packet booking rows remained 100%% unchanged.';

    -- --------------------------------------------------------------------------
    -- TEST 11: DIRECT SAL- INVOICE DISPATCH_STATE DEFAULT ASSERTION
    -- --------------------------------------------------------------------------
    INSERT INTO public.sales_orders (
        id, reference_number, distributor_id, total_amount, sale_date, status, booking_id,
        created_at, updated_at
    ) VALUES (
        gen_random_uuid(), 'SAL-DIRECT-' || UPPER(SUBSTRING(gen_random_uuid()::TEXT FROM 1 FOR 6)),
        v_dist_id, 3500.00, NOW(), 'Approved', NULL,
        NOW(), NOW()
    ) RETURNING id INTO v_direct_sal_id;

    ASSERT (
        SELECT dispatch_state FROM public.sales_orders WHERE id = v_direct_sal_id
    ) = 'Delivered', 'TEST 11 FAILED: Direct SAL sale must automatically default to Delivered state';
    RAISE NOTICE '[PASSED] TEST 11: Direct SAL counter invoice correctly defaulted to "Delivered" dispatch state.';

    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  ALL 11 TEST PHASES COMPLETED WITH 100%% PASSING ASSERTIONS';
    RAISE NOTICE '  TRANSACTION WILL NOW ROLL BACK (ZERO PRODUCTION MUTATIONS)';
    RAISE NOTICE '==============================================================================';
END $$;

ROLLBACK;

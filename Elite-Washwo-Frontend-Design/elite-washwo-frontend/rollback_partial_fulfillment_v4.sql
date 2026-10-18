-- ==============================================================================
-- ELITE WASHWO ERP — PARTIAL BOOKING FULFILLMENT ROLLBACK SCRIPT (v4.4)
-- Migration: partial_fulfillment_v4.sql Rollback Strategy
-- Target Database: Supabase PostgreSQL 17.6 Production Instance
-- SAFETY: Purely transactional (enclosed in BEGIN ... COMMIT).
--         ZERO CASCADE: Uses STRICT RESTRICT on all DROPs.
--         Pre-checks verify zero transaction data exists before dropping anything.
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 1. PRE-ROLLBACK DEPENDENCY & DATA INTEGRITY ASSERTIONS
-- Aborts immediately if ANY transaction has touched new columns or tables
-- ------------------------------------------------------------------------------
DO $$
DECLARE
    v_alloc_count INT := 0;
    v_bkg_link_count INT := 0;
    v_item_link_count INT := 0;
    v_inv_link_count INT := 0;
    v_dep_views_count INT := 0;
    v_ext_fk_count INT := 0;
BEGIN
    RAISE NOTICE 'Executing pre-rollback safety dependency assertions...';

    -- Assertion 1: Ensure zero records exist in invoice_payment_allocations
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'invoice_payment_allocations'
    ) THEN
        SELECT COUNT(*) INTO v_alloc_count FROM public.invoice_payment_allocations;
        IF v_alloc_count > 0 THEN
            RAISE EXCEPTION 'ROLLBACK ABORTED: invoice_payment_allocations contains % records. Production transactions exist. Use Tier 1 Operational Deactivation instead of destructive schema rollback.', v_alloc_count;
        END IF;
    END IF;

    -- Assertion 2: Ensure zero sales_orders have booking_id populated
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'booking_id'
    ) THEN
        SELECT COUNT(*) INTO v_bkg_link_count FROM public.sales_orders WHERE booking_id IS NOT NULL;
        IF v_bkg_link_count > 0 THEN
            RAISE EXCEPTION 'ROLLBACK ABORTED: % sales_orders have active booking_id links. Use Tier 1 Operational Deactivation instead.', v_bkg_link_count;
        END IF;
    END IF;

    -- Assertion 3: Ensure zero sale_items have booking_item_id populated
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'sale_items' AND column_name = 'booking_item_id'
    ) THEN
        SELECT COUNT(*) INTO v_item_link_count FROM public.sale_items WHERE booking_item_id IS NOT NULL;
        IF v_item_link_count > 0 THEN
            RAISE EXCEPTION 'ROLLBACK ABORTED: % sale_items have active booking_item_id links. Use Tier 1 Operational Deactivation instead.', v_item_link_count;
        END IF;
    END IF;

    -- Assertion 4: Ensure zero inventory_transactions have sale_order_id populated
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'inventory_transactions' AND column_name = 'sale_order_id'
    ) THEN
        SELECT COUNT(*) INTO v_inv_link_count FROM public.inventory_transactions WHERE sale_order_id IS NOT NULL;
        IF v_inv_link_count > 0 THEN
            RAISE EXCEPTION 'ROLLBACK ABORTED: % inventory_transactions have active sale_order_id links. Use Tier 1 Operational Deactivation instead.', v_inv_link_count;
        END IF;
    END IF;

    -- Assertion 5: Ensure zero external database views or rules depend on invoice_payment_allocations
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'invoice_payment_allocations') THEN
        SELECT COUNT(*) INTO v_dep_views_count
        FROM pg_depend d
        JOIN pg_rewrite r ON r.oid = d.objid
        JOIN pg_class c ON c.oid = r.ev_class
        WHERE d.refobjid = 'public.invoice_payment_allocations'::regclass
          AND c.relname != 'invoice_payment_allocations';

        IF v_dep_views_count > 0 THEN
            RAISE EXCEPTION 'ROLLBACK ABORTED: % external views or rewrite rules depend on invoice_payment_allocations. Drop them manually first.', v_dep_views_count;
        END IF;
    END IF;

    -- Assertion 6: Ensure zero external foreign key constraints reference invoice_payment_allocations
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'invoice_payment_allocations') THEN
        SELECT COUNT(*) INTO v_ext_fk_count
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_schema = 'public'
          AND ccu.table_name = 'invoice_payment_allocations'
          AND tc.table_name != 'invoice_payment_allocations';

        IF v_ext_fk_count > 0 THEN
            RAISE EXCEPTION 'ROLLBACK ABORTED: % external foreign key constraints reference invoice_payment_allocations. Inspect dependencies first.', v_ext_fk_count;
        END IF;
    END IF;

    RAISE NOTICE 'Pre-rollback dependency assertions PASSED. Proceeding with clean restoration.';
END $$;

-- ------------------------------------------------------------------------------
-- 2. REVOKE EXPLICIT FUNCTION EXECUTE GRANTS
-- ------------------------------------------------------------------------------
REVOKE ALL ON FUNCTION public.allocate_recovery_to_invoice(UUID, UUID, NUMERIC, TEXT, TEXT) FROM authenticated, anon, PUBLIC;
REVOKE ALL ON FUNCTION public.reverse_invoice_payment_allocation(UUID, TEXT) FROM authenticated, anon, PUBLIC;
REVOKE ALL ON FUNCTION public.dispatch_partial_booking_fulfillment(UUID, JSONB, TIMESTAMPTZ, TEXT, TEXT) FROM authenticated, anon, PUBLIC;
REVOKE ALL ON FUNCTION public.confirm_sale_order_handover(UUID, TEXT) FROM authenticated, anon, PUBLIC;
REVOKE ALL ON FUNCTION public.cancel_undispatched_sale_invoice(UUID, TEXT) FROM authenticated, anon, PUBLIC;
REVOKE ALL ON FUNCTION public.record_verified_distributor_stock_return(UUID, UUID, UUID, INTEGER, TEXT, TEXT) FROM authenticated, anon, PUBLIC;

-- ------------------------------------------------------------------------------
-- 3. DROP MIGRATION TRIGGERS
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_sales_order_booking_immutability ON public.sales_orders;
DROP TRIGGER IF EXISTS trg_sales_order_new_row_defaults ON public.sales_orders;
DROP TRIGGER IF EXISTS trg_sale_items_booking_immutability ON public.sale_items;
DROP TRIGGER IF EXISTS trg_allocation_immutability ON public.invoice_payment_allocations;
DROP TRIGGER IF EXISTS trg_prevent_cancel_allocated_recovery ON public.recoveries;

-- ------------------------------------------------------------------------------
-- 4. DROP MIGRATION PROCEDURES & FUNCTIONS (STRICTLY RESTRICT)
-- ------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.allocate_recovery_to_invoice(UUID, UUID, NUMERIC, TEXT, TEXT) RESTRICT;
DROP FUNCTION IF EXISTS public.reverse_invoice_payment_allocation(UUID, TEXT) RESTRICT;
DROP FUNCTION IF EXISTS public.dispatch_partial_booking_fulfillment(UUID, JSONB, TIMESTAMPTZ, TEXT, TEXT) RESTRICT;
DROP FUNCTION IF EXISTS public.confirm_sale_order_handover(UUID, TEXT) RESTRICT;
DROP FUNCTION IF EXISTS public.cancel_undispatched_sale_invoice(UUID, TEXT) RESTRICT;
DROP FUNCTION IF EXISTS public.record_verified_distributor_stock_return(UUID, UUID, UUID, INTEGER, TEXT, TEXT) RESTRICT;
DROP FUNCTION IF EXISTS public.handle_booking_relationship_immutability() RESTRICT;
DROP FUNCTION IF EXISTS public.handle_allocation_immutability() RESTRICT;
DROP FUNCTION IF EXISTS public.handle_sales_order_new_row_defaults() RESTRICT;
DROP FUNCTION IF EXISTS public.check_recovery_cancellation_allocations() RESTRICT;

-- ------------------------------------------------------------------------------
-- 5. DROP INVOICE PAYMENT ALLOCATION TABLE (STRICTLY RESTRICT, NEVER CASCADE)
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS public.invoice_payment_allocations RESTRICT;

-- ------------------------------------------------------------------------------
-- 6. DROP ADDED CONSTRAINTS & INDEXES
-- ------------------------------------------------------------------------------
ALTER TABLE public.sales_orders DROP CONSTRAINT IF EXISTS chk_no_self_booking_parent;
ALTER TABLE public.sales_orders DROP CONSTRAINT IF EXISTS chk_fulfillment_status_values;
ALTER TABLE public.sales_orders DROP CONSTRAINT IF EXISTS chk_dispatch_state_values;

DROP INDEX IF EXISTS public.idx_sales_orders_booking_id;
DROP INDEX IF EXISTS public.idx_sales_orders_fulfillment_status;
DROP INDEX IF EXISTS public.idx_sales_orders_dispatch_state;
DROP INDEX IF EXISTS public.uq_sales_orders_idempotency_key;

DROP INDEX IF EXISTS public.idx_sale_items_booking_item_id;
DROP INDEX IF EXISTS public.idx_inv_trans_sale_order_id;

-- ------------------------------------------------------------------------------
-- 7. DROP ADDED COLUMNS (STRICTLY RESTRICT)
-- ------------------------------------------------------------------------------
ALTER TABLE public.sale_items DROP COLUMN IF EXISTS booking_item_id RESTRICT;
ALTER TABLE public.inventory_transactions DROP COLUMN IF EXISTS sale_order_id RESTRICT;
ALTER TABLE public.sales_orders 
    DROP COLUMN IF EXISTS booking_id RESTRICT,
    DROP COLUMN IF EXISTS fulfillment_status RESTRICT,
    DROP COLUMN IF EXISTS dispatch_state RESTRICT,
    DROP COLUMN IF EXISTS idempotency_key RESTRICT,
    DROP COLUMN IF EXISTS idempotency_hash RESTRICT;

-- ------------------------------------------------------------------------------
-- 8. RESTORE BASE TABLE-LEVEL UPDATE PRIVILEGES
-- ------------------------------------------------------------------------------
GRANT UPDATE ON public.sales_orders TO authenticated;
GRANT UPDATE ON public.sale_items TO authenticated;
GRANT UPDATE ON public.inventory_transactions TO authenticated;

COMMIT;

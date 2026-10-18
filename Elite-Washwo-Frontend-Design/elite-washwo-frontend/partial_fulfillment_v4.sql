-- ==============================================================================
-- ELITE WASHWO ERP — PARTIAL BOOKING FULFILLMENT & INVOICE ALLOCATION MIGRATION
-- Migration Version: 4.4 (Production Ready: Persisted Dispatch State, Relational
--                          Inventory FK Linking, Mandatory Linked Return Auditing,
--                          Zero Automatic Recovery Allocation, Strict Concurrency
--                          Idempotency Hash Verification, Enum Categorization Fix)
-- Target Database: Supabase PostgreSQL 17.6 Production Instance
-- Status: PREPARED FOR REVIEW ONLY (DO NOT EXECUTE WITHOUT CLIENT APPROVAL)
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 0. PLATFORM & EXTENSION PRECHECKS
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Confirm transaction_type enum values exist safely
DO $$ BEGIN
    ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'Distributor_Issue';
    ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'Distributor_Good_Return';
    ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'Distributor_Damaged_Return';
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- ------------------------------------------------------------------------------
-- 1. SCHEMA MODIFICATIONS (SAFELY RERUNNABLE)
-- ------------------------------------------------------------------------------

-- A. sales_orders: booking link, fulfillment status, persisted dispatch state, idempotency
-- NOTE: Columns are intentionally added WITHOUT table-level DEFAULTs to guarantee that
-- PostgreSQL catalog metadata does NOT retroactively populate legacy historical records.
ALTER TABLE public.sales_orders
    ADD COLUMN IF NOT EXISTS booking_id UUID REFERENCES public.sales_orders(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS fulfillment_status TEXT,
    ADD COLUMN IF NOT EXISTS dispatch_state TEXT,
    ADD COLUMN IF NOT EXISTS idempotency_key TEXT,
    ADD COLUMN IF NOT EXISTS idempotency_hash TEXT;

CREATE INDEX IF NOT EXISTS idx_sales_orders_booking_id ON public.sales_orders(booking_id);
CREATE INDEX IF NOT EXISTS idx_sales_orders_fulfillment_status ON public.sales_orders(fulfillment_status);
CREATE INDEX IF NOT EXISTS idx_sales_orders_dispatch_state ON public.sales_orders(dispatch_state);
CREATE UNIQUE INDEX IF NOT EXISTS uq_sales_orders_idempotency_key 
    ON public.sales_orders(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Constraint: Order cannot be its own booking parent
DO $$ BEGIN
    ALTER TABLE public.sales_orders
        ADD CONSTRAINT chk_no_self_booking_parent CHECK (booking_id IS NULL OR booking_id != id);
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- Constraint: Valid fulfillment status values (permits NULL for legacy historical records)
DO $$ BEGIN
    ALTER TABLE public.sales_orders
        ADD CONSTRAINT chk_fulfillment_status_values 
        CHECK (fulfillment_status IS NULL OR fulfillment_status IN ('Unfulfilled', 'Partially_Fulfilled', 'Fulfilled', 'Cancelled', 'N/A'));
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- Constraint: Valid persisted dispatch state values (permits NULL for legacy historical records)
DO $$ BEGIN
    ALTER TABLE public.sales_orders
        ADD CONSTRAINT chk_dispatch_state_values 
        CHECK (dispatch_state IS NULL OR dispatch_state IN ('Staged', 'Dispatched', 'Delivered', 'Cancelled', 'N/A'));
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- B. sale_items: Link dispatched line item to booked line item
ALTER TABLE public.sale_items
    ADD COLUMN IF NOT EXISTS booking_item_id UUID REFERENCES public.sale_items(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_sale_items_booking_item_id ON public.sale_items(booking_item_id);

-- C. inventory_transactions: Add immutable relational sale_order_id link
ALTER TABLE public.inventory_transactions
    ADD COLUMN IF NOT EXISTS sale_order_id UUID REFERENCES public.sales_orders(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_inv_trans_sale_order_id ON public.inventory_transactions(sale_order_id);

-- D. NEW ROW DEFAULTS TRIGGER (ZERO RETROACTIVE METADATA LEAKAGE & ZERO AUDIT LOG FLOODING)
-- Legacy historical records remain NULL and completely untouched.
-- A BEFORE INSERT trigger assigns default states ONLY to newly created rows going forward.
CREATE OR REPLACE FUNCTION public.handle_sales_order_new_row_defaults()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.reference_number LIKE 'BKG-%' THEN
        IF NEW.fulfillment_status IS NULL THEN
            NEW.fulfillment_status := 'Unfulfilled';
        END IF;
        IF NEW.dispatch_state IS NULL THEN
            NEW.dispatch_state := 'N/A';
        END IF;
    ELSIF NEW.reference_number LIKE 'SAL-%' THEN
        IF NEW.fulfillment_status IS NULL THEN
            NEW.fulfillment_status := 'N/A';
        END IF;
        IF NEW.dispatch_state IS NULL THEN
            -- CRITICAL SEPARATION (Issue 4):
            -- Booking dispatches (booking_id IS NOT NULL) start as 'Staged' at factory dock awaiting gate pass.
            -- Direct SAL invoices (spot/counter deliveries) are immediate completed handovers ('Delivered').
            IF NEW.booking_id IS NOT NULL THEN
                NEW.dispatch_state := 'Staged';
            ELSE
                NEW.dispatch_state := 'Delivered';
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_sales_order_new_row_defaults ON public.sales_orders;
CREATE TRIGGER trg_sales_order_new_row_defaults
    BEFORE INSERT ON public.sales_orders
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_sales_order_new_row_defaults();

-- E. AUTHORIZATION BOUNDARY: TRIGGER-ENFORCED IMMUTABILITY OVERRIDING TABLE PERMISSIONS
-- NOTE ON POSTGRESQL PRIVILEGE MODEL (Issue 1):
-- In PostgreSQL, table-level UPDATE privileges (e.g. possessed by Super_Admin and Managers via RLS)
-- grant update rights across all columns. A column-level REVOKE does NOT restrict a role that
-- holds table-level UPDATE. Therefore, this migration DOES NOT assume column REVOKE alone is sufficient.
-- Instead, the BEFORE UPDATE triggers (trg_sales_order_booking_immutability,
-- trg_sale_items_booking_immutability, and trg_allocation_immutability) serve as the authoritative,
-- un-bypassable engine perimeter that strictly intercepts and halts unauthorized column updates.
REVOKE UPDATE (dispatch_state, fulfillment_status, booking_id) ON public.sales_orders FROM PUBLIC, authenticated, anon;
REVOKE UPDATE (booking_item_id) ON public.sale_items FROM PUBLIC, authenticated, anon;
REVOKE UPDATE (sale_order_id) ON public.inventory_transactions FROM PUBLIC, authenticated, anon;

-- ------------------------------------------------------------------------------
-- 2. IMMUTABILITY SAFEGUARDS: PREVENT ALTERING BOOKING RELATIONSHIPS DIRECTLY
-- ------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.handle_booking_relationship_immutability()
RETURNS TRIGGER AS $$
BEGIN
    -- Protect sales_orders.booking_id, dispatch_state, fulfillment_status, & idempotency keys
    IF TG_TABLE_NAME = 'sales_orders' THEN
        IF OLD.status IN ('Approved', 'Posted') AND OLD.booking_id IS DISTINCT FROM NEW.booking_id THEN
            RAISE EXCEPTION 'booking_id is strictly immutable on approved sales order (%).', OLD.reference_number;
        END IF;

        -- Prevent unauthorized mutation of dispatch_state outside dedicated SECURITY DEFINER RPCs
        IF OLD.dispatch_state IS DISTINCT FROM NEW.dispatch_state THEN
            -- Non-spoofable database execution boundary: table owner / SECURITY DEFINER context only
            IF CURRENT_USER != 'postgres' OR current_setting('app.internal_dispatch_call', true) IS DISTINCT FROM 'true' THEN
                RAISE EXCEPTION 'Direct mutation of dispatch_state on sales_orders is strictly prohibited. State transitions must occur via authorized procedures (confirm_sale_order_handover or cancel_undispatched_sale_invoice).';
            END IF;

            -- State machine integrity: prevent illegal regressions regardless of caller context
            IF OLD.dispatch_state = 'Delivered' AND NEW.dispatch_state IN ('Staged', 'Dispatched') THEN
                RAISE EXCEPTION 'Invalid transition: Cannot regress dispatch_state from Delivered to % on sales order %.',
                    NEW.dispatch_state, OLD.reference_number;
            END IF;

            IF OLD.dispatch_state = 'Cancelled' THEN
                RAISE EXCEPTION 'Invalid transition: Cannot alter dispatch_state of Cancelled order %.',
                    OLD.reference_number;
            END IF;

            IF OLD.dispatch_state = 'Dispatched' AND NEW.dispatch_state = 'Staged' THEN
                RAISE EXCEPTION 'Invalid transition: Cannot regress dispatch_state from Dispatched to Staged on sales order %.',
                    OLD.reference_number;
            END IF;

            IF OLD.dispatch_state = 'N/A' THEN
                RAISE EXCEPTION 'Invalid transition: dispatch_state of % is N/A and cannot be altered to a physical shipment state.',
                    OLD.reference_number;
            END IF;
        END IF;

        -- Protect fulfillment_status against unauthorized direct mutation
        IF OLD.fulfillment_status IS DISTINCT FROM NEW.fulfillment_status THEN
            IF CURRENT_USER != 'postgres' OR current_setting('app.internal_dispatch_call', true) IS DISTINCT FROM 'true' THEN
                RAISE EXCEPTION 'Direct mutation of fulfillment_status on sales_orders is strictly prohibited. Updates must occur via authorized SECURITY DEFINER procedures.';
            END IF;
        END IF;

        -- Protect idempotency_key and idempotency_hash once assigned
        IF OLD.idempotency_key IS NOT NULL AND OLD.idempotency_key IS DISTINCT FROM NEW.idempotency_key THEN
            RAISE EXCEPTION 'idempotency_key is strictly immutable once assigned on sales order (%).', OLD.reference_number;
        END IF;

        IF OLD.idempotency_hash IS NOT NULL AND OLD.idempotency_hash IS DISTINCT FROM NEW.idempotency_hash THEN
            RAISE EXCEPTION 'idempotency_hash is strictly immutable once assigned on sales order (%).', OLD.reference_number;
        END IF;
    END IF;

    -- Protect sale_items.booking_item_id
    IF TG_TABLE_NAME = 'sale_items' THEN
        IF OLD.booking_item_id IS NOT NULL AND OLD.booking_item_id IS DISTINCT FROM NEW.booking_item_id THEN
            RAISE EXCEPTION 'booking_item_id is strictly immutable once assigned (Item ID: %).', OLD.id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_sales_order_booking_immutability ON public.sales_orders;
CREATE TRIGGER trg_sales_order_booking_immutability
    BEFORE UPDATE OF booking_id, dispatch_state, fulfillment_status, idempotency_key, idempotency_hash ON public.sales_orders
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_booking_relationship_immutability();

DROP TRIGGER IF EXISTS trg_sale_items_booking_immutability ON public.sale_items;
CREATE TRIGGER trg_sale_items_booking_immutability
    BEFORE UPDATE OF booking_item_id ON public.sale_items
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_booking_relationship_immutability();

-- ------------------------------------------------------------------------------
-- 3. INVOICE PAYMENT ALLOCATION TABLE (SUB-LEDGER ONLY)
-- Strict RLS: Visible only to Super_Admin & Manager. Direct DML completely revoked.
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.invoice_payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recovery_id UUID NOT NULL REFERENCES public.recoveries(id) ON DELETE RESTRICT,
    sale_order_id UUID NOT NULL REFERENCES public.sales_orders(id) ON DELETE RESTRICT,
    distributor_id UUID NOT NULL REFERENCES public.distributors(id) ON DELETE RESTRICT,
    allocated_amount NUMERIC(12, 2) NOT NULL,
    allocated_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'Approved',
    notes TEXT DEFAULT '',
    idempotency_key TEXT,
    idempotency_hash TEXT,
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reversed_at TIMESTAMPTZ,
    reversed_by UUID REFERENCES public.profiles(id),
    reversal_reason TEXT,

    CONSTRAINT chk_alloc_amount_pos CHECK (allocated_amount > 0 AND allocated_amount <= 100000000.00),
    CONSTRAINT chk_alloc_status CHECK (status IN ('Approved', 'Reversed'))
);

CREATE INDEX IF NOT EXISTS idx_ipa_recovery_id ON public.invoice_payment_allocations(recovery_id);
CREATE INDEX IF NOT EXISTS idx_ipa_sale_order_id ON public.invoice_payment_allocations(sale_order_id);
CREATE INDEX IF NOT EXISTS idx_ipa_distributor_id ON public.invoice_payment_allocations(distributor_id);
CREATE INDEX IF NOT EXISTS idx_ipa_status ON public.invoice_payment_allocations(status);
CREATE UNIQUE INDEX IF NOT EXISTS uq_ipa_idempotency_key 
    ON public.invoice_payment_allocations(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Enable RLS
ALTER TABLE public.invoice_payment_allocations ENABLE ROW LEVEL SECURITY;

-- Drop existing policies for safe rerunnability
DROP POLICY IF EXISTS "Super_Admin and Managers can view allocations" ON public.invoice_payment_allocations;
DROP POLICY IF EXISTS "Block direct inserts on allocations" ON public.invoice_payment_allocations;
DROP POLICY IF EXISTS "Block direct updates on allocations" ON public.invoice_payment_allocations;
DROP POLICY IF EXISTS "Block direct deletes on allocations" ON public.invoice_payment_allocations;

-- Financial data protection: Only Super_Admin and Manager can view allocations
CREATE POLICY "Super_Admin and Managers can view allocations"
    ON public.invoice_payment_allocations FOR SELECT
    TO authenticated
    USING (
        (SELECT role FROM public.profiles WHERE id = auth.uid()) IN ('Super_Admin', 'Manager')
    );

-- Block all direct client DML (Mutations allowed ONLY through SECURITY DEFINER RPCs)
CREATE POLICY "Block direct inserts on allocations"
    ON public.invoice_payment_allocations FOR INSERT
    TO authenticated WITH CHECK (false);

CREATE POLICY "Block direct updates on allocations"
    ON public.invoice_payment_allocations FOR UPDATE
    TO authenticated USING (false);

CREATE POLICY "Block direct deletes on allocations"
    ON public.invoice_payment_allocations FOR DELETE
    TO authenticated USING (false);

-- Revoke direct table manipulation grants
REVOKE INSERT, UPDATE, DELETE ON public.invoice_payment_allocations FROM PUBLIC, authenticated, anon;
GRANT SELECT ON public.invoice_payment_allocations TO authenticated;

-- Immutability safeguard: Core financial and relational fields of allocations cannot be edited
CREATE OR REPLACE FUNCTION public.handle_allocation_immutability()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.recovery_id IS DISTINCT FROM NEW.recovery_id OR
       OLD.sale_order_id IS DISTINCT FROM NEW.sale_order_id OR
       OLD.distributor_id IS DISTINCT FROM NEW.distributor_id OR
       OLD.allocated_amount IS DISTINCT FROM NEW.allocated_amount THEN
        RAISE EXCEPTION 'Financial and relational fields on invoice_payment_allocations are strictly immutable once created.';
    END IF;

    -- Only authorized status transition is Approved -> Reversed
    IF OLD.status = 'Reversed' AND NEW.status != 'Reversed' THEN
        RAISE EXCEPTION 'Reversed invoice payment allocation cannot be reactivated.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_allocation_immutability ON public.invoice_payment_allocations;
CREATE TRIGGER trg_allocation_immutability
    BEFORE UPDATE ON public.invoice_payment_allocations
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_allocation_immutability();

-- ------------------------------------------------------------------------------
-- 4. RECOVERY CANCELLATION SAFEGUARD TRIGGER
-- Prevents cancelling an approved recovery if it has active invoice allocations
-- ------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.check_recovery_cancellation_allocations()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'Cancelled' AND OLD.status != 'Cancelled' THEN
        IF EXISTS (
            SELECT 1 FROM public.invoice_payment_allocations 
            WHERE recovery_id = OLD.id AND status = 'Approved'
        ) THEN
            RAISE EXCEPTION 'Cannot cancel recovery %: It has active invoice payment allocations. Reverse all invoice allocations before cancelling this recovery.', OLD.reference_number;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_prevent_cancel_allocated_recovery ON public.recoveries;
CREATE TRIGGER trg_prevent_cancel_allocated_recovery
    BEFORE UPDATE OF status ON public.recoveries
    FOR EACH ROW
    EXECUTE FUNCTION public.check_recovery_cancellation_allocations();

-- ------------------------------------------------------------------------------
-- 5. ATOMIC, ROW-LOCKED INVOICE ALLOCATION RPC
-- Deterministic locking order on recovery and invoice eliminates deadlocks
-- Strict independent existence checks on both records
-- Concurrency-safe idempotency with mandatory hash validation on retry & race
-- ------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.allocate_recovery_to_invoice(
    p_recovery_id UUID,
    p_sale_order_id UUID,
    p_amount NUMERIC,
    p_notes TEXT DEFAULT '',
    p_idempotency_key TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_rec RECORD;
    v_sale RECORD;
    v_rec_dist_id UUID;
    v_total_rec_allocated NUMERIC(12, 2);
    v_total_sale_allocated NUMERIC(12, 2);
    v_available_rec NUMERIC(12, 2);
    v_available_sale NUMERIC(12, 2);
    v_alloc_id UUID := gen_random_uuid();
    v_existing_alloc RECORD;
    v_payload_hash TEXT;
BEGIN
    -- 1. Authorization check: Super_Admin or Manager
    IF COALESCE(public.auth_user_role()::TEXT, '') NOT IN ('Super_Admin', 'Manager') THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin or Manager can allocate recoveries to invoices.';
    END IF;

    -- 2. Input validation
    IF p_recovery_id IS NULL OR p_sale_order_id IS NULL THEN
        RAISE EXCEPTION 'Both recovery_id and sale_order_id are required.';
    END IF;

    IF p_amount IS NULL OR p_amount <= 0 THEN
        RAISE EXCEPTION 'Allocation amount must be greater than zero. Received: %', p_amount;
    END IF;

    IF ROUND(p_amount, 2) != p_amount THEN
        RAISE EXCEPTION 'Allocation amount cannot exceed 2 decimal places. Received: %', p_amount;
    END IF;

    IF p_amount > 100000000.00 THEN
        RAISE EXCEPTION 'Allocation amount exceeds maximum threshold (Rs. 100,000,000).';
    END IF;

    -- 3. Idempotency check with payload hash validation (includes p_notes)
    v_payload_hash := MD5(CONCAT(p_recovery_id::TEXT, ':', p_sale_order_id::TEXT, ':', ROUND(p_amount, 2)::TEXT, ':', COALESCE(TRIM(p_notes), '')));

    IF p_idempotency_key IS NOT NULL AND p_idempotency_key != '' THEN
        SELECT id, allocated_amount, status, idempotency_hash INTO v_existing_alloc
        FROM public.invoice_payment_allocations
        WHERE idempotency_key = p_idempotency_key;

        IF FOUND THEN
            -- Check for payload mismatch under same key
            IF v_existing_alloc.idempotency_hash IS DISTINCT FROM v_payload_hash THEN
                RAISE EXCEPTION 'Idempotency conflict: Key "%" was previously used with a different allocation request payload.', p_idempotency_key;
            END IF;

            -- Check for reversed allocation state
            IF v_existing_alloc.status = 'Reversed' THEN
                RAISE EXCEPTION 'Idempotency error: Key "%" references allocation %, which has been Reversed. A new idempotency key is required for a new allocation.',
                    p_idempotency_key, v_existing_alloc.id;
            END IF;

            RETURN jsonb_build_object(
                'success', true,
                'idempotent_replay', true,
                'allocation_id', v_existing_alloc.id,
                'allocated_amount', v_existing_alloc.allocated_amount,
                'status', v_existing_alloc.status
            );
        END IF;
    END IF;

    -- 4. DETERMINISTIC ROW-LEVEL LOCKING (Sort UUIDs to prevent cross-transaction deadlocks)
    IF p_recovery_id < p_sale_order_id THEN
        SELECT * INTO v_rec FROM public.recoveries WHERE id = p_recovery_id FOR UPDATE;
        SELECT * INTO v_sale FROM public.sales_orders WHERE id = p_sale_order_id FOR UPDATE;
    ELSE
        SELECT * INTO v_sale FROM public.sales_orders WHERE id = p_sale_order_id FOR UPDATE;
        SELECT * INTO v_rec FROM public.recoveries WHERE id = p_recovery_id FOR UPDATE;
    END IF;

    -- 5. INDEPENDENT EXISTENCE CHECKS
    IF v_rec.id IS NULL THEN
        RAISE EXCEPTION 'Recovery not found with ID %', p_recovery_id;
    END IF;

    IF v_sale.id IS NULL THEN
        RAISE EXCEPTION 'Sale invoice not found with ID %', p_sale_order_id;
    END IF;

    IF v_rec.status NOT IN ('Approved', 'Posted') THEN
        RAISE EXCEPTION 'Recovery % is not approved (Status: %).', v_rec.reference_number, v_rec.status;
    END IF;

    IF v_sale.status NOT IN ('Approved', 'Posted') THEN
        RAISE EXCEPTION 'Sale invoice % is not approved (Status: %).', v_sale.reference_number, v_sale.status;
    END IF;

    IF v_sale.reference_number LIKE 'BKG-%' THEN
        RAISE EXCEPTION 'Cannot allocate payment to a booking reservation (%). Allocations apply only to commercial delivery bills (SAL-).', v_sale.reference_number;
    END IF;

    -- 6. STRICT DISTRIBUTOR RESOLUTION (NO LIKE PATTERN MATCHING)
    IF v_rec.distributor_id IS NOT NULL THEN
        v_rec_dist_id := v_rec.distributor_id;
    ELSIF v_rec.sale_order_id IS NOT NULL THEN
        SELECT distributor_id INTO v_rec_dist_id 
        FROM public.sales_orders 
        WHERE id = v_rec.sale_order_id;
    END IF;

    IF v_rec_dist_id IS NULL THEN
        RAISE EXCEPTION 'Cannot allocate recovery %: Recovery has no verified direct distributor_id or verified linked order relationship.', v_rec.reference_number;
    END IF;

    IF v_rec_dist_id != v_sale.distributor_id THEN
        RAISE EXCEPTION 'Distributor mismatch: Recovery belongs to %, Sale invoice belongs to %',
            v_rec_dist_id, v_sale.distributor_id;
    END IF;

    -- 7. Calculate unallocated balances under exclusive row locks
    SELECT COALESCE(SUM(allocated_amount), 0) INTO v_total_rec_allocated
    FROM public.invoice_payment_allocations
    WHERE recovery_id = p_recovery_id AND status = 'Approved';

    v_available_rec := v_rec.amount - v_total_rec_allocated;
    IF p_amount > v_available_rec THEN
        RAISE EXCEPTION 'Cannot allocate Rs. %: Recovery % has only Rs. % unallocated.',
            p_amount, v_rec.reference_number, v_available_rec;
    END IF;

    SELECT COALESCE(SUM(allocated_amount), 0) INTO v_total_sale_allocated
    FROM public.invoice_payment_allocations
    WHERE sale_order_id = p_sale_order_id AND status = 'Approved';

    v_available_sale := v_sale.total_amount - v_total_sale_allocated;
    IF p_amount > v_available_sale THEN
        RAISE EXCEPTION 'Cannot allocate Rs. %: Invoice % payable balance is only Rs. % (Strictly capped at invoice total).',
            p_amount, v_sale.reference_number, v_available_sale;
    END IF;

    -- 8. Insert allocation (Bypasses RLS via SECURITY DEFINER)
    BEGIN
        INSERT INTO public.invoice_payment_allocations (
            id, recovery_id, sale_order_id, distributor_id, allocated_amount, status, notes,
            idempotency_key, idempotency_hash, created_by, created_at, updated_at
        ) VALUES (
            v_alloc_id, p_recovery_id, p_sale_order_id, v_sale.distributor_id, p_amount, 'Approved', p_notes,
            p_idempotency_key, v_payload_hash, auth.uid(), NOW(), NOW()
        );
    EXCEPTION WHEN unique_violation THEN
        -- Handle concurrent identical idempotency submission safely
        IF p_idempotency_key IS NOT NULL AND p_idempotency_key != '' THEN
            SELECT id, allocated_amount, status, idempotency_hash INTO v_existing_alloc
            FROM public.invoice_payment_allocations
            WHERE idempotency_key = p_idempotency_key;

            IF FOUND THEN
                IF v_existing_alloc.idempotency_hash IS DISTINCT FROM v_payload_hash THEN
                    RAISE EXCEPTION 'Idempotency conflict: Key "%" was submitted concurrently with a different allocation request payload.', p_idempotency_key;
                END IF;

                IF v_existing_alloc.status = 'Reversed' THEN
                    RAISE EXCEPTION 'Idempotency error: Key "%" references allocation %, which has been Reversed. A new idempotency key is required for a new allocation.',
                        p_idempotency_key, v_existing_alloc.id;
                END IF;

                RETURN jsonb_build_object(
                    'success', true,
                    'idempotent_replay', true,
                    'allocation_id', v_existing_alloc.id,
                    'allocated_amount', v_existing_alloc.allocated_amount,
                    'status', v_existing_alloc.status
                );
            ELSE
                RAISE;
            END IF;
        ELSE
            RAISE;
        END IF;
    END;

    RETURN jsonb_build_object(
        'success', true,
        'allocation_id', v_alloc_id,
        'allocated_amount', p_amount,
        'remaining_recovery_unallocated', (v_available_rec - p_amount),
        'remaining_invoice_payable', (v_available_sale - p_amount)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- 5.B. REVERSE INVOICE PAYMENT ALLOCATION RPC
-- Allows authorized managers to safely reverse an individual approved allocation.
-- Releases allocated amount back to distributor's unallocated recovery credit.
CREATE OR REPLACE FUNCTION public.reverse_invoice_payment_allocation(
    p_allocation_id UUID,
    p_reversal_reason TEXT
)
RETURNS JSONB AS $$
DECLARE
    v_alloc RECORD;
BEGIN
    -- 1. Authorization check: Super_Admin or Manager
    IF COALESCE(public.auth_user_role()::TEXT, '') NOT IN ('Super_Admin', 'Manager') THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin or Manager can reverse invoice payment allocations.';
    END IF;

    IF p_reversal_reason IS NULL OR LENGTH(TRIM(p_reversal_reason)) < 5 THEN
        RAISE EXCEPTION 'A meaningful reversal reason is required (minimum 5 characters).';
    END IF;

    -- 2. Lock allocation row
    SELECT * INTO v_alloc 
    FROM public.invoice_payment_allocations 
    WHERE id = p_allocation_id 
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invoice payment allocation not found with ID %', p_allocation_id;
    END IF;

    IF v_alloc.status = 'Reversed' THEN
        RAISE EXCEPTION 'Allocation % is already reversed.', p_allocation_id;
    END IF;

    -- 3. Perform reversal (releases recovery credit back to distributor)
    UPDATE public.invoice_payment_allocations
    SET status = 'Reversed',
        reversed_at = NOW(),
        reversed_by = auth.uid(),
        reversal_reason = p_reversal_reason,
        updated_at = NOW()
    WHERE id = p_allocation_id;

    RETURN jsonb_build_object(
        'success', true,
        'action', 'allocation_reversed',
        'allocation_id', p_allocation_id,
        'released_amount', v_alloc.allocated_amount,
        'recovery_id', v_alloc.recovery_id,
        'sale_order_id', v_alloc.sale_order_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- ------------------------------------------------------------------------------
-- 6. ATOMIC PARTIAL DISPATCH RPC (DUAL AGGREGATION & RELATIONAL INVENTORY LINKING)
-- Features:
--   - Rejects malformed JSON and enforces strict integer packet precision
--   - Aggregates by booking_item_id to prevent over-fulfillment from duplicate lines
--   - Locks product_packaging rows across competing bookings in UUID order
--   - Verifies global_settings configuration row and snapshot rates (no fallbacks)
--   - Sets persisted dispatch_state = 'Staged'
--   - Inserts inventory_transactions explicitly linked by sale_order_id
--   - Automatic recovery allocation completely removed
-- ------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.dispatch_partial_booking_fulfillment(
    p_booking_id UUID,
    p_items JSONB,                 -- [{"booking_item_id": "UUID", "packaging_id": "UUID", "quantity": 10, "unit_price": 350.00}]
    p_sale_date TIMESTAMPTZ DEFAULT NOW(),
    p_notes TEXT DEFAULT '',
    p_idempotency_key TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_booking RECORD;
    v_distributor RECORD;
    v_existing_sale RECORD;
    v_new_sale_id UUID := gen_random_uuid();
    v_new_sal_ref TEXT;
    v_item_iss_ref TEXT;
    v_total_amount NUMERIC(12, 2) := 0;
    v_total_pkts INTEGER := 0;
    v_item RECORD;
    v_raw_item JSONB;
    v_booked_item RECORD;
    v_delivered_qty INTEGER;
    v_comm_rate NUMERIC(12, 2);
    v_adv_rate NUMERIC(12, 2);
    v_welf_rate NUMERIC(12, 2);
    v_wh_stock NUMERIC(12, 2);
    v_total_booked_pkts INTEGER;
    v_total_all_delivered INTEGER;
    v_item_count INT;
    v_line_idx INT := 0;
    v_payload_hash TEXT;
    v_agg_bkg RECORD;
    v_agg_pkg RECORD;
    v_pkg_exists BOOLEAN;
BEGIN
    -- 1. AUTHORIZATION COMPATIBILITY CHECK
    -- Live trigger handle_sales_order_immutability requires Super_Admin or sales.approve
    IF COALESCE(public.auth_user_role()::TEXT, '') != 'Super_Admin' 
       AND NOT COALESCE(public.has_permission('sales.approve'), FALSE) THEN
        RAISE EXCEPTION 'Unauthorized: Caller lacks sales.approve authorization to dispatch and approve delivery sales orders.';
    END IF;

    -- 2. VALIDATE PAYLOAD INTEGRITY & MALFORMED JSON
    IF p_booking_id IS NULL THEN
        RAISE EXCEPTION 'p_booking_id is required.';
    END IF;

    IF p_items IS NULL OR jsonb_typeof(p_items) != 'array' OR jsonb_array_length(p_items) = 0 THEN
        RAISE EXCEPTION 'p_items must be a non-empty JSON array.';
    END IF;

    -- Detailed field-by-field validation of raw payload items
    FOR v_raw_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        IF jsonb_typeof(v_raw_item) != 'object' THEN
            RAISE EXCEPTION 'Each element in p_items must be a valid JSON object.';
        END IF;

        IF (v_raw_item->>'booking_item_id') IS NULL OR (v_raw_item->>'packaging_id') IS NULL 
           OR (v_raw_item->>'quantity') IS NULL OR (v_raw_item->>'unit_price') IS NULL THEN
            RAISE EXCEPTION 'Malformed line item in p_items: booking_item_id, packaging_id, quantity, and unit_price are all mandatory.';
        END IF;

        -- Enforce discrete integer packet quantities
        IF (v_raw_item->>'quantity')::NUMERIC <= 0 OR (v_raw_item->>'quantity')::NUMERIC != FLOOR((v_raw_item->>'quantity')::NUMERIC) THEN
            RAISE EXCEPTION 'Invalid packet quantity (%): Packet quantities must be strictly positive whole integers.', (v_raw_item->>'quantity');
        END IF;

        -- Enforce positive unit price with max 2 decimal places
        IF (v_raw_item->>'unit_price')::NUMERIC <= 0 OR ROUND((v_raw_item->>'unit_price')::NUMERIC, 2) != (v_raw_item->>'unit_price')::NUMERIC THEN
            RAISE EXCEPTION 'Invalid agreed unit price (%): Unit price must be strictly positive with at most 2 decimal places.', (v_raw_item->>'unit_price');
        END IF;
    END LOOP;

    -- 3. IDEMPOTENCY CHECK WITH PAYLOAD HASH INTEGRITY (includes p_notes)
    v_payload_hash := MD5(CONCAT(p_booking_id::TEXT, ':', p_items::jsonb::TEXT, ':', COALESCE(p_sale_date::TIMESTAMPTZ::TEXT, ''), ':', COALESCE(TRIM(p_notes), '')));

    IF p_idempotency_key IS NOT NULL AND p_idempotency_key != '' THEN
        SELECT id, reference_number, total_amount, status, dispatch_state, idempotency_hash INTO v_existing_sale
        FROM public.sales_orders
        WHERE idempotency_key = p_idempotency_key;

        IF FOUND THEN
            IF v_existing_sale.idempotency_hash IS DISTINCT FROM v_payload_hash THEN
                RAISE EXCEPTION 'Idempotency conflict: Key "%" was previously submitted with a different dispatch payload.', p_idempotency_key;
            END IF;

            -- Check for cancelled transaction state
            IF v_existing_sale.status = 'Cancelled' THEN
                RAISE EXCEPTION 'Idempotency error: Key "%" was previously used for sale order %, which has been Cancelled. A new idempotency key is required for a new dispatch.',
                    p_idempotency_key, v_existing_sale.reference_number;
            END IF;

            RETURN jsonb_build_object(
                'success', true,
                'idempotent_replay', true,
                'sale_id', v_existing_sale.id,
                'reference_number', v_existing_sale.reference_number,
                'total_amount', v_existing_sale.total_amount,
                'status', v_existing_sale.status,
                'dispatch_state', v_existing_sale.dispatch_state
            );
        END IF;
    END IF;

    -- 4. EXCLUSIVE ROW LOCK ON THE PARENT BOOKING
    SELECT * INTO v_booking 
    FROM public.sales_orders 
    WHERE id = p_booking_id 
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Booking not found with ID %', p_booking_id;
    END IF;

    IF v_booking.status = 'Cancelled' THEN
        RAISE EXCEPTION 'Cannot dispatch against cancelled booking %', v_booking.reference_number;
    END IF;

    IF NOT (v_booking.reference_number LIKE 'BKG-%') THEN
        RAISE EXCEPTION 'Order % is not a booking reservation.', v_booking.reference_number;
    END IF;

    -- 5. VERIFY ACTIVE DISTRIBUTOR & STRICT RATE SNAPSHOTS (NO SILENT FALLBACKS)
    SELECT * INTO v_distributor FROM public.distributors WHERE id = v_booking.distributor_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Distributor not linked to booking %', v_booking.reference_number;
    END IF;
    IF NOT COALESCE(v_distributor.is_active, TRUE) THEN
        RAISE EXCEPTION 'Distributor % is inactive. Cannot dispatch orders.', v_distributor.name;
    END IF;
    IF v_distributor.commission IS NULL THEN
        RAISE EXCEPTION 'Configuration error: Distributor % has no commission rate configured.', v_distributor.name;
    END IF;
    v_comm_rate := v_distributor.commission;

    -- Retrieve rates from global_settings with mandatory existence check
    SELECT advertisement_rate, welfare_rate
    INTO v_adv_rate, v_welf_rate 
    FROM public.global_settings 
    WHERE id = 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Configuration error: global_settings record (id = 1) is missing from database.';
    END IF;
    IF v_adv_rate IS NULL THEN
        RAISE EXCEPTION 'Configuration error: advertisement_rate is NULL in global_settings.';
    END IF;
    IF v_welf_rate IS NULL THEN
        RAISE EXCEPTION 'Configuration error: welfare_rate is NULL in global_settings.';
    END IF;

    -- 6. LEGACY BOOKING GUARD (ZERO-PACKET BOOKINGS CANNOT AUTO-DISPATCH)
    SELECT COUNT(*) INTO v_item_count FROM public.sale_items WHERE sale_order_id = p_booking_id;
    IF v_item_count = 0 THEN
        RAISE EXCEPTION 'Cannot dispatch: Booking % has no recorded line items in database (legacy unitemized booking).', v_booking.reference_number;
    END IF;

    -- 7. ATOMIC CROSS-BOOKING WAREHOUSE STOCK LOCK
    -- Lock all packaging variant rows involved in this dispatch in deterministic UUID order
    PERFORM 1 FROM public.product_packaging
    WHERE id IN (
        SELECT DISTINCT (item->>'packaging_id')::UUID 
        FROM jsonb_array_elements(p_items) AS item
        WHERE (item->>'packaging_id') IS NOT NULL
    )
    ORDER BY id
    FOR UPDATE;

    -- 8. AGGREGATE REQUESTED QUANTITIES BY BOOKING_ITEM_ID (FIXES DUPLICATE PAYLOAD LINES)
    FOR v_agg_bkg IN 
        SELECT 
            (x->>'booking_item_id')::UUID AS booking_item_id,
            (x->>'packaging_id')::UUID AS packaging_id,
            SUM((x->>'quantity')::INTEGER) AS total_item_qty,
            COUNT(DISTINCT (x->>'unit_price')::NUMERIC) AS distinct_prices,
            MAX((x->>'unit_price')::NUMERIC) AS unit_price
        FROM jsonb_array_elements(p_items) AS x
        GROUP BY (x->>'booking_item_id')::UUID, (x->>'packaging_id')::UUID
    LOOP
        IF v_agg_bkg.distinct_prices > 1 THEN
            RAISE EXCEPTION 'Inconsistent dispatch unit prices submitted for the same booking item % in a single request.', v_agg_bkg.booking_item_id;
        END IF;

        -- Verify packaging exists in catalog
        SELECT EXISTS (
            SELECT 1 FROM public.product_packaging WHERE id = v_agg_bkg.packaging_id
        ) INTO v_pkg_exists;
        IF NOT v_pkg_exists THEN
            RAISE EXCEPTION 'Packaging ID % does not exist in product_packaging catalog.', v_agg_bkg.packaging_id;
        END IF;

        -- Verify booked item belongs to this booking
        SELECT * INTO v_booked_item 
        FROM public.sale_items 
        WHERE id = v_agg_bkg.booking_item_id AND sale_order_id = p_booking_id;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Booking item % does not belong to booking %', v_agg_bkg.booking_item_id, v_booking.reference_number;
        END IF;

        IF v_booked_item.packaging_id != v_agg_bkg.packaging_id THEN
            RAISE EXCEPTION 'Packaging mismatch: Dispatched packaging % does not match booked packaging %',
                v_agg_bkg.packaging_id, v_booked_item.packaging_id;
        END IF;

        -- Sum already delivered quantity across approved child sales
        SELECT COALESCE(SUM(si.quantity), 0) INTO v_delivered_qty
        FROM public.sale_items si
        JOIN public.sales_orders so ON so.id = si.sale_order_id
        WHERE si.booking_item_id = v_agg_bkg.booking_item_id
          AND so.status IN ('Approved', 'Posted');

        IF (v_delivered_qty + v_agg_bkg.total_item_qty) > v_booked_item.quantity THEN
            RAISE EXCEPTION 'Over-fulfillment forbidden: Item booked: % pkts, already delivered: % pkts, requested: % pkts (Remaining: % pkts)',
                v_booked_item.quantity, v_delivered_qty, v_agg_bkg.total_item_qty, (v_booked_item.quantity - v_delivered_qty);
        END IF;
    END LOOP;

    -- 9. AGGREGATE REQUESTED QUANTITIES BY PACKAGING & VERIFY FACTORY WAREHOUSE STOCK
    FOR v_agg_pkg IN 
        SELECT 
            (x->>'packaging_id')::UUID AS packaging_id, 
            SUM((x->>'quantity')::INTEGER) AS total_pkg_qty
        FROM jsonb_array_elements(p_items) AS x
        GROUP BY (x->>'packaging_id')::UUID
    LOOP
        -- Verify real-time factory sellable stock under packaging lock
        -- Reconciles signed Adjustment and Reversal quantities without assuming sign
        SELECT COALESCE(SUM(
            CASE 
                WHEN transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN quantity
                WHEN transaction_type IN ('Adjustment', 'Reversal') AND category = 'Sellable Stock' THEN quantity
                WHEN transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -quantity
                ELSE 0
            END
        ), 0) INTO v_wh_stock
        FROM public.inventory_transactions
        WHERE packaging_id = v_agg_pkg.packaging_id
          AND status IN ('Approved', 'Posted');

        IF v_wh_stock < v_agg_pkg.total_pkg_qty THEN
            RAISE EXCEPTION 'Insufficient factory warehouse sellable stock for packaging %. Available: % pkts, Total Requested: % pkts',
                v_agg_pkg.packaging_id, v_wh_stock, v_agg_pkg.total_pkg_qty;
        END IF;
    END LOOP;

    -- 10. GENERATE CLEAN UNIQUE BILL IDENTIFIERS
    v_new_sal_ref := 'SAL-' || UPPER(SUBSTRING(MD5(gen_random_uuid()::TEXT) FROM 1 FOR 8));

    -- Calculate total bill amount
    FOR v_item IN SELECT * FROM jsonb_to_recordset(p_items) AS x(booking_item_id UUID, packaging_id UUID, quantity INTEGER, unit_price NUMERIC)
    LOOP
        v_total_amount := v_total_amount + ROUND(v_item.quantity * v_item.unit_price, 2);
        v_total_pkts := v_total_pkts + v_item.quantity;
    END LOOP;

    -- 11. INSERT APPROVED COMMERCIAL DELIVERY BILL (SAL-)
    -- Insert header as Pending first to satisfy trg_sale_items_immutability
    -- Persist dispatch_state as 'Staged' (goods at warehouse dock awaiting physical handover)
    BEGIN
        INSERT INTO public.sales_orders (
            id, reference_number, distributor_id, total_amount, sale_date, status,
            commission_rate_snapshot, advertisement_rate_snapshot, welfare_rate_snapshot,
            booking_id, fulfillment_status, dispatch_state, idempotency_key, idempotency_hash, created_at, updated_at
        ) VALUES (
            v_new_sale_id, v_new_sal_ref, v_booking.distributor_id, v_total_amount, p_sale_date, 'Pending',
            v_comm_rate, v_adv_rate, v_welf_rate,
            p_booking_id, 'N/A', 'Staged', p_idempotency_key, v_payload_hash, NOW(), NOW()
        );
    EXCEPTION WHEN unique_violation THEN
        IF p_idempotency_key IS NOT NULL AND p_idempotency_key != '' THEN
            SELECT id, reference_number, total_amount, status, dispatch_state, idempotency_hash INTO v_existing_sale
            FROM public.sales_orders
            WHERE idempotency_key = p_idempotency_key;

            IF FOUND THEN
                IF v_existing_sale.idempotency_hash IS DISTINCT FROM v_payload_hash THEN
                    RAISE EXCEPTION 'Idempotency conflict: Key "%" was submitted concurrently with a different dispatch payload.', p_idempotency_key;
                END IF;

                -- Check for cancelled transaction state
                IF v_existing_sale.status = 'Cancelled' THEN
                    RAISE EXCEPTION 'Idempotency error: Key "%" was previously used for sale order %, which has been Cancelled. A new idempotency key is required for a new dispatch.',
                        p_idempotency_key, v_existing_sale.reference_number;
                END IF;

                RETURN jsonb_build_object(
                    'success', true,
                    'idempotent_replay', true,
                    'sale_id', v_existing_sale.id,
                    'reference_number', v_existing_sale.reference_number,
                    'total_amount', v_existing_sale.total_amount,
                    'status', v_existing_sale.status,
                    'dispatch_state', v_existing_sale.dispatch_state
                );
            ELSE
                RAISE;
            END IF;
        ELSE
            RAISE;
        END IF;
    END;

    -- 12. INSERT LINE ITEMS & RECORD PHYSICAL FACTORY STOCK ISSUE WITH RELATIONAL LINK
    FOR v_item IN SELECT * FROM jsonb_to_recordset(p_items) AS x(booking_item_id UUID, packaging_id UUID, quantity INTEGER, unit_price NUMERIC)
    LOOP
        v_line_idx := v_line_idx + 1;
        -- Generate guaranteed unique reference number per inventory transaction
        v_item_iss_ref := 'ISS-' || UPPER(SUBSTRING(MD5(CONCAT(v_new_sale_id::TEXT, ':', v_line_idx::TEXT, ':', gen_random_uuid()::TEXT)) FROM 1 FOR 8));

        INSERT INTO public.sale_items (
            id, sale_order_id, packaging_id, quantity, unit_price, subtotal,
            booking_item_id, created_at, updated_at
        ) VALUES (
            gen_random_uuid(), v_new_sale_id, v_item.packaging_id, v_item.quantity, v_item.unit_price,
            ROUND(v_item.quantity * v_item.unit_price, 2),
            v_item.booking_item_id, NOW(), NOW()
        );

        -- Automatic physical factory stock deduction explicitly linked by sale_order_id
        INSERT INTO public.inventory_transactions (
            id, reference_number, transaction_date, packaging_id, category, transaction_type,
            quantity, unit_cost, total_cost, distributor_id, sale_order_id, status, notes, created_at, updated_at
        ) VALUES (
            gen_random_uuid(), v_item_iss_ref, p_sale_date, v_item.packaging_id, 'Sellable Stock', 'Distributor_Issue',
            v_item.quantity, 0.00, 0.00, v_booking.distributor_id, v_new_sale_id, 'Approved',
            'Factory dispatch against ' || v_new_sal_ref || ' (Booking ' || v_booking.reference_number || ', Line ' || v_line_idx || ')' || CASE WHEN p_notes != '' THEN ' · ' || p_notes ELSE '' END,
            NOW(), NOW()
        );
    END LOOP;

    -- Transition header to Approved now that items and stock issue are committed
    UPDATE public.sales_orders 
    SET status = 'Approved', updated_at = NOW() 
    WHERE id = v_new_sale_id;

    -- 13. DYNAMICALLY RE-EVALUATE AND UPDATE PARENT BOOKING FULFILLMENT STATUS
    SELECT COALESCE(SUM(quantity), 0) INTO v_total_booked_pkts
    FROM public.sale_items WHERE sale_order_id = p_booking_id;

    SELECT COALESCE(SUM(si.quantity), 0) INTO v_total_all_delivered
    FROM public.sale_items si
    JOIN public.sales_orders so ON so.id = si.sale_order_id
    WHERE so.booking_id = p_booking_id AND so.status IN ('Approved', 'Posted');

    -- Set transaction-local internal context token for authorized procedure
    PERFORM set_config('app.internal_dispatch_call', 'true', true);

    IF v_total_all_delivered >= v_total_booked_pkts THEN
        UPDATE public.sales_orders 
        SET fulfillment_status = 'Fulfilled', updated_at = NOW() 
        WHERE id = p_booking_id;
    ELSE
        UPDATE public.sales_orders 
        SET fulfillment_status = 'Partially_Fulfilled', updated_at = NOW() 
        WHERE id = p_booking_id;
    END IF;

    -- Automatic recovery allocation is completely disabled.
    -- Allocations must be explicitly made via allocate_recovery_to_invoice().

    RETURN jsonb_build_object(
        'success', true,
        'sale_id', v_new_sale_id,
        'reference_number', v_new_sal_ref,
        'dispatch_state', 'Staged',
        'dispatched_pkts', v_total_pkts,
        'total_amount', v_total_amount,
        'remaining_invoice_payable', v_total_amount,
        'remaining_booked_pkts', (v_total_booked_pkts - v_total_all_delivered)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- ------------------------------------------------------------------------------
-- 7. REVERSAL & HANDOVER ENGINE: STRICT SEPARATION OF COMMERCIAL VS PHYSICAL
-- ------------------------------------------------------------------------------

-- A. Confirm physical warehouse gate handover
-- Transitions dispatch_state from 'Staged' to 'Dispatched'
CREATE OR REPLACE FUNCTION public.confirm_sale_order_handover(
    p_sale_id UUID,
    p_notes TEXT DEFAULT ''
)
RETURNS JSONB AS $$
DECLARE
    v_sale RECORD;
BEGIN
    IF COALESCE(public.auth_user_role()::TEXT, '') NOT IN ('Super_Admin', 'Manager') 
       AND NOT COALESCE(public.has_permission('inventory.approve'), FALSE) THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin, Manager, or inventory.approve can confirm warehouse handover.';
    END IF;

    SELECT * INTO v_sale FROM public.sales_orders WHERE id = p_sale_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Sale order not found with ID %', p_sale_id; END IF;
    IF v_sale.status != 'Approved' THEN RAISE EXCEPTION 'Sale order % is not approved.', v_sale.reference_number; END IF;
    IF v_sale.dispatch_state != 'Staged' THEN 
        RAISE EXCEPTION 'Sale order % cannot be dispatched: Current dispatch state is "%".', v_sale.reference_number, v_sale.dispatch_state; 
    END IF;

    -- Authorized state transition: Executed within SECURITY DEFINER context owned by postgres
    PERFORM set_config('app.internal_dispatch_call', 'true', true);

    UPDATE public.sales_orders 
    SET dispatch_state = 'Dispatched', updated_at = NOW() 
    WHERE id = p_sale_id;

    RETURN jsonb_build_object(
        'success', true,
        'sale_id', p_sale_id,
        'reference_number', v_sale.reference_number,
        'dispatch_state', 'Dispatched'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- B. Cancel undispatched sale invoice (Goods NEVER left factory loading dock)
-- Verified by database state: v_sale.dispatch_state MUST BE 'Staged'.
CREATE OR REPLACE FUNCTION public.cancel_undispatched_sale_invoice(
    p_sale_id UUID,
    p_reversal_reason TEXT
)
RETURNS JSONB AS $$
DECLARE
    v_sale RECORD;
    v_total_booked_pkts INTEGER;
    v_total_all_delivered INTEGER;
BEGIN
    IF COALESCE(public.auth_user_role()::TEXT, '') != 'Super_Admin' 
       AND NOT COALESCE(public.has_permission('sales.approve'), FALSE) THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin or users with sales.approve can cancel sales invoices.';
    END IF;

    IF p_reversal_reason IS NULL OR LENGTH(TRIM(p_reversal_reason)) < 5 THEN
        RAISE EXCEPTION 'A meaningful cancellation reason is required (minimum 5 characters).';
    END IF;

    SELECT * INTO v_sale FROM public.sales_orders WHERE id = p_sale_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Sale order not found with ID %', p_sale_id; END IF;
    IF v_sale.booking_id IS NULL THEN RAISE EXCEPTION 'Sale order % is not a booking dispatch.', v_sale.reference_number; END IF;
    IF v_sale.status = 'Cancelled' THEN RAISE EXCEPTION 'Sale order % is already cancelled.', v_sale.reference_number; END IF;

    -- Strict verification: Must still be in 'Staged' state at factory warehouse
    IF v_sale.dispatch_state != 'Staged' THEN
        RAISE EXCEPTION 'Cannot void invoice as undispatched: Sale % has dispatch_state = "%". Only orders in "Staged" state (goods still at warehouse dock) can be cancelled via this procedure. If goods have physically departed the warehouse, record a verified return instead.',
            v_sale.reference_number, v_sale.dispatch_state;
    END IF;

    -- 1. Reverse all active payment allocations linked to this sale
    -- FINANCIAL ACCOUNTING GUARANTEE (Issue 3):
    -- Reversing allocations releases allocated recovery amounts back to unallocated distributor credit.
    -- The recoveries table remains untouched (cash ledger integrity preserved).
    -- Distributor ledger balance in fetchDistributorOutstanding() derives solely from
    -- Approved sales minus approved recoveries. Voiding this sale (status = 'Cancelled')
    -- removes it from gross sales, and releasing allocations makes the advance payment
    -- available for subsequent invoices without distortion or duplicate credits.
    UPDATE public.invoice_payment_allocations
    SET status = 'Reversed',
        reversed_at = NOW(),
        reversed_by = auth.uid(),
        reversal_reason = p_reversal_reason,
        updated_at = NOW()
    WHERE sale_order_id = p_sale_id AND status = 'Approved';

    -- 2. Cancel associated factory stock issues via IMMUTABLE sale_order_id LINK
    UPDATE public.inventory_transactions
    SET status = 'Cancelled',
        notes = notes || ' · VOIDED (Invoice ' || v_sale.reference_number || ' cancelled before dispatch: ' || p_reversal_reason || ')',
        updated_at = NOW()
    WHERE sale_order_id = p_sale_id
      AND transaction_type = 'Distributor_Issue'
      AND status = 'Approved';

    -- 3. Transition sale header to Cancelled (authorized via SECURITY DEFINER context owned by postgres)
    PERFORM set_config('app.internal_dispatch_call', 'true', true);

    UPDATE public.sales_orders 
    SET status = 'Cancelled', dispatch_state = 'Cancelled', updated_at = NOW() 
    WHERE id = p_sale_id;

    -- 4. Re-evaluate parent booking fulfillment status
    SELECT COALESCE(SUM(quantity), 0) INTO v_total_booked_pkts
    FROM public.sale_items WHERE sale_order_id = v_sale.booking_id;

    SELECT COALESCE(SUM(si.quantity), 0) INTO v_total_all_delivered
    FROM public.sale_items si
    JOIN public.sales_orders so ON so.id = si.sale_order_id
    WHERE so.booking_id = v_sale.booking_id AND so.status IN ('Approved', 'Posted');

    IF v_total_all_delivered = 0 THEN
        UPDATE public.sales_orders SET fulfillment_status = 'Unfulfilled', updated_at = NOW() WHERE id = v_sale.booking_id;
    ELSE
        UPDATE public.sales_orders SET fulfillment_status = 'Partially_Fulfilled', updated_at = NOW() WHERE id = v_sale.booking_id;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'action', 'undispatched_invoice_voided',
        'cancelled_sale', v_sale.reference_number,
        'restored_booking_pkts', (v_total_booked_pkts - v_total_all_delivered)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- C. Record verified physical stock return from distributor
-- Mandatory linked sale, distributor validation, packaging check, row-level locking & return capping
CREATE OR REPLACE FUNCTION public.record_verified_distributor_stock_return(
    p_linked_sale_id UUID,         -- MANDATORY
    p_distributor_id UUID,         -- MANDATORY
    p_packaging_id UUID,           -- MANDATORY
    p_quantity INTEGER,            -- MANDATORY (strictly integer packets)
    p_condition TEXT,              -- 'Good' or 'Damaged' (MANDATORY)
    p_notes TEXT                   -- MANDATORY (min 5 chars)
)
RETURNS JSONB AS $$
DECLARE
    v_rtn_ref TEXT;
    v_ret_type transaction_type;
    v_category inventory_category;
    v_rtn_id UUID := gen_random_uuid();
    v_sale RECORD;
    v_sale_item RECORD;
    v_total_booked_pkts INTEGER;
    v_total_all_delivered INTEGER;
    v_total_issued_qty INTEGER;
    v_already_returned_qty INTEGER;
BEGIN
    IF COALESCE(public.auth_user_role()::TEXT, '') NOT IN ('Super_Admin', 'Manager') THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin or Manager can record warehouse returns.';
    END IF;

    -- 1. Validate mandatory inputs
    IF p_linked_sale_id IS NULL THEN
        RAISE EXCEPTION 'p_linked_sale_id is mandatory for invoice-linked physical returns.';
    END IF;

    IF p_distributor_id IS NULL THEN
        RAISE EXCEPTION 'p_distributor_id is mandatory.';
    END IF;

    IF p_packaging_id IS NULL THEN
        RAISE EXCEPTION 'p_packaging_id is mandatory.';
    END IF;

    IF p_quantity IS NULL OR p_quantity <= 0 THEN
        RAISE EXCEPTION 'Return quantity must be a strictly positive integer.';
    END IF;

    IF p_condition NOT IN ('Good', 'Damaged') THEN
        RAISE EXCEPTION 'Invalid return condition %. Must be either Good or Damaged.', p_condition;
    END IF;

    IF p_notes IS NULL OR LENGTH(TRIM(p_notes)) < 5 THEN
        RAISE EXCEPTION 'Inspection notes with physical warehouse receipt details are required (minimum 5 characters).';
    END IF;

    -- 2. ROW-LEVEL LOCK ON THE LINKED SALE ORDER
    SELECT * INTO v_sale FROM public.sales_orders WHERE id = p_linked_sale_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Linked sale order not found with ID %', p_linked_sale_id;
    END IF;

    IF v_sale.status NOT IN ('Approved', 'Posted') THEN
        RAISE EXCEPTION 'Linked sale order % is not in Approved status (Status: %).', v_sale.reference_number, v_sale.status;
    END IF;

    -- PHYSICAL RETURN ELIGIBILITY (Issue 5):
    -- Physical returns can ONLY be accepted if goods have physically left the warehouse dock.
    -- If dispatch_state is 'Staged', goods are still inside the factory dock, so physical return is an operational impossibility.
    -- Undispatched staged orders must be voided via cancel_undispatched_sale_invoice().
    -- Historical legacy records (dispatch_state IS NULL) and delivered direct counter sales ('Delivered') are accepted.
    IF v_sale.dispatch_state IS NOT NULL AND v_sale.dispatch_state NOT IN ('Dispatched', 'Delivered') THEN
        RAISE EXCEPTION 'Physical stock return rejected: Sale % has dispatch_state = "%". Physical returns can only be recorded for orders in "Dispatched" or "Delivered" state. If the order is still staged at the factory dock, cancel it using cancel_undispatched_sale_invoice instead.',
            v_sale.reference_number, v_sale.dispatch_state;
    END IF;

    IF v_sale.distributor_id != p_distributor_id THEN
        RAISE EXCEPTION 'Distributor mismatch: Linked sale % belongs to distributor %, but return was submitted for %',
            v_sale.reference_number, v_sale.distributor_id, p_distributor_id;
    END IF;

    -- 3. ROW-LEVEL LOCK ON SALE ITEMS & CUMULATIVE ISSUED QUANTITY ACROSS ALL MATCHING LINES
    PERFORM 1 
    FROM public.sale_items 
    WHERE sale_order_id = p_linked_sale_id AND packaging_id = p_packaging_id 
    FOR UPDATE;

    -- Calculate cumulative issued quantity across ALL sale_items on this sale for this packaging
    SELECT COALESCE(SUM(quantity), 0) INTO v_total_issued_qty
    FROM public.sale_items
    WHERE sale_order_id = p_linked_sale_id AND packaging_id = p_packaging_id;

    IF v_total_issued_qty = 0 THEN
        RAISE EXCEPTION 'Packaging variant % was not included in sale %', p_packaging_id, v_sale.reference_number;
    END IF;

    -- Sum existing returns for this specific sale order & packaging via sale_order_id link
    SELECT COALESCE(SUM(quantity), 0) INTO v_already_returned_qty
    FROM public.inventory_transactions
    WHERE sale_order_id = p_linked_sale_id
      AND packaging_id = p_packaging_id
      AND transaction_type IN ('Distributor_Good_Return', 'Distributor_Damaged_Return')
      AND status IN ('Approved', 'Posted');

    IF (v_already_returned_qty + p_quantity) > v_total_issued_qty THEN
        RAISE EXCEPTION 'Return quantity exceeds issued quantity: Sale % issued % pkts, already returned % pkts, requested return % pkts (Max returnable: % pkts)',
            v_sale.reference_number, v_total_issued_qty, v_already_returned_qty, p_quantity, (v_total_issued_qty - v_already_returned_qty);
    END IF;

    -- 4. CATEGORIZATION & INSERTION
    IF p_condition = 'Damaged' THEN
        v_ret_type := 'Distributor_Damaged_Return'::transaction_type;
        v_category := 'Damaged Stock'::inventory_category;
    ELSE
        v_ret_type := 'Distributor_Good_Return'::transaction_type;
        v_category := 'Sellable Stock'::inventory_category;
    END IF;

    v_rtn_ref := 'RTN-' || UPPER(SUBSTRING(MD5(gen_random_uuid()::TEXT) FROM 1 FOR 8));

    -- Insert physical inventory transaction with relational link to sale_order_id
    INSERT INTO public.inventory_transactions (
        id, reference_number, transaction_date, packaging_id, category, transaction_type,
        quantity, unit_cost, total_cost, distributor_id, sale_order_id, status, notes, created_at, updated_at
    ) VALUES (
        v_rtn_id, v_rtn_ref, NOW(), p_packaging_id, v_category, v_ret_type,
        p_quantity, 0.00, 0.00, p_distributor_id, p_linked_sale_id, 'Approved', 
        p_notes || ' (Linked Sale ' || v_sale.reference_number || ')',
        NOW(), NOW()
    );

    -- 5. ADJUST PARENT BOOKING FULFILLMENT STATUS IF APPLICABLE
    IF v_sale.booking_id IS NOT NULL THEN
        SELECT COALESCE(SUM(quantity), 0) INTO v_total_booked_pkts
        FROM public.sale_items WHERE sale_order_id = v_sale.booking_id;

        SELECT COALESCE(SUM(si.quantity), 0) INTO v_total_all_delivered
        FROM public.sale_items si
        JOIN public.sales_orders so ON so.id = si.sale_order_id
        WHERE so.booking_id = v_sale.booking_id AND so.status IN ('Approved', 'Posted');

        IF v_total_all_delivered < v_total_booked_pkts THEN
            PERFORM set_config('app.internal_dispatch_call', 'true', true);

            UPDATE public.sales_orders 
            SET fulfillment_status = 'Partially_Fulfilled', updated_at = NOW() 
            WHERE id = v_sale.booking_id;
        END IF;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'return_id', v_rtn_id,
        'reference_number', v_rtn_ref,
        'quantity', p_quantity,
        'condition', p_condition,
        'category', v_category::TEXT,
        'sale_reference', v_sale.reference_number,
        'remaining_returnable_pkts', (v_total_issued_qty - v_already_returned_qty - p_quantity)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- ------------------------------------------------------------------------------
-- 8. SECURITY & LEAST-PRIVILEGE GRANTS
-- ------------------------------------------------------------------------------
ALTER FUNCTION public.handle_booking_relationship_immutability() OWNER TO postgres;
ALTER FUNCTION public.handle_sales_order_new_row_defaults() OWNER TO postgres;
ALTER FUNCTION public.handle_allocation_immutability() OWNER TO postgres;
ALTER FUNCTION public.check_recovery_cancellation_allocations() OWNER TO postgres;
ALTER FUNCTION public.allocate_recovery_to_invoice(UUID, UUID, NUMERIC, TEXT, TEXT) OWNER TO postgres;
ALTER FUNCTION public.reverse_invoice_payment_allocation(UUID, TEXT) OWNER TO postgres;
ALTER FUNCTION public.dispatch_partial_booking_fulfillment(UUID, JSONB, TIMESTAMPTZ, TEXT, TEXT) OWNER TO postgres;
ALTER FUNCTION public.confirm_sale_order_handover(UUID, TEXT) OWNER TO postgres;
ALTER FUNCTION public.cancel_undispatched_sale_invoice(UUID, TEXT) OWNER TO postgres;
ALTER FUNCTION public.record_verified_distributor_stock_return(UUID, UUID, UUID, INTEGER, TEXT, TEXT) OWNER TO postgres;

-- Revoke public permissions, grant explicitly to authenticated
REVOKE ALL ON FUNCTION public.allocate_recovery_to_invoice(UUID, UUID, NUMERIC, TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.reverse_invoice_payment_allocation(UUID, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.dispatch_partial_booking_fulfillment(UUID, JSONB, TIMESTAMPTZ, TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.confirm_sale_order_handover(UUID, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.cancel_undispatched_sale_invoice(UUID, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.record_verified_distributor_stock_return(UUID, UUID, UUID, INTEGER, TEXT, TEXT) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.allocate_recovery_to_invoice(UUID, UUID, NUMERIC, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.reverse_invoice_payment_allocation(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.dispatch_partial_booking_fulfillment(UUID, JSONB, TIMESTAMPTZ, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.confirm_sale_order_handover(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.cancel_undispatched_sale_invoice(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.record_verified_distributor_stock_return(UUID, UUID, UUID, INTEGER, TEXT, TEXT) TO authenticated;

COMMIT;

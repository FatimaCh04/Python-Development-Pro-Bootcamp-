-- ======================================================================================
-- ELITE WASH ERP — PERMANENT REMOVAL OF LEGACY CUSTOMER MODULE
-- Migration Script: cleanup_customer_module.sql
--
-- TARGET OBJECTS TO PERMANENTLY REMOVE:
--   1. public.customers (table)
--   2. public.customer_ledger (view)
--   3. customer_id columns from:
--      - public.sales_orders
--      - public.recoveries
--      - public.inventory_transactions
--   4. Associated foreign key constraints:
--      - sales_orders_customer_id_fkey
--      - recoveries_customer_id_fkey
--      - inventory_transactions_customer_id_fkey
--      - customers_default_salesman_id_fkey
--   5. Associated RLS policies on public.customers
--
-- BUSINESS DATA PRESERVATION & MIGRATION RULES:
--   1. Purely atomic transaction wrapped in BEGIN ... COMMIT with rollback on ANY error.
--   2. Explicit dependency management — NO BLIND CASCADE DROPS.
--   3. All 12 sales orders and 8 recoveries belong to legitimate distributors:
--      - Preserves MUHAMMAD NADEEM HUSSAIN (ELITEWASH#01), QAMAR SAJJAD (ELITEWASH#03), khalid (Elitewash#04).
--      - For the 3 historical booking recoveries (REC-MUMLQJZX, REC-MUMLRQP1, REC-MUMYSREE)
--        linked to distributor bookings but having distributor_id IS NULL, migrates their distributor_id
--        from the linked booking so distributor ledger and recovery accounts remain 100% coherent.
--   4. Updates database functions and triggers BEFORE dropping columns to prevent runtime errors:
--      - handle_sales_order_immutability(): removes NEW.customer_id check
--      - handle_recovery_immutability(): removes NEW.customer_id check
--      - handle_distributor_settlement_workflow(): removes customer_id from recovery insert
--      - create_sales_order_with_items(): removes customer_id from sales_orders insert
--   5. Preserves Super Admin, Muhammad saeed, all distributor profiles, and Manufacturer SHOAIB.
--   6. Strict pre-migration and post-migration verification gates abort the transaction if any
--      integrity assertion is violated.
-- ======================================================================================

BEGIN;

DO $CLEANUP_CUSTOMER_BLOCK$
DECLARE
    -- Snapshot Verification Counters
    v_dist_count                INTEGER := 0;
    v_staff_count               INTEGER := 0;
    v_person_count              INTEGER := 0;
    v_orders_count              INTEGER := 0;
    v_recoveries_count          INTEGER := 0;
    v_expenses_count            INTEGER := 0;
    v_cust_table_exists         BOOLEAN := FALSE;
    v_cust_view_exists          BOOLEAN := FALSE;

    -- Migration Counters
    v_recs_backfilled           INTEGER := 0;
    v_post_orders_count         INTEGER := 0;
    v_post_recoveries_count     INTEGER := 0;
    v_post_expenses_count       INTEGER := 0;
    v_post_dist_count           INTEGER := 0;
    v_post_staff_count          INTEGER := 0;
    v_post_person_count         INTEGER := 0;
    v_post_unassigned_recs      INTEGER := 0;
    v_remaining_cust_cols       INTEGER := 0;
BEGIN
    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'STARTING: ELITE WASH ERP CUSTOMER MODULE DEPRECATION MIGRATION';
    RAISE NOTICE '======================================================================';

    -- ------------------------------------------------------------------
    -- STEP 1: PRE-MIGRATION SNAPSHOT & INTEGRITY VERIFICATION GATES
    -- ------------------------------------------------------------------
    -- 1.1 Verify Distributors
    SELECT COUNT(*) INTO v_dist_count
    FROM public.distributors
    WHERE code IN ('ELITEWASH#01', 'ELITEWASH#03', 'Elitewash#04');

    IF v_dist_count < 3 THEN
        RAISE EXCEPTION 'PRE-CHECK FAILED: Expected 3 real distributors, found %. Aborting.', v_dist_count;
    END IF;

    -- 1.2 Verify Staff Profiles
    SELECT COUNT(*) INTO v_staff_count
    FROM public.profiles
    WHERE role IN ('Super_Admin', 'Manager') AND is_active = TRUE;

    IF v_staff_count < 2 THEN
        RAISE EXCEPTION 'PRE-CHECK FAILED: Expected at least 2 active staff profiles, found %. Aborting.', v_staff_count;
    END IF;

    -- 1.3 Verify Manufacturer SHOAIB
    SELECT COUNT(*) INTO v_person_count
    FROM public.persons
    WHERE code = 'ELPRODUCTION#01' AND name = 'SHOAIB';

    IF v_person_count < 1 THEN
        RAISE EXCEPTION 'PRE-CHECK FAILED: Manufacturer SHOAIB (ELPRODUCTION#01) not found. Aborting.';
    END IF;

    -- 1.4 Verify Operational Ledger Record Counts
    SELECT COUNT(*) INTO v_orders_count FROM public.sales_orders;
    SELECT COUNT(*) INTO v_recoveries_count FROM public.recoveries;
    SELECT COUNT(*) INTO v_expenses_count FROM public.expenses;

    IF v_orders_count < 12 THEN
        RAISE EXCEPTION 'PRE-CHECK FAILED: Expected at least 12 sales orders, found %. Aborting.', v_orders_count;
    END IF;

    IF v_recoveries_count < 8 THEN
        RAISE EXCEPTION 'PRE-CHECK FAILED: Expected at least 8 recoveries, found %. Aborting.', v_recoveries_count;
    END IF;

    IF v_expenses_count < 2 THEN
        RAISE EXCEPTION 'PRE-CHECK FAILED: Expected at least 2 approved expenses, found %. Aborting.', v_expenses_count;
    END IF;

    RAISE NOTICE '[PRE-CHECK PASSED] Verified 3 Real Distributors, 2 Staff, 1 Manufacturer, % Orders, % Recoveries, % Expenses.',
        v_orders_count, v_recoveries_count, v_expenses_count;

    -- ------------------------------------------------------------------
    -- STEP 2: PRESERVE & MIGRATE DISTRIBUTOR ASSOCIATIONS ON RECOVERIES
    -- ------------------------------------------------------------------
    -- For recoveries created under booking advances where distributor_id was NULL,
    -- inherit the distributor_id from the linked sales order (booking)
    -- to ensure zero orphaned financial records when customer_id is dropped.
    
    -- Temporarily disable immutability trigger for this authorized data migration
    ALTER TABLE public.recoveries DISABLE TRIGGER trg_recovery_immutability;

    UPDATE public.recoveries r
    SET distributor_id = so.distributor_id,
        updated_at = NOW()
    FROM public.sales_orders so
    WHERE r.distributor_id IS NULL
      AND r.sale_order_id = so.id
      AND so.distributor_id IS NOT NULL;

    GET DIAGNOSTICS v_recs_backfilled = ROW_COUNT;
    RAISE NOTICE '[STEP 2] Migrated % historical recoveries to their linked distributor accounts.', v_recs_backfilled;

    ALTER TABLE public.recoveries ENABLE TRIGGER trg_recovery_immutability;

    -- ------------------------------------------------------------------
    -- STEP 3: DROP DEPENDENT VIEWS EXPLICITLY (NO CASCADE)
    -- ------------------------------------------------------------------
    RAISE NOTICE '[STEP 3] Dropping public.customer_ledger view...';
    DROP VIEW IF EXISTS public.customer_ledger;
    DROP MATERIALIZED VIEW IF EXISTS public.customer_ledger;

    -- ------------------------------------------------------------------
    -- STEP 4: UPDATE TRIGGERS & RPC FUNCTIONS BEFORE DROPPING COLUMNS
    -- ------------------------------------------------------------------
    RAISE NOTICE '[STEP 4] Updating functions and triggers to remove customer_id references...';

    -- 4.1 Update handle_sales_order_immutability()
    CREATE OR REPLACE FUNCTION public.handle_sales_order_immutability()
    RETURNS TRIGGER AS $FN$
    DECLARE
        v_caller_role TEXT;
        v_has_approve_perm BOOLEAN;
        v_is_reconciling BOOLEAN := FALSE;
    BEGIN
        v_caller_role := COALESCE(public.auth_user_role()::TEXT, '');
        v_has_approve_perm := (v_caller_role = 'Super_Admin') OR COALESCE(public.has_permission('sales.approve'), FALSE);

        -- SAFE INSERT HANDLING
        IF TG_OP = 'INSERT' THEN
            IF NEW.status IN ('Approved', 'Posted') THEN
                IF NOT v_has_approve_perm THEN
                    RAISE EXCEPTION 'Unauthorized: Only Super_Admin or users with sales.approve permission can create approved sales orders.';
                END IF;
            END IF;
            RETURN NEW;
        END IF;

        -- SAFE UPDATE HANDLING
        IF TG_OP = 'UPDATE' THEN
            -- 1. Prevent reactivation of Cancelled sales orders
            IF OLD.status = 'Cancelled' AND NEW.status != 'Cancelled' THEN
                RAISE EXCEPTION 'Sales order % is Cancelled and cannot be approved or reactivated.', OLD.reference_number;
            END IF;

            -- 2. Gated transition to Approved/Posted
            IF NEW.status IN ('Approved', 'Posted') AND OLD.status NOT IN ('Approved', 'Posted') THEN
                IF NOT v_has_approve_perm THEN
                    RAISE EXCEPTION 'Unauthorized: Only Super_Admin or users with sales.approve permission can approve sales orders.';
                END IF;
            END IF;

            -- 3. Gated transition from Approved/Posted to Cancelled
            IF NEW.status = 'Cancelled' AND OLD.status IN ('Approved', 'Posted') THEN
                IF NOT v_has_approve_perm THEN
                    RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized users with sales.approve can cancel approved sales.';
                END IF;
            END IF;

            -- 4. If already Approved/Posted: enforce strict immutability of core fields
            IF OLD.status IN ('Approved', 'Posted') THEN
                -- Allow Super_Admin to reconcile historical sales orders that currently have NULL snapshot
                IF OLD.commission_rate_snapshot IS NULL AND NEW.commission_rate_snapshot IS NOT NULL THEN
                    IF v_caller_role = 'Super_Admin' THEN
                        v_is_reconciling := TRUE;
                    ELSE
                        RAISE EXCEPTION 'Unauthorized: Only Super_Admin can reconcile historical sales order rates.';
                    END IF;
                END IF;

                -- Core financial and relational fields are strictly immutable (customer_id safely removed)
                IF (
                    NEW.reference_number IS DISTINCT FROM OLD.reference_number OR
                    NEW.sale_date IS DISTINCT FROM OLD.sale_date OR
                    NEW.distributor_id IS DISTINCT FROM OLD.distributor_id OR
                    NEW.salesman_id IS DISTINCT FROM OLD.salesman_id OR
                    NEW.total_amount IS DISTINCT FROM OLD.total_amount
                ) THEN
                    RAISE EXCEPTION 'Approved sales orders are strictly immutable. Financial and relational fields cannot be modified.';
                END IF;

                -- Snapshot rate fields: immutable unless explicitly reconciling a NULL snapshot
                IF NOT v_is_reconciling THEN
                    IF (
                        NEW.commission_rate_snapshot IS DISTINCT FROM OLD.commission_rate_snapshot OR
                        NEW.advertisement_rate_snapshot IS DISTINCT FROM OLD.advertisement_rate_snapshot OR
                        NEW.welfare_rate_snapshot IS DISTINCT FROM OLD.welfare_rate_snapshot
                    ) THEN
                        RAISE EXCEPTION 'Approved sales order rate snapshots are strictly immutable and cannot be altered.';
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END IF;

        RETURN NEW;
    END;
    $FN$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

    -- 4.2 Update handle_recovery_immutability()
    CREATE OR REPLACE FUNCTION public.handle_recovery_immutability()
    RETURNS TRIGGER AS $FN$
    DECLARE
        v_caller_role TEXT;
        v_has_approve_perm BOOLEAN;
    BEGIN
        v_caller_role := COALESCE(public.auth_user_role()::TEXT, '');
        v_has_approve_perm := (v_caller_role = 'Super_Admin') OR 
                              COALESCE(public.has_permission('sales.approve'), FALSE) OR 
                              COALESCE(public.has_permission('settlement.approve'), FALSE);

        -- Protect commission adjustment recoveries from direct manipulation
        IF OLD.payment_method = 'Adjustment' AND pg_trigger_depth() <= 1 THEN
            IF NEW.status IS DISTINCT FROM OLD.status OR NEW.amount IS DISTINCT FROM OLD.amount THEN
                RAISE EXCEPTION 'Commission adjustment recoveries cannot be modified or cancelled directly. Modify or cancel the originating distributor settlement.';
            END IF;
        END IF;

        IF OLD.status IN ('Approved', 'Posted') THEN
            -- Core financial and relational fields are strictly immutable (customer_id safely removed)
            IF (
                NEW.reference_number IS DISTINCT FROM OLD.reference_number OR
                NEW.recovery_date IS DISTINCT FROM OLD.recovery_date OR
                NEW.distributor_id IS DISTINCT FROM OLD.distributor_id OR
                NEW.salesman_id IS DISTINCT FROM OLD.salesman_id OR
                NEW.amount IS DISTINCT FROM OLD.amount OR
                NEW.payment_method IS DISTINCT FROM OLD.payment_method
            ) THEN
                RAISE EXCEPTION 'Approved recoveries are strictly immutable. Financial fields cannot be modified.';
            END IF;

            IF NEW.status = 'Cancelled' AND OLD.status != 'Cancelled' THEN
                IF NOT v_has_approve_perm THEN
                    RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized users can cancel approved recoveries.';
                END IF;
            END IF;
        END IF;
        RETURN NEW;
    END;
    $FN$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

    -- 4.3 Update handle_distributor_settlement_workflow()
    CREATE OR REPLACE FUNCTION public.handle_distributor_settlement_workflow()
    RETURNS TRIGGER AS $FN$
    DECLARE
        v_caller_role TEXT;
        v_has_approve_perm BOOLEAN;
        v_rec_id UUID;
        v_rec_ref TEXT;
        v_accrued_comm NUMERIC(12, 2) := 0;
        v_paid_comm NUMERIC(12, 2) := 0;
        v_avail_comm NUMERIC(12, 2) := 0;
        v_total_sales NUMERIC(12, 2) := 0;
        v_total_recov NUMERIC(12, 2) := 0;
        v_avail_out NUMERIC(12, 2) := 0;
        v_unreconciled_count INT := 0;
    BEGIN
        v_caller_role := COALESCE(public.auth_user_role()::TEXT, '');
        v_has_approve_perm := (v_caller_role = 'Super_Admin') OR COALESCE(public.has_permission('settlement.approve'), FALSE);

        -- SAFE INSERT HANDLING: All settlements MUST start as Pending
        IF TG_OP = 'INSERT' THEN
            IF NEW.status = 'Approved' THEN
                RAISE EXCEPTION 'Direct insertion with Approved status is prohibited. Settlements must be created as Pending and approved via approve_distributor_settlement.';
            END IF;
            NEW.status := 'Pending';
            NEW.recovery_id := NULL;
            RETURN NEW;
        END IF;

        -- SAFE UPDATE HANDLING
        IF TG_OP = 'UPDATE' THEN
            -- If already Approved: enforce immutability of financial, relational, and audit fields
            IF OLD.status = 'Approved' THEN
                IF (
                    NEW.distributor_id IS DISTINCT FROM OLD.distributor_id OR
                    NEW.amount IS DISTINCT FROM OLD.amount OR
                    NEW.settlement_type IS DISTINCT FROM OLD.settlement_type OR
                    NEW.settlement_date IS DISTINCT FROM OLD.settlement_date OR
                    NEW.payment_method IS DISTINCT FROM OLD.payment_method OR
                    NEW.account_detail IS DISTINCT FROM OLD.account_detail OR
                    NEW.tid IS DISTINCT FROM OLD.tid OR
                    NEW.recovery_id IS DISTINCT FROM OLD.recovery_id OR
                    NEW.created_by IS DISTINCT FROM OLD.created_by OR
                    NEW.created_at IS DISTINCT FROM OLD.created_at OR
                    NEW.approved_by IS DISTINCT FROM OLD.approved_by OR
                    NEW.approved_at IS DISTINCT FROM OLD.approved_at
                ) THEN
                    RAISE EXCEPTION 'Approved settlements are strictly immutable. Financial and linking fields cannot be modified even when cancelling.';
                END IF;
            END IF;

            -- Prevent re-approval of Cancelled settlements
            IF OLD.status = 'Cancelled' AND NEW.status != 'Cancelled' THEN
                RAISE EXCEPTION 'Settlement % is already Cancelled and cannot be approved or reactivated.', OLD.reference_number;
            END IF;

            -- Transition from Pending to Approved
            IF NEW.status = 'Approved' AND OLD.status != 'Approved' THEN
                IF NOT v_has_approve_perm THEN
                    RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized Managers with settlement.approve permission can approve settlements.';
                END IF;

                NEW.approved_at := COALESCE(NEW.approved_at, NOW());
                NEW.approved_by := COALESCE(NEW.approved_by, auth.uid());

                -- Row lock distributor to prevent race conditions during concurrent approvals
                PERFORM id FROM public.distributors WHERE id = NEW.distributor_id FOR UPDATE;

                -- Check for historical sales orders with unverified NULL snapshots
                SELECT COUNT(*) INTO v_unreconciled_count
                FROM public.sales_orders so
                WHERE so.distributor_id = NEW.distributor_id 
                  AND so.status IN ('Approved', 'Posted')
                  AND so.commission_rate_snapshot IS NULL;

                IF v_unreconciled_count > 0 THEN
                    RAISE EXCEPTION 'Cannot approve settlement: Distributor has % historical sales orders with unverified commission rates (NULL snapshot). Reconcile historical orders using reconcile_historical_sales_order_rates() before approving settlements.', v_unreconciled_count;
                END IF;

                -- Accrued commission from order snapshots
                SELECT COALESCE(SUM(si.quantity * so.commission_rate_snapshot), 0)
                INTO v_accrued_comm
                FROM public.sale_items si
                JOIN public.sales_orders so ON so.id = si.sale_order_id
                WHERE so.distributor_id = NEW.distributor_id AND so.status IN ('Approved', 'Posted');

                -- Settled commission already approved (excluding this settlement)
                SELECT COALESCE(SUM(amount), 0) INTO v_paid_comm
                FROM public.distributor_settlements
                WHERE distributor_id = NEW.distributor_id AND status = 'Approved' AND id != OLD.id;

                v_avail_comm := GREATEST(0, v_accrued_comm - v_paid_comm);

                IF NEW.amount > v_avail_comm THEN
                    RAISE EXCEPTION 'Settlement amount (Rs. %) exceeds available Commission Payable (Rs. %). Accrued based on order snapshots: Rs. %, Paid: Rs. %',
                        NEW.amount, v_avail_comm, v_accrued_comm, v_paid_comm;
                END IF;

                -- If Commission_Against_Outstanding: verify Sales Outstanding and create linked recovery atomically
                IF NEW.settlement_type = 'Commission_Against_Outstanding' THEN
                    SELECT COALESCE(SUM(total_amount), 0) INTO v_total_sales
                    FROM public.sales_orders
                    WHERE distributor_id = NEW.distributor_id AND status IN ('Approved', 'Posted');

                    SELECT COALESCE(SUM(amount), 0) INTO v_total_recov
                    FROM public.recoveries
                    WHERE distributor_id = NEW.distributor_id 
                      AND status IN ('Approved', 'Posted')
                      AND (reference_number NOT LIKE '%|BKG-%' OR reference_number IS NULL);

                    v_avail_out := GREATEST(0, v_total_sales - v_total_recov);

                    IF NEW.amount > v_avail_out THEN
                        RAISE EXCEPTION 'Offset amount (Rs. %) exceeds available Sales Outstanding (Rs. %). Total Sales: Rs. %, Total Recovered: Rs. %',
                            NEW.amount, v_avail_out, v_total_sales, v_total_recov;
                    END IF;

                    -- Atomic creation of linked recovery (customer_id omitted)
                    IF NEW.recovery_id IS NULL THEN
                        v_rec_ref := 'REC-SET-' || SUBSTRING(REPLACE(NEW.reference_number, '-', ''), 1, 10) || '-' || SUBSTRING(OLD.id::TEXT, 1, 6);

                        INSERT INTO public.recoveries (
                            reference_number,
                            recovery_date,
                            distributor_id,
                            salesman_id,
                            amount,
                            payment_method,
                            status,
                            notes,
                            created_at,
                            updated_at
                        ) VALUES (
                            v_rec_ref,
                            NEW.settlement_date,
                            NEW.distributor_id,
                            NULL,
                            NEW.amount,
                            'Adjustment',
                            'Approved',
                            'Automated offset from Commission Against Outstanding: ' || NEW.reference_number,
                            NOW(),
                            NOW()
                        ) RETURNING id INTO v_rec_id;

                        NEW.recovery_id := v_rec_id;
                    END IF;
                END IF;
            END IF;

            -- Transition from Approved to Cancelled: Reverse linked recovery with strict ownership
            IF NEW.status = 'Cancelled' AND OLD.status = 'Approved' THEN
                IF NOT v_has_approve_perm THEN
                    RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized Managers with settlement.approve permission can cancel approved settlements.';
                END IF;

                IF NEW.recovery_id IS NOT NULL THEN
                    UPDATE public.recoveries
                    SET status = 'Cancelled', notes = COALESCE(notes, '') || ' [Settlement Cancelled: ' || NEW.reference_number || ']'
                    WHERE id = NEW.recovery_id 
                      AND distributor_id = NEW.distributor_id 
                      AND payment_method = 'Adjustment'
                      AND status != 'Cancelled';
                END IF;
            END IF;

            RETURN NEW;
        END IF;

        RETURN NEW;
    END;
    $FN$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

    -- 4.4 Update create_sales_order_with_items()
    -- Parameter p_customer_id is retained as DEFAULT NULL for backward API signature compatibility,
    -- but customer_id is no longer inserted into public.sales_orders.
    CREATE OR REPLACE FUNCTION public.create_sales_order_with_items(
        p_reference_number TEXT,
        p_distributor_id UUID DEFAULT NULL,
        p_salesman_id UUID DEFAULT NULL,
        p_customer_id UUID DEFAULT NULL,
        p_total_amount NUMERIC DEFAULT 0,
        p_sale_date TIMESTAMPTZ DEFAULT NOW(),
        p_status TEXT DEFAULT 'Approved',
        p_items JSONB DEFAULT '[]'::JSONB
    )
    RETURNS JSONB AS $FN$
    DECLARE
        v_order_id UUID := gen_random_uuid();
        v_comm_rate NUMERIC(12, 2) := 30.00;
        v_adv_rate NUMERIC(12, 2) := 20.00;
        v_welf_rate NUMERIC(12, 2) := 10.00;
        v_item JSONB;
        v_pkg_id UUID;
        v_qty NUMERIC(12, 2);
        v_unit_price NUMERIC(12, 2);
        v_subtotal NUMERIC(12, 2);
        v_computed_total NUMERIC(12, 2) := 0;
        v_distributor RECORD;
    BEGIN
        -- 1. Validate Items Payload
        IF p_items IS NULL OR jsonb_array_length(p_items) = 0 THEN
            RAISE EXCEPTION 'At least one sale item is required.';
        END IF;

        -- 2. Validate Distributor if provided & fetch configured commission
        IF p_distributor_id IS NOT NULL THEN
            SELECT * INTO v_distributor FROM public.distributors WHERE id = p_distributor_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Distributor not found with ID %', p_distributor_id;
            END IF;
            IF NOT COALESCE(v_distributor.is_active, TRUE) THEN
                RAISE EXCEPTION 'Distributor % is inactive. Sales cannot be recorded for inactive distributors.', v_distributor.name;
            END IF;
            v_comm_rate := COALESCE(v_distributor.commission, 30.00);
        END IF;

        -- 3. Check Approval Authorization
        IF p_status IN ('Approved', 'Posted') THEN
            IF COALESCE(public.auth_user_role()::TEXT, '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('sales.approve'), FALSE) THEN
                RAISE EXCEPTION 'Unauthorized: Only Super_Admin or users with sales.approve permission can create approved sales orders.';
            END IF;
        ELSE
            IF COALESCE(public.auth_user_role()::TEXT, '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('sales.create'), FALSE) THEN
                RAISE EXCEPTION 'Unauthorized: Caller lacks sales.create permission.';
            END IF;
        END IF;

        -- 4. Rates from global_settings with fallbacks
        SELECT 
            COALESCE(advertisement_rate, 20.00),
            COALESCE(welfare_rate, 10.00)
        INTO v_adv_rate, v_welf_rate
        FROM public.global_settings WHERE id = 1;

        v_adv_rate := COALESCE(v_adv_rate, 20.00);
        v_welf_rate := COALESCE(v_welf_rate, 10.00);

        -- 5. Pre-validate Line Items & Compute Total
        FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
            v_pkg_id := COALESCE((v_item->>'packagingId')::UUID, (v_item->>'packaging_id')::UUID);
            IF v_pkg_id IS NULL THEN
                RAISE EXCEPTION 'Each item must have a valid packagingId.';
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM public.product_packaging WHERE id = v_pkg_id) THEN
                RAISE EXCEPTION 'Packaging ID % not found in product catalog.', v_pkg_id;
            END IF;

            v_qty := (v_item->>'quantity')::NUMERIC;
            IF v_qty IS NULL OR v_qty <= 0 THEN
                RAISE EXCEPTION 'Item quantity must be greater than zero. Received: %', v_qty;
            END IF;

            v_unit_price := COALESCE((v_item->>'price')::NUMERIC, (v_item->>'unit_price')::NUMERIC);
            IF v_unit_price IS NULL OR v_unit_price <= 0 THEN
                RAISE EXCEPTION 'Item unit price must be greater than zero. Received: %', v_unit_price;
            END IF;

            v_subtotal := ROUND(v_qty * v_unit_price, 2);

            IF v_item ? 'subtotal' AND (v_item->>'subtotal') IS NOT NULL THEN
                IF ROUND((v_item->>'subtotal')::NUMERIC, 2) != v_subtotal THEN
                    RAISE EXCEPTION 'Item subtotal mismatch: client sent % but % * % = %', (v_item->>'subtotal')::NUMERIC, v_qty, v_unit_price, v_subtotal;
                END IF;
            END IF;

            v_computed_total := v_computed_total + v_subtotal;
        END LOOP;

        -- Validate Total Amount
        IF p_total_amount IS NOT NULL AND p_total_amount > 0 THEN
            IF ROUND(p_total_amount, 2) != ROUND(v_computed_total, 2) THEN
                RAISE EXCEPTION 'Order total amount (Rs. %) does not match sum of item subtotals (Rs. %)', p_total_amount, v_computed_total;
            END IF;
        END IF;

        -- 6. Insert Order Header as 'Pending' first (customer_id safely omitted)
        INSERT INTO public.sales_orders (
            id,
            reference_number,
            distributor_id,
            salesman_id,
            total_amount,
            sale_date,
            status,
            commission_rate_snapshot,
            advertisement_rate_snapshot,
            welfare_rate_snapshot,
            created_at,
            updated_at
        ) VALUES (
            v_order_id,
            p_reference_number,
            p_distributor_id,
            p_salesman_id,
            v_computed_total,
            COALESCE(p_sale_date, NOW()),
            'Pending'::transaction_status,
            v_comm_rate,
            v_adv_rate,
            v_welf_rate,
            NOW(),
            NOW()
        );

        -- 7. Insert Line Items while order is Pending
        FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
            v_pkg_id := COALESCE((v_item->>'packagingId')::UUID, (v_item->>'packaging_id')::UUID);
            v_qty := (v_item->>'quantity')::NUMERIC;
            v_unit_price := COALESCE((v_item->>'price')::NUMERIC, (v_item->>'unit_price')::NUMERIC);
            v_subtotal := ROUND(v_qty * v_unit_price, 2);

            INSERT INTO public.sale_items (
                id,
                sale_order_id,
                packaging_id,
                quantity,
                unit_price,
                subtotal
            ) VALUES (
                gen_random_uuid(),
                v_order_id,
                v_pkg_id,
                v_qty,
                v_unit_price,
                v_subtotal
            );
        END LOOP;

        -- 8. Transition Order to final requested status (e.g. Approved)
        IF p_status != 'Pending' THEN
            UPDATE public.sales_orders
            SET status = p_status::transaction_status,
                updated_at = NOW()
            WHERE id = v_order_id;
        END IF;

        RETURN jsonb_build_object(
            'id', v_order_id,
            'reference_number', p_reference_number,
            'status', p_status,
            'total_amount', v_computed_total
        );
    END;
    $FN$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

    ALTER FUNCTION public.create_sales_order_with_items(TEXT, UUID, UUID, UUID, NUMERIC, TIMESTAMPTZ, TEXT, JSONB) OWNER TO postgres;
    GRANT EXECUTE ON FUNCTION public.create_sales_order_with_items(TEXT, UUID, UUID, UUID, NUMERIC, TIMESTAMPTZ, TEXT, JSONB) TO authenticated;

    -- ------------------------------------------------------------------
    -- STEP 5: DROP FOREIGN KEY CONSTRAINTS REFERENCING CUSTOMERS
    -- ------------------------------------------------------------------
    RAISE NOTICE '[STEP 5] Dropping foreign key constraints referencing public.customers...';
    ALTER TABLE public.sales_orders DROP CONSTRAINT IF EXISTS sales_orders_customer_id_fkey;
    ALTER TABLE public.recoveries DROP CONSTRAINT IF EXISTS recoveries_customer_id_fkey;
    ALTER TABLE public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_customer_id_fkey;
    ALTER TABLE public.customers DROP CONSTRAINT IF EXISTS customers_default_salesman_id_fkey;

    -- ------------------------------------------------------------------
    -- STEP 6: DROP OBSOLETE customer_id COLUMNS FROM OPERATIONAL TABLES
    -- ------------------------------------------------------------------
    RAISE NOTICE '[STEP 6] Dropping customer_id columns from sales_orders, recoveries, inventory_transactions...';
    ALTER TABLE public.sales_orders DROP COLUMN IF EXISTS customer_id;
    ALTER TABLE public.recoveries DROP COLUMN IF EXISTS customer_id;
    ALTER TABLE public.inventory_transactions DROP COLUMN IF EXISTS customer_id;

    -- ------------------------------------------------------------------
    -- STEP 7: DROP RLS POLICIES ON public.customers
    -- ------------------------------------------------------------------
    RAISE NOTICE '[STEP 7] Dropping RLS policies on public.customers...';
    DROP POLICY IF EXISTS "Anyone can view customers" ON public.customers;
    DROP POLICY IF EXISTS "Super Admins manage customers" ON public.customers;
    DROP POLICY IF EXISTS "Managers manage customers" ON public.customers;

    -- ------------------------------------------------------------------
    -- STEP 8: PERMANENTLY DROP public.customers TABLE
    -- ------------------------------------------------------------------
    RAISE NOTICE '[STEP 8] Dropping table public.customers...';
    DROP TABLE IF EXISTS public.customers;

    -- ------------------------------------------------------------------
    -- STEP 9: POST-MIGRATION STRICT VERIFICATION GATES
    -- ------------------------------------------------------------------
    RAISE NOTICE '[STEP 9] Executing post-migration strict verification gates...';

    -- 9.1 Verify public.customers table is completely gone
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'customers'
    ) INTO v_cust_table_exists;

    IF v_cust_table_exists THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: public.customers table still exists! Aborting transaction.';
    END IF;

    -- 9.2 Verify public.customer_ledger view is completely gone
    SELECT EXISTS (
        SELECT 1 FROM pg_views 
        WHERE schemaname = 'public' AND viewname = 'customer_ledger'
    ) OR EXISTS (
        SELECT 1 FROM pg_matviews
        WHERE schemaname = 'public' AND matviewname = 'customer_ledger'
    ) INTO v_cust_view_exists;

    IF v_cust_view_exists THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: public.customer_ledger view still exists! Aborting transaction.';
    END IF;

    -- 9.3 Verify customer_id column does not exist on any table in public schema
    SELECT COUNT(*) INTO v_remaining_cust_cols
    FROM information_schema.columns
    WHERE table_schema = 'public' AND column_name = 'customer_id';

    IF v_remaining_cust_cols > 0 THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: customer_id column still exists in % table(s)! Aborting transaction.', v_remaining_cust_cols;
    END IF;

    -- 9.4 Verify all operational business records remain 100% intact
    SELECT COUNT(*) INTO v_post_orders_count FROM public.sales_orders;
    SELECT COUNT(*) INTO v_post_recoveries_count FROM public.recoveries;
    SELECT COUNT(*) INTO v_post_expenses_count FROM public.expenses;
    SELECT COUNT(*) INTO v_post_dist_count FROM public.distributors WHERE code IN ('ELITEWASH#01', 'ELITEWASH#03', 'Elitewash#04');
    SELECT COUNT(*) INTO v_post_staff_count FROM public.profiles WHERE role IN ('Super_Admin', 'Manager') AND is_active = TRUE;
    SELECT COUNT(*) INTO v_post_person_count FROM public.persons WHERE code = 'ELPRODUCTION#01';

    IF v_post_orders_count != v_orders_count THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: Orders count changed from % to %! Data loss detected. Aborting.', v_orders_count, v_post_orders_count;
    END IF;

    IF v_post_recoveries_count != v_recoveries_count THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: Recoveries count changed from % to %! Data loss detected. Aborting.', v_recoveries_count, v_post_recoveries_count;
    END IF;

    IF v_post_expenses_count != v_expenses_count THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: Expenses count changed from % to %! Data loss detected. Aborting.', v_expenses_count, v_post_expenses_count;
    END IF;

    IF v_post_dist_count != 3 THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: Real distributors count changed! Expected 3, found %. Aborting.', v_post_dist_count;
    END IF;

    IF v_post_staff_count != 2 THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: Staff count changed! Expected 2, found %. Aborting.', v_post_staff_count;
    END IF;

    IF v_post_person_count != 1 THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: Manufacturer SHOAIB is missing! Aborting.';
    END IF;

    -- 9.5 Verify zero recoveries have NULL distributor_id
    SELECT COUNT(*) INTO v_post_unassigned_recs
    FROM public.recoveries
    WHERE distributor_id IS NULL;

    IF v_post_unassigned_recs > 0 THEN
        RAISE EXCEPTION 'POST-CHECK FAILED: % recoveries still have NULL distributor_id! Aborting.', v_post_unassigned_recs;
    END IF;

    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'ALL POST-MIGRATION GATES PASSED 100%% CLEAN:';
    RAISE NOTICE '  - public.customers: DROPPED';
    RAISE NOTICE '  - public.customer_ledger: DROPPED';
    RAISE NOTICE '  - customer_id columns: PURGED FROM ALL TABLES (0 remaining)';
    RAISE NOTICE '  - Legitimate Orders Preserved: % of %', v_post_orders_count, v_orders_count;
    RAISE NOTICE '  - Legitimate Recoveries Preserved: % of % (0 unassigned)', v_post_recoveries_count, v_recoveries_count;
    RAISE NOTICE '  - Legitimate Expenses Preserved: % of %', v_post_expenses_count, v_expenses_count;
    RAISE NOTICE '  - Real Distributors Preserved: % (100%%)', v_post_dist_count;
    RAISE NOTICE '  - Staff Profiles Preserved: % (Super Admin & Muhammad saeed)', v_post_staff_count;
    RAISE NOTICE '  - Manufacturer Preserved: % (SHOAIB)', v_post_person_count;
    RAISE NOTICE '======================================================================';

END $CLEANUP_CUSTOMER_BLOCK$;

COMMIT;

-- ==============================================================================
-- ELITE WASHWO ERP — PRODUCTION PHASE 2 DATABASE MIGRATION SCRIPT
-- Version: 3.0 (Production Release: PostgreSQL Parameter Ordering,
--               TG_OP Immutability, Expense Double-Counting Prevention,
--               Server-Side Sales Authorization, Audit Trail Reconciliation)
-- Target: Supabase PostgreSQL 17.6 Production Instance
-- 
-- TRANSACTIONAL & NON-DESTRUCTIVE:
--   - Fully enclosed in BEGIN ... COMMIT.
--   - Preserves all 19 sales, 6 recoveries, 11 expenses, and 3 distributors.
--   - Preserves historical records with NULL distributor_id without auto-assignment.
--   - NEVER redefines or alters Supabase native auth.uid() or auth.jwt().
--   - Default commission rate is verified Rs. 30/pkt unless distributor config differs.
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 0. PLATFORM IDENTITY & EXTENSION SAFEGUARDS
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. AUTH & PERMISSION FUNCTIONS (PRESERVE EXISTING SIGNATURES & BEHAVIOR)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

-- auth_user_role(): Preserves existing return type public.user_role
CREATE OR REPLACE FUNCTION public.auth_user_role() 
RETURNS public.user_role AS $$
DECLARE
    v_role public.user_role;
BEGIN
    SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid() LIMIT 1;
    RETURN v_role;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- has_permission(): Preserves existing behavior (Super_Admin returns true; Manager checks user_permissions)
CREATE OR REPLACE FUNCTION public.has_permission(req_perm TEXT) 
RETURNS BOOLEAN AS $$
DECLARE
    u_role public.user_role;
BEGIN
    SELECT role INTO u_role FROM public.profiles WHERE id = auth.uid() LIMIT 1;
    IF u_role = 'Super_Admin' THEN 
        RETURN TRUE; 
    END IF;
    IF u_role = 'Manager' THEN
        RETURN EXISTS (
            SELECT 1 FROM public.user_permissions 
            WHERE user_id = auth.uid() AND permission_id = req_perm
        );
    END IF;
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

ALTER FUNCTION public.set_updated_at_timestamp() OWNER TO postgres;
ALTER FUNCTION public.auth_user_role() OWNER TO postgres;
ALTER FUNCTION public.has_permission(TEXT) OWNER TO postgres;

GRANT EXECUTE ON FUNCTION public.auth_user_role() TO authenticated;
GRANT EXECUTE ON FUNCTION public.has_permission(TEXT) TO authenticated;

-- ------------------------------------------------------------------------------
-- 2. SCHEMA MODIFICATIONS FOR EXISTING TABLES (NON-DESTRUCTIVE)
-- ------------------------------------------------------------------------------

-- A. SALES_ORDERS: Allow distributor-only sales, add distributor FK & rate snapshots
ALTER TABLE public.sales_orders ALTER COLUMN salesman_id DROP NOT NULL;
ALTER TABLE public.sales_orders ALTER COLUMN customer_id DROP NOT NULL;

ALTER TABLE public.sales_orders
    ADD COLUMN IF NOT EXISTS distributor_id UUID REFERENCES public.distributors(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS commission_rate_snapshot NUMERIC(12, 2),
    ADD COLUMN IF NOT EXISTS advertisement_rate_snapshot NUMERIC(12, 2),
    ADD COLUMN IF NOT EXISTS welfare_rate_snapshot NUMERIC(12, 2);

CREATE INDEX IF NOT EXISTS idx_sales_orders_distributor ON public.sales_orders(distributor_id);
CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON public.sales_orders(status);
CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON public.sales_orders(sale_date);

-- B. SALE_ITEMS: Add audit timestamps if absent
ALTER TABLE public.sale_items
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- C. RECOVERIES: Allow distributor recoveries, add distributor FK, payment details,
--    and safely migrate chk_payment_method constraint to allow 'Adjustment'
ALTER TABLE public.recoveries ALTER COLUMN salesman_id DROP NOT NULL;
ALTER TABLE public.recoveries ALTER COLUMN customer_id DROP NOT NULL;

ALTER TABLE public.recoveries
    ADD COLUMN IF NOT EXISTS distributor_id UUID REFERENCES public.distributors(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS account_detail TEXT,
    ADD COLUMN IF NOT EXISTS tid TEXT,
    ADD COLUMN IF NOT EXISTS notes TEXT;

-- Safe constraint migration: Drop old 3-value constraint and add 4-value constraint allowing 'Adjustment'
DO $$ BEGIN
    ALTER TABLE public.recoveries DROP CONSTRAINT IF EXISTS chk_payment_method;
    ALTER TABLE public.recoveries ADD CONSTRAINT chk_payment_method 
        CHECK (payment_method IN ('Cash', 'Bank', 'Cheque', 'Adjustment'));
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE INDEX IF NOT EXISTS idx_recoveries_distributor ON public.recoveries(distributor_id);
CREATE INDEX IF NOT EXISTS idx_recoveries_status ON public.recoveries(status);
CREATE INDEX IF NOT EXISTS idx_recoveries_date ON public.recoveries(recovery_date);

-- D. EXPENSES: Allow company/distributor/person expenses, add linking columns
ALTER TABLE public.expenses ALTER COLUMN salesman_id DROP NOT NULL;

ALTER TABLE public.expenses
    ADD COLUMN IF NOT EXISTS person_id UUID,
    ADD COLUMN IF NOT EXISTS originating_ledger_entry_id UUID,
    ADD COLUMN IF NOT EXISTS distributor_id UUID REFERENCES public.distributors(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS account_detail TEXT,
    ADD COLUMN IF NOT EXISTS tid TEXT,
    ADD COLUMN IF NOT EXISTS head TEXT;

CREATE INDEX IF NOT EXISTS idx_expenses_person ON public.expenses(person_id);
CREATE INDEX IF NOT EXISTS idx_expenses_originating_entry ON public.expenses(originating_ledger_entry_id);
CREATE INDEX IF NOT EXISTS idx_expenses_distributor ON public.expenses(distributor_id);
CREATE INDEX IF NOT EXISTS idx_expenses_status ON public.expenses(status);

-- E. INVENTORY_TRANSACTIONS: Add distributor FK & new transaction types
ALTER TABLE public.inventory_transactions
    ADD COLUMN IF NOT EXISTS distributor_id UUID REFERENCES public.distributors(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_inv_trans_distributor ON public.inventory_transactions(distributor_id);

DO $$ BEGIN
    ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'Distributor_Issue';
    ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'Distributor_Good_Return';
    ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'Distributor_Damaged_Return';
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- F. GLOBAL_SETTINGS: Add configurable rate columns with defaults
ALTER TABLE public.global_settings
    ADD COLUMN IF NOT EXISTS advertisement_rate NUMERIC(12, 2) DEFAULT 20.00,
    ADD COLUMN IF NOT EXISTS welfare_rate NUMERIC(12, 2) DEFAULT 10.00;

UPDATE public.global_settings
SET advertisement_rate = COALESCE(advertisement_rate, 20.00),
    welfare_rate = COALESCE(welfare_rate, 10.00)
WHERE id = 1;

-- ------------------------------------------------------------------------------
-- 3. NEW PHASE 2 DOMAIN TABLES
-- ------------------------------------------------------------------------------

-- A. PERSON DIRECTORY TABLE
CREATE TABLE IF NOT EXISTS public.persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'Labourer', 'Helper', 'Transporter', 'Manufacturer', 
        'Employee', 'Service Provider', 'Other'
    )),
    phone TEXT,
    cnic TEXT,
    address TEXT,
    default_rate NUMERIC(12, 2) DEFAULT 0.00 CHECK (default_rate >= 0),
    commission_rate NUMERIC(12, 2) DEFAULT 0.00 CHECK (commission_rate >= 0),
    opening_payable_balance NUMERIC(12, 2) DEFAULT 0.00 CHECK (opening_payable_balance >= 0),
    opening_receivable_balance NUMERIC(12, 2) DEFAULT 0.00 CHECK (opening_receivable_balance >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_persons_updated_at ON public.persons;
CREATE TRIGGER trg_persons_updated_at
    BEFORE UPDATE ON public.persons
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at_timestamp();

CREATE INDEX IF NOT EXISTS idx_persons_category ON public.persons(category);
CREATE INDEX IF NOT EXISTS idx_persons_active ON public.persons(is_active);

-- Safely add FK from expenses.person_id to persons(id)
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_expenses_person' AND table_name = 'expenses'
    ) THEN
        ALTER TABLE public.expenses 
        ADD CONSTRAINT fk_expenses_person FOREIGN KEY (person_id) 
        REFERENCES public.persons(id) ON DELETE SET NULL;
    END IF;
END $$;

-- B. PERSON LEDGER ENTRIES TABLE
DO $$ BEGIN
    CREATE TYPE person_entry_type AS ENUM (
        'Opening_Balance', 'Work_Earning', 'Payment', 'Advance', 
        'Commission_Earned', 'Commission_Paid', 'Adjustment'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS public.person_ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_number TEXT NOT NULL UNIQUE,
    person_id UUID NOT NULL REFERENCES public.persons(id) ON DELETE RESTRICT,
    entry_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    entry_type person_entry_type NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('Payable', 'Receivable')),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    quantity NUMERIC(12, 2) DEFAULT 0 CHECK (quantity >= 0),
    rate NUMERIC(12, 2) DEFAULT 0 CHECK (rate >= 0),
    payment_method TEXT DEFAULT 'Cash' CHECK (payment_method IN ('Cash', 'Bank', 'Cheque', 'Other')),
    account_detail TEXT,
    tid TEXT,
    description TEXT,
    expense_id UUID REFERENCES public.expenses(id) ON DELETE SET NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Cancelled')),
    created_by UUID REFERENCES auth.users(id),
    approved_by UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_person_ledger_updated_at ON public.person_ledger_entries;
CREATE TRIGGER trg_person_ledger_updated_at
    BEFORE UPDATE ON public.person_ledger_entries
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at_timestamp();

CREATE INDEX IF NOT EXISTS idx_person_ledger_person ON public.person_ledger_entries(person_id);
CREATE INDEX IF NOT EXISTS idx_person_ledger_status ON public.person_ledger_entries(status);
CREATE INDEX IF NOT EXISTS idx_person_ledger_date ON public.person_ledger_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_person_ledger_expense ON public.person_ledger_entries(expense_id);

-- C. DISTRIBUTOR SETTLEMENTS TABLE
DO $$ BEGIN
    CREATE TYPE distributor_settlement_type AS ENUM (
        'Commission_Cash_Paid', 'Commission_Bank_Paid', 'Commission_Against_Outstanding'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS public.distributor_settlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_number TEXT NOT NULL UNIQUE,
    settlement_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    distributor_id UUID NOT NULL REFERENCES public.distributors(id) ON DELETE RESTRICT,
    settlement_type distributor_settlement_type NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    payment_method TEXT DEFAULT 'Cash' CHECK (payment_method IN ('Cash', 'Bank', 'Adjustment')),
    account_detail TEXT,
    tid TEXT,
    recovery_id UUID REFERENCES public.recoveries(id) ON DELETE SET NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Cancelled')),
    created_by UUID REFERENCES auth.users(id),
    approved_by UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_distributor_settlements_updated_at ON public.distributor_settlements;
CREATE TRIGGER trg_distributor_settlements_updated_at
    BEFORE UPDATE ON public.distributor_settlements
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at_timestamp();

CREATE INDEX IF NOT EXISTS idx_dist_settle_distributor ON public.distributor_settlements(distributor_id);
CREATE INDEX IF NOT EXISTS idx_dist_settle_status ON public.distributor_settlements(status);
CREATE INDEX IF NOT EXISTS idx_dist_settle_date ON public.distributor_settlements(settlement_date);
CREATE INDEX IF NOT EXISTS idx_dist_settle_recovery ON public.distributor_settlements(recovery_id);

-- ------------------------------------------------------------------------------
-- 4. FINANCIAL IMMUTABILITY & RECONCILIATION TRIGGERS
-- ------------------------------------------------------------------------------

-- A. SALES_ORDERS Immutability, Status Transitions & Authorized Reconciliation
CREATE OR REPLACE FUNCTION public.handle_sales_order_immutability()
RETURNS TRIGGER AS $$
DECLARE
    v_caller_role TEXT;
    v_has_approve_perm BOOLEAN;
    v_is_reconciling BOOLEAN := FALSE;
BEGIN
    v_caller_role := COALESCE(public.auth_user_role()::TEXT, '');
    v_has_approve_perm := (v_caller_role = 'Super_Admin') OR COALESCE(public.has_permission('sales.approve'), FALSE);

    -- SAFE INSERT HANDLING
    IF TG_OP = 'INSERT' THEN
        -- If inserting directly as Approved/Posted, require Super_Admin or sales.approve
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

            -- Core financial and relational fields are strictly immutable
            IF (
                NEW.reference_number IS DISTINCT FROM OLD.reference_number OR
                NEW.sale_date IS DISTINCT FROM OLD.sale_date OR
                NEW.distributor_id IS DISTINCT FROM OLD.distributor_id OR
                NEW.salesman_id IS DISTINCT FROM OLD.salesman_id OR
                NEW.customer_id IS DISTINCT FROM OLD.customer_id OR
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
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_sales_order_immutability ON public.sales_orders;
CREATE TRIGGER trg_sales_order_immutability
    BEFORE INSERT OR UPDATE ON public.sales_orders
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_sales_order_immutability();

CREATE OR REPLACE FUNCTION public.prevent_approved_sales_order_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IN ('Approved', 'Posted') THEN
        RAISE EXCEPTION 'Cannot delete approved sales order (%). It must remain in the audit ledger.', OLD.reference_number;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_sales_order_prevent_delete ON public.sales_orders;
CREATE TRIGGER trg_sales_order_prevent_delete
    BEFORE DELETE ON public.sales_orders
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_approved_sales_order_delete();

-- B. SALE_ITEMS Immutability on approved orders (Safe separate TG_OP handling)
CREATE OR REPLACE FUNCTION public.prevent_approved_sale_items_mutation()
RETURNS TRIGGER AS $$
DECLARE
    v_order_id UUID;
    v_order_status TEXT;
BEGIN
    -- Explicit TG_OP separation: NEVER reference NEW on DELETE or OLD on INSERT
    IF TG_OP = 'DELETE' THEN
        v_order_id := OLD.sale_order_id;
    ELSE
        v_order_id := NEW.sale_order_id;
    END IF;

    SELECT status::TEXT INTO v_order_status 
    FROM public.sales_orders 
    WHERE id = v_order_id;

    IF v_order_status IN ('Approved', 'Posted') THEN
        IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'Cannot delete line items of an approved sales order (ID: %).', v_order_id;
        ELSIF TG_OP = 'UPDATE' THEN
            RAISE EXCEPTION 'Cannot update line items of an approved sales order (ID: %).', v_order_id;
        ELSE
            RAISE EXCEPTION 'Cannot insert line items into an approved sales order (ID: %).', v_order_id;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_sale_items_immutability ON public.sale_items;
CREATE TRIGGER trg_sale_items_immutability
    BEFORE INSERT OR UPDATE OR DELETE ON public.sale_items
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_approved_sale_items_mutation();

-- C. RECOVERIES Immutability & Reversal Protection
CREATE OR REPLACE FUNCTION public.handle_recovery_immutability()
RETURNS TRIGGER AS $$
DECLARE
    v_caller_role TEXT;
    v_has_approve_perm BOOLEAN;
BEGIN
    v_caller_role := COALESCE(public.auth_user_role()::TEXT, '');
    v_has_approve_perm := (v_caller_role = 'Super_Admin') OR 
                          COALESCE(public.has_permission('sales.approve'), FALSE) OR 
                          COALESCE(public.has_permission('settlement.approve'), FALSE);

    -- Protect commission adjustment recoveries from direct client manipulation/cancellation
    IF OLD.payment_method = 'Adjustment' AND pg_trigger_depth() <= 1 THEN
        IF NEW.status IS DISTINCT FROM OLD.status OR NEW.amount IS DISTINCT FROM OLD.amount THEN
            RAISE EXCEPTION 'Commission adjustment recoveries cannot be modified or cancelled directly. Modify or cancel the originating distributor settlement.';
        END IF;
    END IF;

    IF OLD.status IN ('Approved', 'Posted') THEN
        IF (
            NEW.reference_number IS DISTINCT FROM OLD.reference_number OR
            NEW.recovery_date IS DISTINCT FROM OLD.recovery_date OR
            NEW.distributor_id IS DISTINCT FROM OLD.distributor_id OR
            NEW.salesman_id IS DISTINCT FROM OLD.salesman_id OR
            NEW.customer_id IS DISTINCT FROM OLD.customer_id OR
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
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_recovery_immutability ON public.recoveries;
CREATE TRIGGER trg_recovery_immutability
    BEFORE UPDATE ON public.recoveries
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_recovery_immutability();

CREATE OR REPLACE FUNCTION public.prevent_approved_recovery_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IN ('Approved', 'Posted') THEN
        RAISE EXCEPTION 'Cannot delete approved recovery (%). It must remain in the audit ledger.', OLD.reference_number;
    END IF;
    IF OLD.payment_method = 'Adjustment' AND pg_trigger_depth() <= 1 THEN
        RAISE EXCEPTION 'Cannot delete commission adjustment recovery (%). Cancel the originating distributor settlement.', OLD.reference_number;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_recovery_prevent_delete ON public.recoveries;
CREATE TRIGGER trg_recovery_prevent_delete
    BEFORE DELETE ON public.recoveries
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_approved_recovery_delete();

-- D. EXPENSES Immutability & Reversal Protection
CREATE OR REPLACE FUNCTION public.handle_expense_immutability()
RETURNS TRIGGER AS $$
DECLARE
    v_caller_role TEXT;
    v_has_approve_perm BOOLEAN;
BEGIN
    v_caller_role := COALESCE(public.auth_user_role()::TEXT, '');
    v_has_approve_perm := (v_caller_role = 'Super_Admin') OR 
                          COALESCE(public.has_permission('expenses.approve'), FALSE) OR 
                          COALESCE(public.has_permission('payments.approve'), FALSE);

    -- Protect linked person expenses from direct client modification/cancellation
    IF OLD.originating_ledger_entry_id IS NOT NULL AND pg_trigger_depth() <= 1 THEN
        IF NEW.status IS DISTINCT FROM OLD.status OR NEW.amount IS DISTINCT FROM OLD.amount THEN
            RAISE EXCEPTION 'Linked person expenses cannot be modified or cancelled directly. Modify or cancel the originating person ledger entry.';
        END IF;
    END IF;

    IF OLD.status = 'Approved' THEN
        IF (
            NEW.reference_number IS DISTINCT FROM OLD.reference_number OR
            NEW.expense_date IS DISTINCT FROM OLD.expense_date OR
            NEW.distributor_id IS DISTINCT FROM OLD.distributor_id OR
            NEW.person_id IS DISTINCT FROM OLD.person_id OR
            NEW.salesman_id IS DISTINCT FROM OLD.salesman_id OR
            NEW.amount IS DISTINCT FROM OLD.amount OR
            NEW.originating_ledger_entry_id IS DISTINCT FROM OLD.originating_ledger_entry_id
        ) THEN
            RAISE EXCEPTION 'Approved expenses are strictly immutable. Financial and linking fields cannot be modified.';
        END IF;

        IF NEW.status = 'Cancelled' AND OLD.status != 'Cancelled' THEN
            IF NOT v_has_approve_perm THEN
                RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized users can cancel approved expenses.';
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_expense_immutability ON public.expenses;
CREATE TRIGGER trg_expense_immutability
    BEFORE UPDATE ON public.expenses
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_expense_immutability();

CREATE OR REPLACE FUNCTION public.prevent_approved_expense_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'Approved' THEN
        RAISE EXCEPTION 'Cannot delete approved expense (%). It must remain in the audit ledger.', OLD.reference_number;
    END IF;
    IF OLD.originating_ledger_entry_id IS NOT NULL AND pg_trigger_depth() <= 1 THEN
        RAISE EXCEPTION 'Cannot delete linked person expense (%). Delete or cancel the originating person ledger entry.', OLD.reference_number;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_expense_prevent_delete ON public.expenses;
CREATE TRIGGER trg_expense_prevent_delete
    BEFORE DELETE ON public.expenses
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_approved_expense_delete();

-- ------------------------------------------------------------------------------
-- 5. WORKFLOW TRIGGERS (SAFE INSERT & UPDATE SEPARATION)
-- ------------------------------------------------------------------------------

-- A. Person Ledger Workflow Trigger
CREATE OR REPLACE FUNCTION public.handle_person_ledger_entry_workflow()
RETURNS TRIGGER AS $$
DECLARE
    v_caller_role TEXT;
    v_has_approve_perm BOOLEAN;
BEGIN
    v_caller_role := COALESCE(public.auth_user_role()::TEXT, '');
    v_has_approve_perm := (v_caller_role = 'Super_Admin') OR COALESCE(public.has_permission('payments.approve'), FALSE);

    -- SAFE INSERT HANDLING
    IF TG_OP = 'INSERT' THEN
        -- Prevent double-counting: expense_id can only ever be attached to Payment entries
        IF NEW.expense_id IS NOT NULL AND NEW.entry_type != 'Payment' THEN
            RAISE EXCEPTION 'Invalid ledger entry: expense_id can only be linked to Payment entries (entry_type: %). Work_Earning is an accrued liability and Advance is a receivable.', NEW.entry_type;
        END IF;

        IF NEW.status = 'Approved' THEN
            IF NOT v_has_approve_perm THEN
                RAISE EXCEPTION 'Direct insertion with Approved status is prohibited. Entries must start with status Pending.';
            END IF;
            NEW.approved_at := COALESCE(NEW.approved_at, NOW());
            NEW.approved_by := COALESCE(NEW.approved_by, auth.uid());
        ELSE
            NEW.status := 'Pending';
        END IF;
        RETURN NEW;
    END IF;

    -- SAFE UPDATE HANDLING
    IF TG_OP = 'UPDATE' THEN
        -- Prevent double-counting: expense_id can only ever be attached to Payment entries
        IF NEW.expense_id IS NOT NULL AND NEW.entry_type != 'Payment' THEN
            RAISE EXCEPTION 'Invalid ledger entry: expense_id can only be linked to Payment entries (entry_type: %).', NEW.entry_type;
        END IF;

        -- If already Approved: enforce immutability of financial and audit fields
        IF OLD.status = 'Approved' THEN
            IF (
                NEW.person_id IS DISTINCT FROM OLD.person_id OR
                NEW.amount IS DISTINCT FROM OLD.amount OR
                NEW.direction IS DISTINCT FROM OLD.direction OR
                NEW.entry_type IS DISTINCT FROM OLD.entry_type OR
                NEW.entry_date IS DISTINCT FROM OLD.entry_date OR
                NEW.quantity IS DISTINCT FROM OLD.quantity OR
                NEW.rate IS DISTINCT FROM OLD.rate OR
                NEW.payment_method IS DISTINCT FROM OLD.payment_method OR
                NEW.account_detail IS DISTINCT FROM OLD.account_detail OR
                NEW.tid IS DISTINCT FROM OLD.tid OR
                NEW.expense_id IS DISTINCT FROM OLD.expense_id OR
                NEW.created_by IS DISTINCT FROM OLD.created_by OR
                NEW.created_at IS DISTINCT FROM OLD.created_at
            ) THEN
                RAISE EXCEPTION 'Approved financial transactions are strictly immutable. Financial fields cannot be modified even when cancelling.';
            END IF;
        END IF;

        -- Prevent re-approval of Cancelled records
        IF OLD.status = 'Cancelled' AND NEW.status != 'Cancelled' THEN
            RAISE EXCEPTION 'Entry % is already Cancelled and cannot be approved or reactivated.', OLD.reference_number;
        END IF;

        -- Transition from Pending to Approved
        IF NEW.status = 'Approved' AND OLD.status != 'Approved' THEN
            IF NOT v_has_approve_perm THEN
                RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized Managers with payments.approve permission can approve entries.';
            END IF;

            NEW.approved_at := COALESCE(NEW.approved_at, NOW());
            NEW.approved_by := COALESCE(NEW.approved_by, auth.uid());

            -- Synchronized Expense Approval
            IF NEW.expense_id IS NOT NULL THEN
                UPDATE public.expenses
                SET status = 'Approved'
                WHERE id = NEW.expense_id
                  AND originating_ledger_entry_id = NEW.id
                  AND status != 'Approved';
            END IF;
        END IF;

        -- Transition from Approved to Cancelled: Reverse only the owned expense
        IF NEW.status = 'Cancelled' AND OLD.status = 'Approved' THEN
            IF NOT v_has_approve_perm THEN
                RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized Managers with payments.approve permission can cancel approved entries.';
            END IF;

            IF NEW.expense_id IS NOT NULL THEN
                UPDATE public.expenses 
                SET status = 'Cancelled', 
                    description = description || ' [Reversed via Person Ledger: ' || NEW.reference_number || ']'
                WHERE id = NEW.expense_id 
                  AND person_id = NEW.person_id
                  AND originating_ledger_entry_id = NEW.id
                  AND status != 'Cancelled';
            END IF;
        END IF;

        RETURN NEW;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_person_ledger_workflow ON public.person_ledger_entries;
CREATE TRIGGER trg_person_ledger_workflow
    BEFORE INSERT OR UPDATE ON public.person_ledger_entries
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_person_ledger_entry_workflow();

CREATE OR REPLACE FUNCTION public.prevent_approved_person_entry_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'Approved' THEN
        RAISE EXCEPTION 'Cannot delete approved person ledger entry (%). Status must be Cancelled via authorized reversal.', OLD.reference_number;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_person_ledger_prevent_delete ON public.person_ledger_entries;
CREATE TRIGGER trg_person_ledger_prevent_delete
    BEFORE DELETE ON public.person_ledger_entries
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_approved_person_entry_delete();

-- B. Distributor Settlement Workflow Trigger
CREATE OR REPLACE FUNCTION public.handle_distributor_settlement_workflow()
RETURNS TRIGGER AS $$
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

                -- Atomic creation of linked recovery
                IF NEW.recovery_id IS NULL THEN
                    v_rec_ref := 'REC-SET-' || SUBSTRING(REPLACE(NEW.reference_number, '-', ''), 1, 10) || '-' || SUBSTRING(OLD.id::TEXT, 1, 6);

                    INSERT INTO public.recoveries (
                        reference_number,
                        recovery_date,
                        distributor_id,
                        salesman_id,
                        customer_id,
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
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_distributor_settlement_workflow ON public.distributor_settlements;
CREATE TRIGGER trg_distributor_settlement_workflow
    BEFORE INSERT OR UPDATE ON public.distributor_settlements
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_distributor_settlement_workflow();

CREATE OR REPLACE FUNCTION public.prevent_approved_settlement_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'Approved' THEN
        RAISE EXCEPTION 'Cannot delete approved settlement (%). Status must be Cancelled via authorized reversal.', OLD.reference_number;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_distributor_settlement_prevent_delete ON public.distributor_settlements;
CREATE TRIGGER trg_distributor_settlement_prevent_delete
    BEFORE DELETE ON public.distributor_settlements
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_approved_settlement_delete();

-- ------------------------------------------------------------------------------
-- 6. SERVER-SIDE RPC FUNCTIONS (SECURITY DEFINER + SAFE SEARCH_PATH)
-- ------------------------------------------------------------------------------

-- A. Atomic Sales Order & Items Creation RPC
-- Workflow: Insert as Pending -> Insert & Validate line items -> Transition to Approved
-- Parameter ordering: all parameters with defaults follow required parameters
DROP FUNCTION IF EXISTS public.create_sales_order_with_items(TEXT, UUID, UUID, UUID, NUMERIC, TIMESTAMPTZ, TEXT, JSONB);
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
RETURNS JSONB AS $$
DECLARE
    v_order_id UUID := gen_random_uuid();
    v_comm_rate NUMERIC(12, 2) := 30.00; -- Standard verified business rate (Rs. 30/pkt)
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
        -- Use distributor configured commission, defaulting to Rs. 30 if null
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

    -- 6. Insert Order Header as 'Pending' first (bypasses trg_sale_items_immutability block)
    INSERT INTO public.sales_orders (
        id,
        reference_number,
        distributor_id,
        salesman_id,
        customer_id,
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
        p_customer_id,
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
            subtotal,
            created_at,
            updated_at
        ) VALUES (
            gen_random_uuid(),
            v_order_id,
            v_pkg_id,
            v_qty,
            v_unit_price,
            v_subtotal,
            NOW(),
            NOW()
        );
    END LOOP;

    -- 8. If requested status was Approved/Posted, transition header now that items are attached
    IF p_status IN ('Approved', 'Posted') THEN
        UPDATE public.sales_orders
        SET status = p_status::transaction_status,
            updated_at = NOW()
        WHERE id = v_order_id;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'id', v_order_id,
        'order_id', v_order_id,
        'reference_number', p_reference_number,
        'total_amount', v_computed_total,
        'status', p_status
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- B. Atomic Person Ledger Entry & Linked Expense Creation RPC
-- Double-counting prevention: Operational expenses can ONLY be linked to Payment entries
DROP FUNCTION IF EXISTS public.create_person_ledger_entry_with_expense(UUID, TEXT, TEXT, NUMERIC, TEXT, NUMERIC, NUMERIC, TEXT, TEXT, TEXT, TEXT, BOOLEAN, BOOLEAN);
CREATE OR REPLACE FUNCTION public.create_person_ledger_entry_with_expense(
    p_person_id UUID,
    p_entry_type TEXT,
    p_direction TEXT,
    p_amount NUMERIC,
    p_description TEXT,
    p_quantity NUMERIC DEFAULT 0,
    p_rate NUMERIC DEFAULT 0,
    p_payment_method TEXT DEFAULT 'Cash',
    p_account_detail TEXT DEFAULT '',
    p_tid TEXT DEFAULT '',
    p_notes TEXT DEFAULT '',
    p_create_expense BOOLEAN DEFAULT FALSE,
    p_auto_approve BOOLEAN DEFAULT FALSE
)
RETURNS JSONB AS $$
DECLARE
    v_entry_id UUID := gen_random_uuid();
    v_expense_id UUID := NULL;
    v_entry_ref TEXT;
    v_exp_ref TEXT;
    v_person RECORD;
    v_caller_role TEXT;
    v_has_approve_perm BOOLEAN;
    v_status TEXT := 'Pending';
    v_approved_by UUID := NULL;
    v_approved_at TIMESTAMPTZ := NULL;
BEGIN
    SELECT * INTO v_person FROM public.persons WHERE id = p_person_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Person not found with ID %', p_person_id;
    END IF;

    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be greater than zero.';
    END IF;

    -- Double-counting prevention: Operational expenses can ONLY be linked to Payment entries
    IF p_create_expense THEN
        IF p_entry_type != 'Payment' THEN
            RAISE EXCEPTION 'Operational expenses can only be linked to Payment entries. Entry type % represents an accrual liability or advance; linking an operational expense causes double-counting.', p_entry_type;
        END IF;
    END IF;

    IF p_entry_type = 'Work_Earning' AND p_quantity > 0 AND p_rate > 0 THEN
        IF ROUND(p_amount, 2) != ROUND(p_quantity * p_rate, 2) THEN
            RAISE EXCEPTION 'Work amount (Rs. %) must equal Quantity (%) * Rate (Rs. %)', p_amount, p_quantity, p_rate;
        END IF;
    END IF;

    -- Generate reference numbers
    v_entry_ref := CASE 
        WHEN p_entry_type = 'Work_Earning' THEN 'WRK-' 
        WHEN p_entry_type IN ('Payment', 'Advance') THEN 'PMT-' 
        ELSE 'ENT-' 
    END || TO_CHAR(NOW(), 'YYMMDD') || '-' || SUBSTRING(v_entry_id::TEXT, 1, 6);

    -- Check auto-approval authorization if requested
    IF p_auto_approve THEN
        v_caller_role := COALESCE(public.auth_user_role()::TEXT, '');
        v_has_approve_perm := COALESCE(public.has_permission('payments.approve'), FALSE);
        IF v_caller_role = 'Super_Admin' OR v_has_approve_perm THEN
            v_status := 'Approved';
            v_approved_by := auth.uid();
            v_approved_at := NOW();
        ELSE
            v_status := 'Pending';
        END IF;
    END IF;

    -- If linked expense requested (strictly Payment), insert expense first with synchronized status
    IF p_create_expense AND p_entry_type = 'Payment' THEN
        v_expense_id := gen_random_uuid();
        v_exp_ref := 'EXP-' || TO_CHAR(NOW(), 'YYMMDD') || '-' || SUBSTRING(v_expense_id::TEXT, 1, 6);

        INSERT INTO public.expenses (
            id,
            reference_number,
            expense_date,
            category,
            head,
            amount,
            description,
            paid_by,
            payment_method,
            account_detail,
            tid,
            person_id,
            originating_ledger_entry_id,
            status,
            created_at
        ) VALUES (
            v_expense_id,
            v_exp_ref,
            NOW(),
            'Company',
            v_person.category,
            p_amount,
            'Payment to ' || v_person.name || ': ' || p_description,
            'Company',
            p_payment_method,
            p_account_detail,
            p_tid,
            p_person_id,
            v_entry_id,
            v_status::transaction_status,
            NOW()
        );
    END IF;

    -- Insert Person Ledger Entry
    INSERT INTO public.person_ledger_entries (
        id,
        reference_number,
        person_id,
        entry_date,
        entry_type,
        direction,
        amount,
        quantity,
        rate,
        payment_method,
        account_detail,
        tid,
        description,
        expense_id,
        notes,
        status,
        created_by,
        approved_by,
        approved_at,
        created_at,
        updated_at
    ) VALUES (
        v_entry_id,
        v_entry_ref,
        p_person_id,
        NOW(),
        p_entry_type::person_entry_type,
        p_direction,
        p_amount,
        p_quantity,
        p_rate,
        p_payment_method,
        p_account_detail,
        p_tid,
        p_description,
        v_expense_id,
        p_notes,
        v_status,
        auth.uid(),
        v_approved_by,
        v_approved_at,
        NOW(),
        NOW()
    );

    RETURN jsonb_build_object(
        'success', true,
        'entry_id', v_entry_id,
        'id', v_entry_id,
        'reference_number', v_entry_ref,
        'expense_id', v_expense_id,
        'expense_reference', v_exp_ref,
        'status', v_status
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- C. Approve Person Ledger Entry RPC
DROP FUNCTION IF EXISTS public.approve_person_ledger_entry(UUID);
CREATE OR REPLACE FUNCTION public.approve_person_ledger_entry(p_entry_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_entry RECORD;
BEGIN
    IF COALESCE(public.auth_user_role()::TEXT, '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('payments.approve'), FALSE) THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin or users with payments.approve permission can approve entries.';
    END IF;

    SELECT * INTO v_entry FROM public.person_ledger_entries WHERE id = p_entry_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Person ledger entry not found.';
    END IF;
    
    IF v_entry.status != 'Pending' THEN
        RAISE EXCEPTION 'Entry is already % and cannot be approved.', v_entry.status;
    END IF;

    UPDATE public.person_ledger_entries
    SET status = 'Approved', approved_at = NOW(), approved_by = auth.uid()
    WHERE id = p_entry_id;

    -- Synchronized Expense Approval (handled automatically by trg_person_ledger_workflow, kept idempotent here)
    IF v_entry.expense_id IS NOT NULL THEN
        UPDATE public.expenses
        SET status = 'Approved'
        WHERE id = v_entry.expense_id
          AND originating_ledger_entry_id = p_entry_id
          AND status != 'Approved';
    END IF;

    RETURN jsonb_build_object('success', true, 'id', p_entry_id, 'status', 'Approved');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- D. Cancel Person Ledger Entry RPC
DROP FUNCTION IF EXISTS public.cancel_person_ledger_entry(UUID, TEXT);
CREATE OR REPLACE FUNCTION public.cancel_person_ledger_entry(p_entry_id UUID, p_reason TEXT DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    v_entry RECORD;
BEGIN
    IF COALESCE(public.auth_user_role()::TEXT, '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('payments.approve'), FALSE) THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin or users with payments.approve permission can cancel entries.';
    END IF;

    SELECT * INTO v_entry FROM public.person_ledger_entries WHERE id = p_entry_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Person ledger entry not found.';
    END IF;

    UPDATE public.person_ledger_entries
    SET status = 'Cancelled', 
        description = CASE WHEN p_reason IS NOT NULL AND p_reason != '' THEN description || ' [Reason: ' || p_reason || ']' ELSE description END,
        notes = CASE WHEN p_reason IS NOT NULL AND p_reason != '' THEN COALESCE(notes, '') || ' [Cancelled: ' || p_reason || ']' ELSE notes END
    WHERE id = p_entry_id;

    -- Synchronized Expense Cancellation (handled automatically by trg_person_ledger_workflow, kept idempotent here)
    IF v_entry.expense_id IS NOT NULL THEN
        UPDATE public.expenses 
        SET status = 'Cancelled', 
            description = description || ' [Reversed via Person Ledger: ' || v_entry.reference_number || ']'
        WHERE id = v_entry.expense_id 
          AND person_id = v_entry.person_id
          AND originating_ledger_entry_id = p_entry_id
          AND status != 'Cancelled';
    END IF;

    RETURN jsonb_build_object('success', true, 'id', p_entry_id, 'status', 'Cancelled');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- E. Approve Distributor Settlement RPC
DROP FUNCTION IF EXISTS public.approve_distributor_settlement(UUID);
CREATE OR REPLACE FUNCTION public.approve_distributor_settlement(p_settlement_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_settle RECORD;
BEGIN
    IF COALESCE(public.auth_user_role()::TEXT, '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('settlement.approve'), FALSE) THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin or users with settlement.approve permission can approve settlements.';
    END IF;

    SELECT * INTO v_settle FROM public.distributor_settlements WHERE id = p_settlement_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Distributor settlement not found.';
    END IF;

    IF v_settle.status != 'Pending' THEN
        RAISE EXCEPTION 'Settlement is already % and cannot be approved.', v_settle.status;
    END IF;

    UPDATE public.distributor_settlements
    SET status = 'Approved', approved_at = NOW(), approved_by = auth.uid()
    WHERE id = p_settlement_id;

    RETURN jsonb_build_object('success', true, 'id', p_settlement_id, 'status', 'Approved');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- F. Cancel Distributor Settlement RPC
DROP FUNCTION IF EXISTS public.cancel_distributor_settlement(UUID, TEXT);
CREATE OR REPLACE FUNCTION public.cancel_distributor_settlement(p_settlement_id UUID, p_reason TEXT DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    v_settle RECORD;
BEGIN
    IF COALESCE(public.auth_user_role()::TEXT, '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('settlement.approve'), FALSE) THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin or users with settlement.approve permission can cancel settlements.';
    END IF;

    SELECT * INTO v_settle FROM public.distributor_settlements WHERE id = p_settlement_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Distributor settlement not found.';
    END IF;

    UPDATE public.distributor_settlements
    SET status = 'Cancelled',
        notes = CASE WHEN p_reason IS NOT NULL AND p_reason != '' THEN COALESCE(notes, '') || ' [Cancelled: ' || p_reason || ']' ELSE notes END
    WHERE id = p_settlement_id;

    RETURN jsonb_build_object('success', true, 'id', p_settlement_id, 'status', 'Cancelled');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- G. Historical Sales Order Rate Reconciliation RPC (with rate validation & audit log)
DROP FUNCTION IF EXISTS public.reconcile_historical_sales_order_rates(UUID, NUMERIC, NUMERIC, NUMERIC);
CREATE OR REPLACE FUNCTION public.reconcile_historical_sales_order_rates(
    p_order_id UUID,
    p_commission_rate NUMERIC(12, 2),
    p_advertisement_rate NUMERIC(12, 2),
    p_welfare_rate NUMERIC(12, 2)
)
RETURNS JSONB AS $$
DECLARE
    v_order RECORD;
BEGIN
    IF COALESCE(public.auth_user_role()::TEXT, '') != 'Super_Admin' THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin can reconcile historical sales order rates.';
    END IF;

    -- Rate bounds validation
    IF p_commission_rate IS NULL OR p_commission_rate < 0 OR p_commission_rate > 500.00 THEN
        RAISE EXCEPTION 'Invalid commission rate: %. Must be between 0 and 500.', p_commission_rate;
    END IF;
    IF p_advertisement_rate IS NULL OR p_advertisement_rate < 0 OR p_advertisement_rate > 500.00 THEN
        RAISE EXCEPTION 'Invalid advertisement rate: %. Must be between 0 and 500.', p_advertisement_rate;
    END IF;
    IF p_welfare_rate IS NULL OR p_welfare_rate < 0 OR p_welfare_rate > 500.00 THEN
        RAISE EXCEPTION 'Invalid welfare rate: %. Must be between 0 and 500.', p_welfare_rate;
    END IF;

    -- Row lock and verify order existence
    SELECT * INTO v_order FROM public.sales_orders WHERE id = p_order_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Sales order % not found.', p_order_id;
    END IF;

    -- Prevent modifying snapshots that have already been reconciled
    IF v_order.commission_rate_snapshot IS NOT NULL THEN
        RAISE EXCEPTION 'Sales order % is already reconciled with commission rate Rs. %. Rates cannot be modified once set.',
            v_order.reference_number, v_order.commission_rate_snapshot;
    END IF;

    -- Update snapshot rates
    UPDATE public.sales_orders
    SET commission_rate_snapshot = p_commission_rate,
        advertisement_rate_snapshot = p_advertisement_rate,
        welfare_rate_snapshot = p_welfare_rate,
        updated_at = NOW()
    WHERE id = p_order_id;

    -- Record explicit entry in audit_logs
    INSERT INTO public.audit_logs (
        table_name,
        record_id,
        action,
        old_data,
        new_data,
        performed_by,
        created_at
    ) VALUES (
        'sales_orders',
        p_order_id,
        'RECONCILE_RATES',
        jsonb_build_object(
            'reference_number', v_order.reference_number,
            'commission_rate_snapshot', v_order.commission_rate_snapshot,
            'advertisement_rate_snapshot', v_order.advertisement_rate_snapshot,
            'welfare_rate_snapshot', v_order.welfare_rate_snapshot
        ),
        jsonb_build_object(
            'reference_number', v_order.reference_number,
            'commission_rate_snapshot', p_commission_rate,
            'advertisement_rate_snapshot', p_advertisement_rate,
            'welfare_rate_snapshot', p_welfare_rate
        ),
        auth.uid(),
        NOW()
    );

    RETURN jsonb_build_object(
        'success', true, 
        'id', p_order_id,
        'reference_number', v_order.reference_number,
        'commission_rate_snapshot', p_commission_rate,
        'advertisement_rate_snapshot', p_advertisement_rate,
        'welfare_rate_snapshot', p_welfare_rate
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- H. Unreconciled Sales Orders Audit View
CREATE OR REPLACE VIEW public.v_unreconciled_sales_orders AS
SELECT 
    so.id,
    so.reference_number,
    so.sale_date,
    so.distributor_id,
    d.name AS distributor_name,
    d.code AS distributor_code,
    so.total_amount,
    so.status,
    so.commission_rate_snapshot,
    COALESCE(SUM(si.quantity), 0) AS total_packets
FROM public.sales_orders so
LEFT JOIN public.distributors d ON d.id = so.distributor_id
LEFT JOIN public.sale_items si ON si.sale_order_id = so.id
WHERE so.distributor_id IS NOT NULL 
  AND so.commission_rate_snapshot IS NULL
GROUP BY so.id, so.reference_number, so.sale_date, so.distributor_id, d.name, d.code, so.total_amount, so.status, so.commission_rate_snapshot;

-- Function Ownership
ALTER FUNCTION public.create_sales_order_with_items(TEXT, UUID, UUID, UUID, NUMERIC, TIMESTAMPTZ, TEXT, JSONB) OWNER TO postgres;
ALTER FUNCTION public.create_person_ledger_entry_with_expense(UUID, TEXT, TEXT, NUMERIC, TEXT, NUMERIC, NUMERIC, TEXT, TEXT, TEXT, TEXT, BOOLEAN, BOOLEAN) OWNER TO postgres;
ALTER FUNCTION public.approve_person_ledger_entry(UUID) OWNER TO postgres;
ALTER FUNCTION public.cancel_person_ledger_entry(UUID, TEXT) OWNER TO postgres;
ALTER FUNCTION public.approve_distributor_settlement(UUID) OWNER TO postgres;
ALTER FUNCTION public.cancel_distributor_settlement(UUID, TEXT) OWNER TO postgres;
ALTER FUNCTION public.reconcile_historical_sales_order_rates(UUID, NUMERIC, NUMERIC, NUMERIC) OWNER TO postgres;

-- Minimal EXECUTE grants to authenticated role
GRANT EXECUTE ON FUNCTION public.create_sales_order_with_items(TEXT, UUID, UUID, UUID, NUMERIC, TIMESTAMPTZ, TEXT, JSONB) TO authenticated;
GRANT EXECUTE ON FUNCTION public.create_person_ledger_entry_with_expense(UUID, TEXT, TEXT, NUMERIC, TEXT, NUMERIC, NUMERIC, TEXT, TEXT, TEXT, TEXT, BOOLEAN, BOOLEAN) TO authenticated;
GRANT EXECUTE ON FUNCTION public.approve_person_ledger_entry(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.cancel_person_ledger_entry(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.approve_distributor_settlement(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.cancel_distributor_settlement(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.reconcile_historical_sales_order_rates(UUID, NUMERIC, NUMERIC, NUMERIC) TO authenticated;

-- ------------------------------------------------------------------------------
-- 7. MASTER PERMISSIONS SEEDING
-- ------------------------------------------------------------------------------
INSERT INTO public.permissions (id, module, description) VALUES
('payments.view',       'Payments',   'View person directory and financial ledgers'),
('payments.create',     'Payments',   'Record work earnings and payments'),
('payments.edit',       'Payments',   'Edit pending person directory and ledger entries'),
('payments.approve',    'Payments',   'Approve pending person payment entries'),
('payments.export',     'Payments',   'Export person statements and ledgers'),
('settlement.view',      'Settlement', 'View distributor settlement records'),
('settlement.create',    'Settlement', 'Create distributor commission settlement entries'),
('settlement.approve',   'Settlement', 'Approve distributor commission settlements')
ON CONFLICT (id) DO NOTHING;

-- ------------------------------------------------------------------------------
-- 8. GRANULAR ROW LEVEL SECURITY (RLS) POLICIES & COLUMN PRIVILEGES
-- ------------------------------------------------------------------------------

-- Enable RLS on new tables
ALTER TABLE public.persons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.person_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.distributor_settlements ENABLE ROW LEVEL SECURITY;

-- Revoke all table-level access from anon and public
REVOKE ALL ON TABLE public.persons FROM PUBLIC, anon;
REVOKE ALL ON TABLE public.person_ledger_entries FROM PUBLIC, anon;
REVOKE ALL ON TABLE public.distributor_settlements FROM PUBLIC, anon;

-- Direct table UPDATE & DELETE revoked from authenticated (must use RPC for approval/reversal)
REVOKE UPDATE, DELETE ON TABLE public.person_ledger_entries FROM authenticated;
REVOKE UPDATE, DELETE ON TABLE public.distributor_settlements FROM authenticated;

-- Grant table SELECT and INSERT to authenticated
GRANT SELECT, INSERT ON TABLE public.person_ledger_entries TO authenticated;
GRANT SELECT, INSERT ON TABLE public.distributor_settlements TO authenticated;
GRANT SELECT, INSERT, UPDATE ON TABLE public.persons TO authenticated;

-- Column-level UPDATE grants on editable non-sensitive columns
GRANT UPDATE (
    person_id, entry_type, direction, amount, quantity, rate,
    entry_date, payment_method, account_detail, tid, description, notes, expense_id
) ON TABLE public.person_ledger_entries TO authenticated;

GRANT UPDATE (
    settlement_type, distributor_id, settlement_date, amount,
    payment_method, account_detail, tid, notes
) ON TABLE public.distributor_settlements TO authenticated;

-- Clean redundant/overlapping ad-hoc policies
DROP POLICY IF EXISTS "Allow Admins and Managers to insert inventory" ON public.inventory_transactions;
DROP POLICY IF EXISTS "Allow Admins and Managers to insert expenses" ON public.expenses;

-- Drop and recreate clean policies on Persons
DROP POLICY IF EXISTS "Admins full access persons" ON public.persons;
DROP POLICY IF EXISTS "Managers select persons" ON public.persons;
DROP POLICY IF EXISTS "Managers insert persons" ON public.persons;
DROP POLICY IF EXISTS "Managers update persons" ON public.persons;

CREATE POLICY "Admins full access persons" ON public.persons
    FOR ALL TO authenticated
    USING (COALESCE(public.auth_user_role()::TEXT, '') = 'Super_Admin')
    WITH CHECK (COALESCE(public.auth_user_role()::TEXT, '') = 'Super_Admin');

CREATE POLICY "Managers select persons" ON public.persons
    FOR SELECT TO authenticated
    USING (COALESCE(public.has_permission('payments.view'), FALSE));

CREATE POLICY "Managers insert persons" ON public.persons
    FOR INSERT TO authenticated
    WITH CHECK (COALESCE(public.has_permission('payments.create'), FALSE));

CREATE POLICY "Managers update persons" ON public.persons
    FOR UPDATE TO authenticated
    USING (COALESCE(public.has_permission('payments.edit'), FALSE))
    WITH CHECK (COALESCE(public.has_permission('payments.edit'), FALSE));

-- Drop and recreate clean policies on Person Ledger Entries
DROP POLICY IF EXISTS "Admins full access person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Managers select person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Managers insert person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Managers update pending person entries" ON public.person_ledger_entries;

CREATE POLICY "Admins full access person entries" ON public.person_ledger_entries
    FOR ALL TO authenticated
    USING (COALESCE(public.auth_user_role()::TEXT, '') = 'Super_Admin')
    WITH CHECK (COALESCE(public.auth_user_role()::TEXT, '') = 'Super_Admin');

CREATE POLICY "Managers select person entries" ON public.person_ledger_entries
    FOR SELECT TO authenticated
    USING (COALESCE(public.has_permission('payments.view'), FALSE));

CREATE POLICY "Managers insert person entries" ON public.person_ledger_entries
    FOR INSERT TO authenticated
    WITH CHECK (COALESCE(public.has_permission('payments.create'), FALSE));

CREATE POLICY "Managers update pending person entries" ON public.person_ledger_entries
    FOR UPDATE TO authenticated
    USING (status = 'Pending' AND COALESCE(public.has_permission('payments.edit'), FALSE))
    WITH CHECK (status = 'Pending' AND COALESCE(public.has_permission('payments.edit'), FALSE));

-- Drop and recreate clean policies on Distributor Settlements
DROP POLICY IF EXISTS "Admins full access settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Managers select settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Managers insert settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Managers update pending settlements" ON public.distributor_settlements;

CREATE POLICY "Admins full access settlements" ON public.distributor_settlements
    FOR ALL TO authenticated
    USING (COALESCE(public.auth_user_role()::TEXT, '') = 'Super_Admin')
    WITH CHECK (COALESCE(public.auth_user_role()::TEXT, '') = 'Super_Admin');

CREATE POLICY "Managers select settlements" ON public.distributor_settlements
    FOR SELECT TO authenticated
    USING (COALESCE(public.has_permission('settlement.view'), FALSE));

CREATE POLICY "Managers insert settlements" ON public.distributor_settlements
    FOR INSERT TO authenticated
    WITH CHECK (COALESCE(public.has_permission('settlement.create'), FALSE));

CREATE POLICY "Managers update pending settlements" ON public.distributor_settlements
    FOR UPDATE TO authenticated
    USING (status = 'Pending' AND COALESCE(public.has_permission('settlement.create'), FALSE))
    WITH CHECK (status = 'Pending' AND COALESCE(public.has_permission('settlement.create'), FALSE));

COMMIT;

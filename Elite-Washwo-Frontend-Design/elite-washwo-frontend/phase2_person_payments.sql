-- ==============================================================================
-- ELITE WASH ERP — PHASE 2 PRODUCTION MIGRATION SCRIPT
-- Version: 2.6 (Approval Security & Column Privilege Verification:
--               PostgreSQL Column-Level Grants, Safe SECURITY DEFINER RPCs,
--               Strict Expense Ownership, Mandatory Historical Reconciliation)
-- IDEMPOTENT & REPEATABLE: Transactional DDL ensures all-or-nothing execution
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 0. LOCAL POSTGRESQL COMPATIBILITY: Create Supabase roles if absent
--    In production Supabase these roles already exist. In local PostgreSQL
--    (for migration testing) they must be created before any GRANT/REVOKE.
--    DO block is idempotent — skips silently if roles already exist.
-- ------------------------------------------------------------------------------
DO $$
BEGIN
    -- Create 'authenticated' role (Supabase JWT role for logged-in users)
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN;
        RAISE NOTICE 'INFO: Created local role ''authenticated'' for testing.';
    END IF;

    -- Create 'anon' role (Supabase JWT role for unauthenticated requests)
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN;
        RAISE NOTICE 'INFO: Created local role ''anon'' for testing.';
    END IF;

    -- Create 'service_role' role (Supabase service key bypass)
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN;
        RAISE NOTICE 'INFO: Created local role ''service_role'' for testing.';
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- 1. UTILITY FUNCTIONS & UPDATED_AT TRIGGER
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

-- ------------------------------------------------------------------------------
-- 1b. AUTH SCHEMA COMPATIBILITY STUBS (Local PostgreSQL only)
--     In Supabase, auth.uid(), auth.jwt(), and the auth schema are provided
--     by the platform. In local PostgreSQL we must create stubs so that the
--     migration and SECURITY DEFINER functions can compile and run.
--     These stubs read JWT claims from the GUC variables that the test harness
--     sets via set_config('request.jwt.claim.sub', ...).
-- ------------------------------------------------------------------------------
DO $$
BEGIN
    -- Ensure auth schema exists
    CREATE SCHEMA IF NOT EXISTS auth;

    -- Ensure auth.users exists (minimal schema for FK resolution)
    CREATE TABLE IF NOT EXISTS auth.users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email TEXT
    );
END $$;

-- auth.uid(): Returns the UUID of the currently authenticated user.
-- Reads from the GUC set by the Supabase PostgREST middleware (or our test harness).
CREATE OR REPLACE FUNCTION auth.uid()
RETURNS UUID AS $$
    SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID;
$$ LANGUAGE SQL STABLE SET search_path = auth, public, pg_temp;

-- auth.jwt(): Returns the full JWT claims object.
CREATE OR REPLACE FUNCTION auth.jwt()
RETURNS JSONB AS $$
    SELECT NULLIF(current_setting('request.jwt.claims', true), '')::JSONB;
$$ LANGUAGE SQL STABLE SET search_path = auth, public, pg_temp;

-- auth_user_role(): Returns the role of the currently authenticated user.
-- Reads from public.profiles using auth.uid().
CREATE OR REPLACE FUNCTION public.auth_user_role()
RETURNS TEXT AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid();
$$ LANGUAGE SQL STABLE SECURITY DEFINER SET search_path = public, pg_temp;

-- has_permission(): Checks if the current user holds a specific permission.
CREATE OR REPLACE FUNCTION public.has_permission(p_permission_id TEXT)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.user_permissions
        WHERE user_id = auth.uid()
          AND permission_id = p_permission_id
    );
$$ LANGUAGE SQL STABLE SECURITY DEFINER SET search_path = public, pg_temp;

ALTER FUNCTION auth.uid() OWNER TO postgres;
ALTER FUNCTION auth.jwt() OWNER TO postgres;
ALTER FUNCTION public.auth_user_role() OWNER TO postgres;
ALTER FUNCTION public.has_permission(TEXT) OWNER TO postgres;


-- ------------------------------------------------------------------------------
-- 2. PERSON DIRECTORY TABLE
-- ------------------------------------------------------------------------------
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

-- Idempotent column safeguard for pre-existing or partially migrated tables
ALTER TABLE public.persons ADD COLUMN IF NOT EXISTS notes TEXT;

DROP TRIGGER IF EXISTS trg_persons_updated_at ON public.persons;
CREATE TRIGGER trg_persons_updated_at
    BEFORE UPDATE ON public.persons
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at_timestamp();

CREATE INDEX IF NOT EXISTS idx_persons_category ON public.persons(category);
CREATE INDEX IF NOT EXISTS idx_persons_active ON public.persons(is_active);

-- ------------------------------------------------------------------------------
-- 3. PERSON LEDGER ENTRIES TABLE (FINANCIAL INTEGRITY & APPROVALS)
-- ------------------------------------------------------------------------------
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
    entry_type TEXT NOT NULL CHECK (entry_type IN (
        'Opening_Balance', 'Work_Earning', 'Payment', 'Advance', 
        'Commission_Earned', 'Commission_Paid', 'Adjustment'
    )),
    direction TEXT CHECK (direction IN ('Payable', 'Receivable', 'Credit', 'Debit')),
    description TEXT NOT NULL,
    notes TEXT,
    quantity NUMERIC(12, 2) DEFAULT 0 CHECK (quantity >= 0),
    rate NUMERIC(12, 2) DEFAULT 0 CHECK (rate >= 0),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    payment_method TEXT CHECK (payment_method IN ('Cash', 'Bank', 'Cheque', 'Adjustment', 'N/A')),
    account_detail TEXT,
    tid TEXT,
    expense_id UUID REFERENCES public.expenses(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Cancelled')),
    created_by UUID REFERENCES public.profiles(id),
    approved_by UUID REFERENCES public.profiles(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Idempotent column safeguard for pre-existing or partially migrated tables
ALTER TABLE public.person_ledger_entries ADD COLUMN IF NOT EXISTS notes TEXT;

-- Safely recreate work earning validation constraint
ALTER TABLE public.person_ledger_entries DROP CONSTRAINT IF EXISTS chk_work_earning_calc;
ALTER TABLE public.person_ledger_entries ADD CONSTRAINT chk_work_earning_calc CHECK (
    entry_type != 'Work_Earning' OR
    quantity IS NULL OR quantity = 0 OR
    rate IS NULL OR rate = 0 OR
    ROUND(amount, 2) = ROUND(quantity * rate, 2)
);

DROP TRIGGER IF EXISTS trg_person_ledger_updated_at ON public.person_ledger_entries;
CREATE TRIGGER trg_person_ledger_updated_at
    BEFORE UPDATE ON public.person_ledger_entries
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at_timestamp();

CREATE INDEX IF NOT EXISTS idx_person_ledger_person ON public.person_ledger_entries(person_id);
CREATE INDEX IF NOT EXISTS idx_person_ledger_date ON public.person_ledger_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_person_ledger_status ON public.person_ledger_entries(status);

-- ------------------------------------------------------------------------------
-- 4. PERSON LEDGER IMMUTABILITY & RPC GATING TRIGGER
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_person_ledger_entry_workflow()
RETURNS TRIGGER AS $$
DECLARE
    v_caller_role TEXT;
    v_has_approve_perm BOOLEAN;
BEGIN
    -- [RULE 1]: Prevent direct insertion of Approved or Cancelled records
    IF OLD IS NULL THEN
        IF NEW.status != 'Pending' THEN
            RAISE EXCEPTION 'All newly created person ledger entries must start with status Pending. Direct insertion of Approved or Cancelled records is prohibited.';
        END IF;
    END IF;

    -- Validate Status Transitions
    IF OLD IS NOT NULL THEN
        -- Terminal state: Cancelled records can NEVER be modified or reopened
        IF OLD.status = 'Cancelled' THEN
            RAISE EXCEPTION 'Cancelled records are immutable and cannot be modified or reopened.';
        END IF;

        -- Approved entries can ONLY transition to Cancelled (Reversal workflow)
        IF OLD.status = 'Approved' AND NEW.status NOT IN ('Approved', 'Cancelled') THEN
            RAISE EXCEPTION 'Approved entries cannot transition to %.', NEW.status;
        END IF;

        -- Pending entries can only become Approved or Cancelled
        IF OLD.status = 'Pending' AND NEW.status NOT IN ('Pending', 'Approved', 'Cancelled') THEN
            RAISE EXCEPTION 'Invalid status transition from Pending to %.', NEW.status;
        END IF;
    END IF;

    -- Strict Immutability of Approved Entries
    IF OLD IS NOT NULL AND OLD.status = 'Approved' THEN
        IF (
            NEW.amount != OLD.amount OR
            NEW.person_id != OLD.person_id OR
            NEW.entry_type != OLD.entry_type OR
            NEW.direction IS DISTINCT FROM OLD.direction OR
            NEW.quantity != OLD.quantity OR
            NEW.rate != OLD.rate OR
            NEW.entry_date != OLD.entry_date OR
            NEW.payment_method IS DISTINCT FROM OLD.payment_method OR
            NEW.account_detail IS DISTINCT FROM OLD.account_detail OR
            NEW.tid IS DISTINCT FROM OLD.tid OR
            NEW.expense_id IS DISTINCT FROM OLD.expense_id OR
            NEW.created_by IS DISTINCT FROM OLD.created_by OR
            NEW.created_at != OLD.created_at
        ) THEN
            RAISE EXCEPTION 'Approved financial transactions are strictly immutable. Financial fields cannot be modified even when cancelling.';
        END IF;
    END IF;

    -- Strict Approval Authorization
    IF NEW.status = 'Approved' AND (OLD IS NULL OR OLD.status != 'Approved') THEN
        v_caller_role := public.auth_user_role();
        v_has_approve_perm := public.has_permission('payments.approve');
        
        IF COALESCE(v_caller_role, '') != 'Super_Admin' AND NOT COALESCE(v_has_approve_perm, FALSE) THEN
            RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized Managers with payments.approve permission can approve entries.';
        END IF;

        NEW.approved_at = COALESCE(NEW.approved_at, NOW());
        IF NEW.approved_by IS NULL THEN
            NEW.approved_by = auth.uid();
        END IF;
    END IF;

    -- [BLOCKING FIX 1]: Verified Expense Ownership Cancellation
    -- Only cancel an expense when originating_ledger_entry_id EXACTLY equals NEW.id
    -- Removed all fallback allowance for NULL originating_ledger_entry_id
    IF NEW.status = 'Cancelled' AND OLD IS NOT NULL AND OLD.status = 'Approved' THEN
        v_caller_role := public.auth_user_role();
        v_has_approve_perm := public.has_permission('payments.approve');
        
        IF COALESCE(v_caller_role, '') != 'Super_Admin' AND NOT COALESCE(v_has_approve_perm, FALSE) THEN
            RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized Managers with payments.approve permission can cancel approved entries.';
        END IF;

        IF NEW.expense_id IS NOT NULL THEN
            UPDATE public.expenses 
            SET status = 'Cancelled', description = description || ' [Reversed via Person Ledger: ' || NEW.reference_number || ']'
            WHERE id = NEW.expense_id 
              AND person_id = NEW.person_id
              AND originating_ledger_entry_id = NEW.id
              AND status != 'Cancelled';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_person_ledger_workflow ON public.person_ledger_entries;
CREATE TRIGGER trg_person_ledger_workflow
    BEFORE INSERT OR UPDATE ON public.person_ledger_entries
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_person_ledger_entry_workflow();

-- Prevent deletion of Approved entries
CREATE OR REPLACE FUNCTION public.prevent_approved_person_entry_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'Approved' THEN
        RAISE EXCEPTION 'Cannot delete approved transaction (%). Status must be Cancelled via authorized reversal.', OLD.reference_number;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_person_ledger_prevent_delete ON public.person_ledger_entries;
CREATE TRIGGER trg_person_ledger_prevent_delete
    BEFORE DELETE ON public.person_ledger_entries
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_approved_person_entry_delete();

-- ------------------------------------------------------------------------------
-- 5. REUSE EXPENSES MODULE: EXTEND WITH PERSON_ID & ORIGINATING OWNERSHIP
-- ------------------------------------------------------------------------------
ALTER TABLE public.expenses
ADD COLUMN IF NOT EXISTS person_id UUID REFERENCES public.persons(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS originating_ledger_entry_id UUID;

CREATE INDEX IF NOT EXISTS idx_expenses_person_id ON public.expenses(person_id);
CREATE INDEX IF NOT EXISTS idx_expenses_originating_entry ON public.expenses(originating_ledger_entry_id);

-- ------------------------------------------------------------------------------
-- 6. LEGACY COMPATIBILITY: DROP NOT NULL CONSTRAINTS
-- ------------------------------------------------------------------------------
ALTER TABLE public.sales_orders ALTER COLUMN salesman_id DROP NOT NULL;
ALTER TABLE public.sales_orders ALTER COLUMN customer_id DROP NOT NULL;
ALTER TABLE public.recoveries ALTER COLUMN salesman_id DROP NOT NULL;
ALTER TABLE public.recoveries ALTER COLUMN customer_id DROP NOT NULL;
ALTER TABLE public.inventory_transactions ALTER COLUMN salesman_id DROP NOT NULL;
ALTER TABLE public.expenses ALTER COLUMN salesman_id DROP NOT NULL;

-- Support distributor daily closing alongside legacy salesmen
ALTER TABLE public.daily_closings ADD COLUMN IF NOT EXISTS distributor_id UUID REFERENCES public.distributors(id) ON DELETE RESTRICT;
ALTER TABLE public.daily_closings ALTER COLUMN salesman_id DROP NOT NULL;
CREATE INDEX IF NOT EXISTS idx_daily_closings_distributor ON public.daily_closings(distributor_id);

-- Support distributor & tracking fields on expenses
ALTER TABLE public.expenses
ADD COLUMN IF NOT EXISTS distributor_id UUID REFERENCES public.distributors(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS head TEXT,
ADD COLUMN IF NOT EXISTS account_detail TEXT,
ADD COLUMN IF NOT EXISTS tid TEXT,
ADD COLUMN IF NOT EXISTS payment_method TEXT DEFAULT 'Cash';

CREATE INDEX IF NOT EXISTS idx_expenses_distributor ON public.expenses(distributor_id);

-- Support distributor assignment on inventory_transactions
ALTER TABLE public.inventory_transactions
ADD COLUMN IF NOT EXISTS distributor_id UUID REFERENCES public.distributors(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_inv_trans_distributor ON public.inventory_transactions(distributor_id);

-- Ensure recoveries payment_method allows 'Adjustment' for automated commission offsets
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    FOR r IN (
        SELECT conname 
        FROM pg_constraint 
        WHERE conrelid = 'public.recoveries'::regclass 
          AND contype = 'c' 
          AND pg_get_constraintdef(oid) LIKE '%payment_method%'
    ) LOOP
        EXECUTE 'ALTER TABLE public.recoveries DROP CONSTRAINT ' || quote_ident(r.conname);
    END LOOP;
END $$;

ALTER TABLE public.recoveries 
DROP CONSTRAINT IF EXISTS recoveries_payment_method_check;

ALTER TABLE public.recoveries 
ADD CONSTRAINT recoveries_payment_method_check 
CHECK (payment_method IN ('Cash', 'Bank', 'Cheque', 'Online', 'Adjustment', 'Other', 'N/A'));

-- ------------------------------------------------------------------------------
-- 7. DISTRIBUTOR SETTLEMENTS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.distributor_settlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_number TEXT NOT NULL UNIQUE,
    settlement_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    distributor_id UUID NOT NULL REFERENCES public.distributors(id) ON DELETE RESTRICT,
    settlement_type TEXT NOT NULL CHECK (settlement_type IN (
        'Commission_Cash_Paid', 
        'Commission_Bank_Paid', 
        'Commission_Against_Outstanding'
    )),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    payment_method TEXT CHECK (payment_method IN ('Cash', 'Bank', 'Cheque', 'Adjustment', 'N/A')),
    account_detail TEXT,
    tid TEXT,
    recovery_id UUID REFERENCES public.recoveries(id) ON DELETE SET NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Cancelled')),
    created_by UUID REFERENCES public.profiles(id),
    approved_by UUID REFERENCES public.profiles(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Idempotent column safeguard for pre-existing or partially migrated tables
ALTER TABLE public.distributor_settlements ADD COLUMN IF NOT EXISTS notes TEXT;

DROP TRIGGER IF EXISTS trg_distributor_settlements_updated_at ON public.distributor_settlements;
CREATE TRIGGER trg_distributor_settlements_updated_at
    BEFORE UPDATE ON public.distributor_settlements
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at_timestamp();

CREATE INDEX IF NOT EXISTS idx_dist_settlements_distributor ON public.distributor_settlements(distributor_id);
CREATE INDEX IF NOT EXISTS idx_dist_settlements_status ON public.distributor_settlements(status);
CREATE INDEX IF NOT EXISTS idx_dist_settlements_type ON public.distributor_settlements(settlement_type);

-- ------------------------------------------------------------------------------
-- 8. DISTRIBUTOR SETTLEMENT WORKFLOW, BOUNDS & ATOMIC RECOVERY TRIGGER
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_distributor_settlement_workflow()
RETURNS TRIGGER AS $$
DECLARE
    v_caller_role TEXT;
    v_has_approve_perm BOOLEAN;
    v_rec_id UUID;
    v_rec_ref TEXT;
    v_unreconciled_count INTEGER;
    v_accrued_comm NUMERIC;
    v_paid_comm NUMERIC;
    v_avail_comm NUMERIC;
    v_total_sales NUMERIC;
    v_total_recov NUMERIC;
    v_avail_out NUMERIC;
BEGIN
    -- [BLOCKING FIX 4]: Prevent direct insertion of Approved or Cancelled settlements
    IF OLD IS NULL THEN
        IF NEW.status != 'Pending' THEN
            RAISE EXCEPTION 'All newly created distributor settlements must start with status Pending. Direct insertion of Approved or Cancelled records is prohibited.';
        END IF;
    END IF;

    -- Reject all client-supplied recovery_id values on INSERT
    IF OLD IS NULL AND NEW.recovery_id IS NOT NULL THEN
        RAISE EXCEPTION 'Direct assignment of recovery_id is strictly prohibited. Linked recoveries can only be created by the database workflow.';
    END IF;

    IF OLD IS NOT NULL AND OLD.recovery_id IS NOT NULL AND NEW.recovery_id IS DISTINCT FROM OLD.recovery_id THEN
        RAISE EXCEPTION 'recovery_id is strictly immutable once linked to an offset recovery.';
    END IF;

    -- Validate Status Transitions
    IF OLD IS NOT NULL THEN
        IF OLD.status = 'Cancelled' THEN
            RAISE EXCEPTION 'Cancelled settlements are immutable and cannot be modified or reopened.';
        END IF;

        IF OLD.status = 'Approved' AND NEW.status NOT IN ('Approved', 'Cancelled') THEN
            RAISE EXCEPTION 'Approved settlements cannot transition to %.', NEW.status;
        END IF;

        IF OLD.status = 'Pending' AND NEW.status NOT IN ('Pending', 'Approved', 'Cancelled') THEN
            RAISE EXCEPTION 'Invalid status transition from Pending to %.', NEW.status;
        END IF;
    END IF;

    -- Strict Immutability of Approved Settlements
    IF OLD IS NOT NULL AND OLD.status = 'Approved' THEN
        IF (
            NEW.amount != OLD.amount OR
            NEW.distributor_id != OLD.distributor_id OR
            NEW.settlement_type != OLD.settlement_type OR
            NEW.settlement_date != OLD.settlement_date OR
            NEW.payment_method IS DISTINCT FROM OLD.payment_method OR
            NEW.account_detail IS DISTINCT FROM OLD.account_detail OR
            NEW.tid IS DISTINCT FROM OLD.tid OR
            NEW.recovery_id IS DISTINCT FROM OLD.recovery_id OR
            NEW.created_by IS DISTINCT FROM OLD.created_by OR
            NEW.created_at != OLD.created_at OR
            NEW.approved_by IS DISTINCT FROM OLD.approved_by OR
            NEW.approved_at IS DISTINCT FROM OLD.approved_at
        ) THEN
            RAISE EXCEPTION 'Approved settlements are strictly immutable. Financial and linking fields cannot be modified even when cancelling.';
        END IF;
    END IF;

    -- Strict Approval Authorization & Immutable Rate Snapshot Calculations
    IF NEW.status = 'Approved' AND (OLD IS NULL OR OLD.status != 'Approved') THEN
        v_caller_role := public.auth_user_role();
        v_has_approve_perm := public.has_permission('settlement.approve');
        
        IF COALESCE(v_caller_role, '') != 'Super_Admin' AND NOT COALESCE(v_has_approve_perm, FALSE) THEN
            RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized Managers with settlement.approve permission can approve settlements.';
        END IF;

        NEW.approved_at = COALESCE(NEW.approved_at, NOW());
        IF NEW.approved_by IS NULL THEN
            NEW.approved_by = auth.uid();
        END IF;

        -- Row lock distributor to prevent race conditions during concurrent approvals
        PERFORM id FROM public.distributors WHERE id = NEW.distributor_id FOR UPDATE;

        -- [BLOCKING FIX 3]: Check for historical sales orders with unverified NULL snapshots
        -- Do not treat NULL as zero. Block settlement approval if rate snapshots are missing.
        SELECT COUNT(*) INTO v_unreconciled_count
        FROM public.sales_orders so
        WHERE so.distributor_id = NEW.distributor_id 
          AND so.status IN ('Approved', 'Posted')
          AND so.commission_rate_snapshot IS NULL;

        IF v_unreconciled_count > 0 THEN
            RAISE EXCEPTION 'Cannot approve settlement: Distributor has % historical sales orders with unverified commission rates (NULL snapshot). Reconcile historical orders using reconcile_historical_sales_order_rates() before approving settlements.', v_unreconciled_count;
        END IF;

        -- Accrued commission calculated strictly from immutable sale-specific rate snapshots
        SELECT COALESCE(SUM(si.quantity * so.commission_rate_snapshot), 0)
        INTO v_accrued_comm
        FROM public.sale_items si
        JOIN public.sales_orders so ON so.id = si.sale_order_id
        WHERE so.distributor_id = NEW.distributor_id AND so.status IN ('Approved', 'Posted');

        -- Accrued settlements already approved
        SELECT COALESCE(SUM(amount), 0) INTO v_paid_comm
        FROM public.distributor_settlements
        WHERE distributor_id = NEW.distributor_id AND status = 'Approved' AND id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::UUID);

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
            WHERE distributor_id = NEW.distributor_id AND status IN ('Approved', 'Posted');

            v_avail_out := GREATEST(0, v_total_sales - v_total_recov);

            IF NEW.amount > v_avail_out THEN
                RAISE EXCEPTION 'Offset amount (Rs. %) exceeds available Sales Outstanding (Rs. %). Total Sales: Rs. %, Total Recovered: Rs. %',
                    NEW.amount, v_avail_out, v_total_sales, v_total_recov;
            END IF;

            -- Atomic creation of recovery
            IF NEW.recovery_id IS NULL THEN
                v_rec_ref := 'REC-SET-' || SUBSTRING(REPLACE(NEW.reference_number, '-', ''), 1, 10) || '-' || SUBSTRING(COALESCE(NEW.id::TEXT, gen_random_uuid()::TEXT), 1, 6);

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

    -- If settlement is Cancelled: check authorization and cancel paired recovery
    IF NEW.status = 'Cancelled' AND OLD IS NOT NULL AND OLD.status = 'Approved' THEN
        v_caller_role := public.auth_user_role();
        v_has_approve_perm := public.has_permission('settlement.approve');
        
        IF COALESCE(v_caller_role, '') != 'Super_Admin' AND NOT COALESCE(v_has_approve_perm, FALSE) THEN
            RAISE EXCEPTION 'Unauthorized: Only Super_Admin or authorized Managers with settlement.approve permission can cancel approved settlements.';
        END IF;

        IF NEW.recovery_id IS NOT NULL THEN
            UPDATE public.recoveries
            SET status = 'Cancelled', notes = notes || ' [Settlement Cancelled: ' || NEW.reference_number || ']'
            WHERE id = NEW.recovery_id AND status != 'Cancelled';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_distributor_settlement_workflow ON public.distributor_settlements;
CREATE TRIGGER trg_distributor_settlement_workflow
    BEFORE INSERT OR UPDATE ON public.distributor_settlements
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_distributor_settlement_workflow();

-- Prevent deletion of Approved settlements
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
-- 9. CONTROLLED SERVER-SIDE APPROVAL & CREATION FUNCTIONS (SECURITY DEFINER + SAFE SEARCH_PATH)
-- ------------------------------------------------------------------------------

-- Atomic Person Ledger Entry & Linked Expense Creation RPC
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
        v_caller_role := public.auth_user_role();
        v_has_approve_perm := public.has_permission('payments.approve');
        IF COALESCE(v_caller_role, '') = 'Super_Admin' OR COALESCE(v_has_approve_perm, FALSE) THEN
            v_status := 'Approved';
            v_approved_by := auth.uid();
            v_approved_at := NOW();
        ELSE
            v_status := 'Pending'; -- Fallback to Pending if caller lacks permission
        END IF;
    END IF;

    -- If linked expense requested, insert expense first with Pending status (or Approved if authorized auto-approve)
    IF p_create_expense AND p_entry_type IN ('Payment', 'Work_Earning', 'Advance') THEN
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
            payment_method,
            account_detail,
            tid,
            person_id,
            originating_ledger_entry_id,
            status,
            created_at,
            updated_at
        ) VALUES (
            v_expense_id,
            v_exp_ref,
            NOW(),
            'Company',
            COALESCE(v_person.category, 'Labour'),
            p_amount,
            REPLACE(p_entry_type, '_', ' ') || ' to ' || v_person.name || ': ' || p_description,
            COALESCE(p_payment_method, 'Cash'),
            COALESCE(p_account_detail, ''),
            COALESCE(p_tid, ''),
            p_person_id,
            v_entry_id,
            v_status,
            NOW(),
            NOW()
        );
    END IF;

    -- Insert person ledger entry
    INSERT INTO public.person_ledger_entries (
        id,
        reference_number,
        person_id,
        entry_date,
        entry_type,
        direction,
        description,
        notes,
        quantity,
        rate,
        amount,
        payment_method,
        account_detail,
        tid,
        expense_id,
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
        p_entry_type,
        p_direction,
        p_description,
        p_notes,
        COALESCE(p_quantity, 0),
        COALESCE(p_rate, 0),
        p_amount,
        COALESCE(p_payment_method, 'Cash'),
        COALESCE(p_account_detail, ''),
        COALESCE(p_tid, ''),
        v_expense_id,
        v_status,
        auth.uid(),
        v_approved_by,
        v_approved_at,
        NOW(),
        NOW()
    );

    RETURN jsonb_build_object(
        'success', true,
        'id', v_entry_id,
        'reference_number', v_entry_ref,
        'expense_id', v_expense_id,
        'status', v_status
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- Atomic Sales Order with Line Items Creation RPC
CREATE OR REPLACE FUNCTION public.create_sales_order_with_items(
    p_reference_number TEXT,
    p_distributor_id UUID,
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
    v_comm_rate NUMERIC(12, 2) := 30.00;
    v_adv_rate NUMERIC(12, 2) := 20.00;
    v_welf_rate NUMERIC(12, 2) := 10.00;
    v_item JSONB;
    v_pkg_id UUID;
    v_qty NUMERIC(12, 2);
    v_unit_price NUMERIC(12, 2);
    v_subtotal NUMERIC(12, 2);
    v_computed_total NUMERIC(12, 2) := 0;
BEGIN
    IF p_distributor_id IS NOT NULL THEN
        SELECT COALESCE(commission, 30.00) INTO v_comm_rate 
        FROM public.distributors WHERE id = p_distributor_id;
    END IF;

    -- Fetch rates from global_settings if present
    SELECT 
        COALESCE(advertisement_rate, 20.00),
        COALESCE(welfare_rate, 10.00)
    INTO v_adv_rate, v_welf_rate
    FROM public.global_settings LIMIT 1;

    -- Compute total from items
    IF jsonb_array_length(p_items) > 0 THEN
        FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
            v_qty := (v_item->>'quantity')::NUMERIC;
            v_unit_price := (v_item->>'price')::NUMERIC;
            IF v_unit_price IS NULL THEN
                v_unit_price := (v_item->>'unit_price')::NUMERIC;
            END IF;
            v_subtotal := COALESCE((v_item->>'subtotal')::NUMERIC, v_qty * v_unit_price);
            v_computed_total := v_computed_total + v_subtotal;
        END LOOP;
    ELSE
        v_computed_total := p_total_amount;
    END IF;

    -- Insert sales_orders header
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
        p_status,
        v_comm_rate,
        v_adv_rate,
        v_welf_rate,
        NOW(),
        NOW()
    );

    -- Insert line items
    IF jsonb_array_length(p_items) > 0 THEN
        FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
            v_pkg_id := (v_item->>'packagingId')::UUID;
            IF v_pkg_id IS NULL THEN
                v_pkg_id := (v_item->>'packaging_id')::UUID;
            END IF;
            v_qty := (v_item->>'quantity')::NUMERIC;
            v_unit_price := (v_item->>'price')::NUMERIC;
            IF v_unit_price IS NULL THEN
                v_unit_price := (v_item->>'unit_price')::NUMERIC;
            END IF;
            v_subtotal := COALESCE((v_item->>'subtotal')::NUMERIC, v_qty * v_unit_price);

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
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'id', v_order_id,
        'reference_number', p_reference_number,
        'total_amount', v_computed_total,
        'status', p_status
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

CREATE OR REPLACE FUNCTION public.approve_person_ledger_entry(p_entry_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_entry RECORD;
BEGIN
    IF COALESCE(public.auth_user_role(), '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('payments.approve'), FALSE) THEN
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

    -- Synchronized Expense Approval
    IF v_entry.expense_id IS NOT NULL THEN
        UPDATE public.expenses
        SET status = 'Approved', updated_at = NOW()
        WHERE id = v_entry.expense_id
          AND originating_ledger_entry_id = p_entry_id
          AND status != 'Approved';
    END IF;

    RETURN jsonb_build_object('success', true, 'id', p_entry_id, 'status', 'Approved');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

CREATE OR REPLACE FUNCTION public.cancel_person_ledger_entry(p_entry_id UUID, p_reason TEXT DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    v_entry RECORD;
BEGIN
    IF COALESCE(public.auth_user_role(), '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('payments.approve'), FALSE) THEN
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

    -- Synchronized Expense Cancellation (Only owned expense)
    IF v_entry.expense_id IS NOT NULL THEN
        UPDATE public.expenses 
        SET status = 'Cancelled', 
            description = description || ' [Reversed via Person Ledger: ' || v_entry.reference_number || ']',
            updated_at = NOW()
        WHERE id = v_entry.expense_id 
          AND person_id = v_entry.person_id
          AND originating_ledger_entry_id = p_entry_id
          AND status != 'Cancelled';
    END IF;

    RETURN jsonb_build_object('success', true, 'id', p_entry_id, 'status', 'Cancelled');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

CREATE OR REPLACE FUNCTION public.approve_distributor_settlement(p_settlement_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_settle RECORD;
BEGIN
    IF COALESCE(public.auth_user_role(), '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('settlement.approve'), FALSE) THEN
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

CREATE OR REPLACE FUNCTION public.cancel_distributor_settlement(p_settlement_id UUID, p_reason TEXT DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    v_settle RECORD;
BEGIN
    IF COALESCE(public.auth_user_role(), '') != 'Super_Admin' AND NOT COALESCE(public.has_permission('settlement.approve'), FALSE) THEN
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

-- Function Ownership & Minimal EXECUTE Grants
ALTER FUNCTION public.set_updated_at_timestamp() OWNER TO postgres;
ALTER FUNCTION public.handle_person_ledger_entry_workflow() OWNER TO postgres;
ALTER FUNCTION public.prevent_approved_person_entry_delete() OWNER TO postgres;
ALTER FUNCTION public.handle_distributor_settlement_workflow() OWNER TO postgres;
ALTER FUNCTION public.prevent_approved_settlement_delete() OWNER TO postgres;
ALTER FUNCTION public.create_person_ledger_entry_with_expense(UUID, TEXT, TEXT, NUMERIC, TEXT, NUMERIC, NUMERIC, TEXT, TEXT, TEXT, TEXT, BOOLEAN, BOOLEAN) OWNER TO postgres;
ALTER FUNCTION public.create_sales_order_with_items(TEXT, UUID, UUID, UUID, NUMERIC, TIMESTAMPTZ, TEXT, JSONB) OWNER TO postgres;
ALTER FUNCTION public.approve_person_ledger_entry(UUID) OWNER TO postgres;
ALTER FUNCTION public.cancel_person_ledger_entry(UUID, TEXT) OWNER TO postgres;
ALTER FUNCTION public.approve_distributor_settlement(UUID) OWNER TO postgres;
ALTER FUNCTION public.cancel_distributor_settlement(UUID, TEXT) OWNER TO postgres;

REVOKE ALL ON FUNCTION public.create_person_ledger_entry_with_expense(UUID, TEXT, TEXT, NUMERIC, TEXT, NUMERIC, NUMERIC, TEXT, TEXT, TEXT, TEXT, BOOLEAN, BOOLEAN) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.create_person_ledger_entry_with_expense(UUID, TEXT, TEXT, NUMERIC, TEXT, NUMERIC, NUMERIC, TEXT, TEXT, TEXT, TEXT, BOOLEAN, BOOLEAN) TO authenticated;

REVOKE ALL ON FUNCTION public.create_sales_order_with_items(TEXT, UUID, UUID, UUID, NUMERIC, TIMESTAMPTZ, TEXT, JSONB) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.create_sales_order_with_items(TEXT, UUID, UUID, UUID, NUMERIC, TIMESTAMPTZ, TEXT, JSONB) TO authenticated;

REVOKE ALL ON FUNCTION public.approve_person_ledger_entry(UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.approve_person_ledger_entry(UUID) TO authenticated;

REVOKE ALL ON FUNCTION public.cancel_person_ledger_entry(UUID, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.cancel_person_ledger_entry(UUID, TEXT) TO authenticated;

REVOKE ALL ON FUNCTION public.approve_distributor_settlement(UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.approve_distributor_settlement(UUID) TO authenticated;

REVOKE ALL ON FUNCTION public.cancel_distributor_settlement(UUID, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.cancel_distributor_settlement(UUID, TEXT) TO authenticated;

-- ------------------------------------------------------------------------------
-- 10. HISTORICAL RATE SNAPSHOTS & RECONCILIATION SUPPORT
-- ------------------------------------------------------------------------------
ALTER TABLE public.sales_orders
ADD COLUMN IF NOT EXISTS commission_rate_snapshot NUMERIC(12, 2),
ADD COLUMN IF NOT EXISTS advertisement_rate_snapshot NUMERIC(12, 2),
ADD COLUMN IF NOT EXISTS welfare_rate_snapshot NUMERIC(12, 2);

-- Historical reconciliation procedure for Super Admin to explicitly verify unknown rates
CREATE OR REPLACE FUNCTION public.reconcile_historical_sales_order_rates(
    p_order_id UUID,
    p_commission_rate NUMERIC(12, 2),
    p_advertisement_rate NUMERIC(12, 2),
    p_welfare_rate NUMERIC(12, 2)
)
RETURNS JSONB AS $$
BEGIN
    IF COALESCE(public.auth_user_role(), '') != 'Super_Admin' THEN
        RAISE EXCEPTION 'Unauthorized: Only Super_Admin can reconcile historical sales order rates.';
    END IF;

    UPDATE public.sales_orders
    SET commission_rate_snapshot = p_commission_rate,
        advertisement_rate_snapshot = p_advertisement_rate,
        welfare_rate_snapshot = p_welfare_rate
    WHERE id = p_order_id AND commission_rate_snapshot IS NULL;

    RETURN jsonb_build_object('success', true, 'id', p_order_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

ALTER FUNCTION public.reconcile_historical_sales_order_rates(UUID, NUMERIC, NUMERIC, NUMERIC) OWNER TO postgres;
REVOKE ALL ON FUNCTION public.reconcile_historical_sales_order_rates(UUID, NUMERIC, NUMERIC, NUMERIC) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.reconcile_historical_sales_order_rates(UUID, NUMERIC, NUMERIC, NUMERIC) TO authenticated;

-- Unreconciled orders view for Super Admin auditing
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

-- ------------------------------------------------------------------------------
-- 11. SEED PERMISSIONS IN MASTER TABLE ONLY
-- ------------------------------------------------------------------------------
INSERT INTO public.permissions (id, module, description) VALUES
('payments.view',    'Payments',   'View person directory and financial ledgers'),
('payments.create',  'Payments',   'Record work earnings and payments'),
('payments.edit',    'Payments',   'Edit pending person directory and ledger entries'),
('payments.approve', 'Payments',   'Approve pending person payment entries'),
('payments.export',  'Payments',   'Export person statements and ledgers'),
('settlement.view',   'Settlement', 'View distributor settlement records'),
('settlement.create', 'Settlement', 'Create distributor commission settlement entries'),
('settlement.approve','Settlement', 'Approve distributor commission settlements')
ON CONFLICT (id) DO NOTHING;

-- ------------------------------------------------------------------------------
-- 12. GRANULAR ROW LEVEL SECURITY (RLS) POLICIES & COLUMN PRIVILEGES
-- ------------------------------------------------------------------------------
ALTER TABLE public.persons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.person_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.distributor_settlements ENABLE ROW LEVEL SECURITY;

-- 1. Revoke ALL table-level access from anon and PUBLIC
REVOKE ALL ON TABLE public.person_ledger_entries FROM PUBLIC, anon;
REVOKE ALL ON TABLE public.distributor_settlements FROM PUBLIC, anon;
REVOKE ALL ON TABLE public.persons FROM PUBLIC, anon;

-- 2. Revoke direct table-level UPDATE and DELETE from authenticated
REVOKE UPDATE, DELETE ON TABLE public.person_ledger_entries FROM authenticated;
REVOKE UPDATE, DELETE ON TABLE public.distributor_settlements FROM authenticated;

-- 3. Grant table-level SELECT and INSERT to authenticated
GRANT SELECT, INSERT ON TABLE public.person_ledger_entries TO authenticated;
GRANT SELECT, INSERT ON TABLE public.distributor_settlements TO authenticated;
GRANT SELECT, INSERT, UPDATE ON TABLE public.persons TO authenticated;

-- 4. Grant column-level UPDATE ONLY on non-sensitive, editable operational columns
-- Excludes status, approved_by, approved_at, reference_number, created_by, created_at, id
GRANT UPDATE (
    person_id, entry_type, direction, amount, quantity, rate,
    entry_date, payment_method, account_detail, tid, description, notes, expense_id
) ON TABLE public.person_ledger_entries TO authenticated;

-- Excludes status, approved_by, approved_at, recovery_id, reference_number, created_by, created_at, id
GRANT UPDATE (
    settlement_type, distributor_id, settlement_date, amount,
    payment_method, account_detail, tid, notes
) ON TABLE public.distributor_settlements TO authenticated;

-- Clean existing policies for idempotency
DROP POLICY IF EXISTS "Admins manage persons" ON public.persons;
DROP POLICY IF EXISTS "Admins full access persons" ON public.persons;
DROP POLICY IF EXISTS "Managers view persons" ON public.persons;
DROP POLICY IF EXISTS "Managers manage persons" ON public.persons;
DROP POLICY IF EXISTS "Managers create persons" ON public.persons;
DROP POLICY IF EXISTS "Managers update persons" ON public.persons;
DROP POLICY IF EXISTS "Managers select persons" ON public.persons;

-- A. PERSONS POLICIES
CREATE POLICY "Admins full access persons" ON public.persons
    FOR ALL TO authenticated
    USING (COALESCE(public.auth_user_role(), '') = 'Super_Admin')
    WITH CHECK (COALESCE(public.auth_user_role(), '') = 'Super_Admin');

CREATE POLICY "Managers select persons" ON public.persons
    FOR SELECT TO authenticated
    USING (public.has_permission('payments.view'));

CREATE POLICY "Managers insert persons" ON public.persons
    FOR INSERT TO authenticated
    WITH CHECK (public.has_permission('payments.create'));

CREATE POLICY "Managers update persons" ON public.persons
    FOR UPDATE TO authenticated
    USING (public.has_permission('payments.edit'))
    WITH CHECK (public.has_permission('payments.edit'));

-- B. PERSON LEDGER ENTRIES POLICIES
DROP POLICY IF EXISTS "Admins manage person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Admins full access person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Managers view person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Managers insert person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Managers update person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Managers approve person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Managers select person entries" ON public.person_ledger_entries;
DROP POLICY IF EXISTS "Managers update pending person entries" ON public.person_ledger_entries;

CREATE POLICY "Admins full access person entries" ON public.person_ledger_entries
    FOR ALL TO authenticated
    USING (COALESCE(public.auth_user_role(), '') = 'Super_Admin')
    WITH CHECK (COALESCE(public.auth_user_role(), '') = 'Super_Admin');

CREATE POLICY "Managers select person entries" ON public.person_ledger_entries
    FOR SELECT TO authenticated
    USING (public.has_permission('payments.view'));

CREATE POLICY "Managers insert person entries" ON public.person_ledger_entries
    FOR INSERT TO authenticated
    WITH CHECK (public.has_permission('payments.create'));

-- Managers can ONLY update non-status fields on Pending entries for correction
CREATE POLICY "Managers update pending person entries" ON public.person_ledger_entries
    FOR UPDATE TO authenticated
    USING (status = 'Pending' AND public.has_permission('payments.edit'))
    WITH CHECK (status = 'Pending' AND public.has_permission('payments.edit'));

-- C. DISTRIBUTOR SETTLEMENTS POLICIES
DROP POLICY IF EXISTS "Admins manage settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Admins full access settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Managers view settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Managers create settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Managers update settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Managers approve settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Managers select settlements" ON public.distributor_settlements;
DROP POLICY IF EXISTS "Managers update pending settlements" ON public.distributor_settlements;

CREATE POLICY "Admins full access settlements" ON public.distributor_settlements
    FOR ALL TO authenticated
    USING (COALESCE(public.auth_user_role(), '') = 'Super_Admin')
    WITH CHECK (COALESCE(public.auth_user_role(), '') = 'Super_Admin');

CREATE POLICY "Managers select settlements" ON public.distributor_settlements
    FOR SELECT TO authenticated
    USING (public.has_permission('settlement.view'));

CREATE POLICY "Managers insert settlements" ON public.distributor_settlements
    FOR INSERT TO authenticated
    WITH CHECK (public.has_permission('settlement.create'));

CREATE POLICY "Managers update pending settlements" ON public.distributor_settlements
    FOR UPDATE TO authenticated
    USING (status = 'Pending' AND public.has_permission('settlement.create'))
    WITH CHECK (status = 'Pending' AND public.has_permission('settlement.create'));

-- ------------------------------------------------------------------------------
-- 13. INVENTORY & EXPENSES RLS POLICIES FOR NULL SALESMAN_ID (DISTRIBUTOR OPERATIONS)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Allow Admins and Managers to insert inventory" ON public.inventory_transactions;
CREATE POLICY "Allow Admins and Managers to insert inventory" 
ON public.inventory_transactions 
FOR INSERT TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.profiles
    WHERE profiles.id = auth.uid()
    AND profiles.role IN ('Super_Admin', 'Manager')
  )
);

DROP POLICY IF EXISTS "Allow Admins and Managers to insert expenses" ON public.expenses;
CREATE POLICY "Allow Admins and Managers to insert expenses" 
ON public.expenses 
FOR INSERT TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.profiles
    WHERE profiles.id = auth.uid()
    AND profiles.role IN ('Super_Admin', 'Manager')
  )
);

COMMIT;

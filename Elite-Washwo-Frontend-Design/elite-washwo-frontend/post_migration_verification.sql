-- ==============================================================================
-- ELITE WASHWO ERP — POST-MIGRATION VERIFICATION SCRIPT v3.0
-- Target: Supabase PostgreSQL 17.6 Production Instance
-- SAFETY: Purely read-only inspection. Enclosed in BEGIN ... ROLLBACK.
--
-- Run AFTER production_phase2_migration.sql v3.0 has been applied.
-- Execute via Supabase SQL Editor → output appears in NOTICE messages.
--
-- Each check is classified:
--   [SI]  Static Inspection   — reads system catalogue / pg_proc source
--   [DV]  Data Verification   — reads live table row counts / column values
-- ==============================================================================

BEGIN;

DO $$
DECLARE
    v_all_passed                   BOOLEAN := TRUE;

    -- ── Table existence ────────────────────────────────────────────────────
    v_missing_tables               TEXT[] := ARRAY[]::TEXT[];
    v_expected_tables              TEXT[] := ARRAY[
        'profiles', 'salesmen', 'customers', 'products', 'product_packaging',
        'product_prices', 'inventory_transactions', 'sales_orders', 'sale_items',
        'recoveries', 'expenses', 'daily_closings', 'variances', 'audit_logs',
        'permissions', 'user_permissions', 'distributors', 'global_settings',
        'persons', 'person_ledger_entries', 'distributor_settlements'
    ];
    v_tbl                          TEXT;

    -- ── Nullability ────────────────────────────────────────────────────────
    v_so_sm_null                   TEXT;
    v_so_cust_null                 TEXT;
    v_rec_sm_null                  TEXT;
    v_rec_cust_null                TEXT;
    v_exp_sm_null                  TEXT;

    -- ── Phase 2 added columns ──────────────────────────────────────────────
    v_has_so_dist                  BOOLEAN;
    v_has_so_comm_snap             BOOLEAN;
    v_has_so_adv_snap              BOOLEAN;
    v_has_so_welf_snap             BOOLEAN;
    v_has_rec_dist                 BOOLEAN;
    v_has_exp_dist                 BOOLEAN;
    v_has_exp_person               BOOLEAN;
    v_has_exp_orig                 BOOLEAN;
    v_has_inv_dist                 BOOLEAN;
    v_has_gs_adv_rate              BOOLEAN;
    v_has_gs_welf_rate             BOOLEAN;
    v_has_si_created_at            BOOLEAN;
    v_has_si_updated_at            BOOLEAN;

    -- ── Global settings rate values ────────────────────────────────────────
    v_gs_adv                       NUMERIC;
    v_gs_welf                      NUMERIC;

    -- ── Historical data counts ─────────────────────────────────────────────
    v_sales_count                  INT;
    v_recs_count                   INT;
    v_exp_count                    INT;
    v_dist_count                   INT;
    v_null_dist_sales              INT;
    v_null_dist_recs               INT;

    -- ── v3.0 Defect-specific checks ────────────────────────────────────────
    v_constraint_def               TEXT;
    v_constraint_valid             BOOLEAN := FALSE;
    v_role_fn_return_type          TEXT;
    v_fn_source                    TEXT;
    v_commission_default_correct   BOOLEAN := FALSE;
    v_no_bad_default               BOOLEAN := TRUE;
    v_sales_fn_pending_first       BOOLEAN := FALSE;
    v_rec_fn_src                   TEXT;
    v_sales_fn_reconcile_safe      BOOLEAN := FALSE;
    v_person_fn_src                TEXT;
    v_person_trigger_safe          BOOLEAN := FALSE;
    v_settlement_fn_src            TEXT;
    v_settlement_trigger_safe      BOOLEAN := FALSE;
    v_person_cancel_ownership      BOOLEAN := FALSE;

    -- New v3.0 check variables
    v_sale_items_fn_src            TEXT;
    v_sale_items_tgop_safe         BOOLEAN := FALSE;
    v_expense_double_count_safe    BOOLEAN := FALSE;
    v_sales_auth_safe              BOOLEAN := FALSE;
    v_reconcile_audit_safe         BOOLEAN := FALSE;
    v_settle_insert_pending        BOOLEAN := FALSE;

    -- ── RPC functions ──────────────────────────────────────────────────────
    v_missing_functions            TEXT[] := ARRAY[]::TEXT[];
    v_fn                           TEXT;
    v_expected_fns                 TEXT[] := ARRAY[
        'create_sales_order_with_items',
        'create_person_ledger_entry_with_expense',
        'approve_person_ledger_entry',
        'cancel_person_ledger_entry',
        'approve_distributor_settlement',
        'cancel_distributor_settlement',
        'reconcile_historical_sales_order_rates'
    ];

    -- ── Triggers ───────────────────────────────────────────────────────────
    v_missing_triggers             TEXT[] := ARRAY[]::TEXT[];
    v_trg                          TEXT;
    v_expected_triggers            TEXT[] := ARRAY[
        'trg_person_ledger_workflow',
        'trg_distributor_settlement_workflow',
        'trg_sales_order_immutability',
        'trg_sale_items_immutability',
        'trg_recovery_immutability',
        'trg_expense_immutability',
        'trg_sales_order_prevent_delete',
        'trg_recovery_prevent_delete',
        'trg_expense_prevent_delete',
        'trg_person_ledger_prevent_delete',
        'trg_distributor_settlement_prevent_delete'
    ];
    v_has_perm_argname             TEXT;
    v_settle_tgtype                SMALLINT;
    v_person_tgtype                SMALLINT;
    v_so_trg_tgtype                SMALLINT;

    -- ── Views & Security ───────────────────────────────────────────────────
    v_unreconciled_count           INT := 0;
    v_e2_passed                    BOOLEAN;
    v_unsafe_fns                   TEXT[];

    -- ── Financial Spot-Checks ──────────────────────────────────────────────
    v_bad_settlements              INT;
    v_bad_entries                  INT;
    v_orders_with_snaps            INT;
    v_orders_null_snaps            INT;
    v_adj_recoveries               INT;

BEGIN
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  ELITE WASHWO ERP — POST-MIGRATION VERIFICATION SUITE v3.0';
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '';

    -- ══════════════════════════════════════════════════════════════════════
    -- SECTION A: SCHEMA COMPLETENESS
    -- ══════════════════════════════════════════════════════════════════════
    RAISE NOTICE '── Section A: Schema Completeness ─────────────────────────────────────────';

    -- ── A-1 [SI]: All 21 tables exist ─────────────────────────────────────
    FOREACH v_tbl IN ARRAY v_expected_tables LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = v_tbl
        ) THEN
            v_missing_tables := array_append(v_missing_tables, v_tbl);
        END IF;
    END LOOP;

    IF array_length(v_missing_tables, 1) IS NULL THEN
        RAISE NOTICE '[PASS] A-1 [SI] All 21 public tables present.';
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] A-1 [SI] Missing tables: %', v_missing_tables;
    END IF;

    -- ── A-2 [SI]: Nullability — salesman_id & customer_id allow NULL ───────
    SELECT is_nullable INTO v_so_sm_null   FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'sales_orders'  AND column_name = 'salesman_id';
    SELECT is_nullable INTO v_so_cust_null FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'sales_orders'  AND column_name = 'customer_id';
    SELECT is_nullable INTO v_rec_sm_null  FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'recoveries'    AND column_name = 'salesman_id';
    SELECT is_nullable INTO v_rec_cust_null FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'recoveries'   AND column_name = 'customer_id';
    SELECT is_nullable INTO v_exp_sm_null  FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'expenses'      AND column_name = 'salesman_id';

    IF v_so_sm_null = 'YES' AND v_so_cust_null = 'YES'
       AND v_rec_sm_null = 'YES' AND v_rec_cust_null = 'YES'
       AND v_exp_sm_null = 'YES'
    THEN
        RAISE NOTICE '[PASS] A-2 [SI] salesman_id & customer_id are nullable on sales_orders, recoveries, and expenses.';
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] A-2 [SI] Nullability mismatch. so_sm=%, so_cust=%, rec_sm=%, rec_cust=%, exp_sm=%',
            v_so_sm_null, v_so_cust_null, v_rec_sm_null, v_rec_cust_null, v_exp_sm_null;
    END IF;

    -- ── A-3 [SI]: Phase 2 columns on existing tables ───────────────────────
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sales_orders'           AND column_name='distributor_id')            INTO v_has_so_dist;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sales_orders'           AND column_name='commission_rate_snapshot')   INTO v_has_so_comm_snap;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sales_orders'           AND column_name='advertisement_rate_snapshot') INTO v_has_so_adv_snap;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sales_orders'           AND column_name='welfare_rate_snapshot')       INTO v_has_so_welf_snap;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='recoveries'             AND column_name='distributor_id')              INTO v_has_rec_dist;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='expenses'               AND column_name='distributor_id')              INTO v_has_exp_dist;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='expenses'               AND column_name='person_id')                   INTO v_has_exp_person;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='expenses'               AND column_name='originating_ledger_entry_id') INTO v_has_exp_orig;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='inventory_transactions' AND column_name='distributor_id')              INTO v_has_inv_dist;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='global_settings'        AND column_name='advertisement_rate')          INTO v_has_gs_adv_rate;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='global_settings'        AND column_name='welfare_rate')                INTO v_has_gs_welf_rate;

    IF v_has_so_dist AND v_has_so_comm_snap AND v_has_so_adv_snap AND v_has_so_welf_snap
       AND v_has_rec_dist AND v_has_exp_dist AND v_has_exp_person AND v_has_exp_orig
       AND v_has_inv_dist AND v_has_gs_adv_rate AND v_has_gs_welf_rate
    THEN
        RAISE NOTICE '[PASS] A-3 [SI] All Phase 2 columns on existing tables verified.';
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] A-3 [SI] Missing columns. so_dist=%, comm_snap=%, adv_snap=%, welf_snap=%, gs_adv=%, gs_welf=%',
            v_has_so_dist, v_has_so_comm_snap, v_has_so_adv_snap, v_has_so_welf_snap, v_has_gs_adv_rate, v_has_gs_welf_rate;
    END IF;

    -- ── A-4 [SI]: sale_items has created_at / updated_at ───────────────────
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sale_items' AND column_name='created_at') INTO v_has_si_created_at;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sale_items' AND column_name='updated_at') INTO v_has_si_updated_at;

    IF v_has_si_created_at AND v_has_si_updated_at THEN
        RAISE NOTICE '[PASS] A-4 [SI] sale_items has created_at and updated_at audit columns.';
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] A-4 [SI] sale_items is missing audit timestamp columns. created_at=%, updated_at=%',
            v_has_si_created_at, v_has_si_updated_at;
    END IF;

    -- ── A-5 [DV]: global_settings rates populated ─────────────────────────
    IF v_has_gs_adv_rate AND v_has_gs_welf_rate THEN
        EXECUTE 'SELECT advertisement_rate, welfare_rate FROM public.global_settings ORDER BY id LIMIT 1'
        INTO v_gs_adv, v_gs_welf;

        IF v_gs_adv IS NOT NULL AND v_gs_welf IS NOT NULL THEN
            RAISE NOTICE '[PASS] A-5 [DV] global_settings rates populated. advertisement_rate=%, welfare_rate=%', v_gs_adv, v_gs_welf;
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] A-5 [DV] global_settings rates are NULL after migration. advertisement_rate=%, welfare_rate=%', v_gs_adv, v_gs_welf;
        END IF;
    ELSE
        RAISE NOTICE '[SKIP] A-5 [DV] Skipped — global_settings rate columns absent (caught by A-3).';
    END IF;

    -- ══════════════════════════════════════════════════════════════════════
    -- SECTION B: DATA PRESERVATION
    -- ══════════════════════════════════════════════════════════════════════
    RAISE NOTICE '';
    RAISE NOTICE '── Section B: Data Preservation ───────────────────────────────────────────';

    -- ── B-1 [DV]: Historical record counts not dropped ─────────────────────
    SELECT COUNT(*) INTO v_sales_count FROM public.sales_orders;
    SELECT COUNT(*) INTO v_recs_count  FROM public.recoveries;
    SELECT COUNT(*) INTO v_exp_count   FROM public.expenses;
    SELECT COUNT(*) INTO v_dist_count  FROM public.distributors;

    IF v_has_so_dist THEN
        EXECUTE 'SELECT COUNT(*) FROM public.sales_orders WHERE distributor_id IS NULL' INTO v_null_dist_sales;
    ELSE
        v_null_dist_sales := NULL;
    END IF;

    IF v_has_rec_dist THEN
        EXECUTE 'SELECT COUNT(*) FROM public.recoveries WHERE distributor_id IS NULL' INTO v_null_dist_recs;
    ELSE
        v_null_dist_recs := NULL;
    END IF;

    IF v_sales_count >= 19 AND v_recs_count >= 6 AND v_exp_count >= 11 AND v_dist_count >= 3 THEN
        RAISE NOTICE '[PASS] B-1 [DV] Historical records preserved. Sales: %, Recoveries: %, Expenses: %, Distributors: %',
            v_sales_count, v_recs_count, v_exp_count, v_dist_count;
        RAISE NOTICE '       Records with NULL distributor_id — Sales: %, Recoveries: % (preserved, not auto-assigned).',
            COALESCE(v_null_dist_sales::TEXT, 'n/a — column absent'),
            COALESCE(v_null_dist_recs::TEXT,  'n/a — column absent');
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] B-1 [DV] Record count below minimum. Sales: %, Recoveries: %, Expenses: %, Distributors: %',
            v_sales_count, v_recs_count, v_exp_count, v_dist_count;
    END IF;

    -- ══════════════════════════════════════════════════════════════════════
    -- SECTION C: v3.0 DEFECT-SPECIFIC CHECKS
    -- ══════════════════════════════════════════════════════════════════════
    RAISE NOTICE '';
    RAISE NOTICE '── Section C: v3.0 Defect-Specific Checks ─────────────────────────────────';

    -- ── C-1 [SI]: chk_payment_method includes 'Adjustment' & preserves legacy methods ──
    SELECT pg_get_constraintdef(c.oid)
    INTO v_constraint_def
    FROM pg_constraint c
    JOIN pg_class t      ON t.oid = c.conrelid
    JOIN pg_namespace n  ON n.oid = t.relnamespace
    WHERE n.nspname = 'public'
      AND t.relname  = 'recoveries'
      AND c.conname  = 'chk_payment_method'
      AND c.contype  = 'c';

    IF v_constraint_def IS NOT NULL THEN
        v_constraint_valid := (
            v_constraint_def ILIKE '%Adjustment%'
            AND v_constraint_def ILIKE '%Cash%'
            AND v_constraint_def ILIKE '%Bank%'
            AND v_constraint_def ILIKE '%Cheque%'
        );
        IF v_constraint_valid THEN
            RAISE NOTICE '[PASS] C-1 [SI] chk_payment_method correctly allows Cash, Bank, Cheque, and Adjustment. Definition: %', v_constraint_def;
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-1 [SI] chk_payment_method definition incomplete or invalid: %', v_constraint_def;
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-1 [SI] Constraint chk_payment_method not found on recoveries table.';
    END IF;

    -- ── C-2 [SI]: auth_user_role() returns public.user_role enum, not TEXT ──
    SELECT pt.typname
    INTO v_role_fn_return_type
    FROM pg_proc p
    JOIN pg_namespace fn ON fn.oid = p.pronamespace
    JOIN pg_type pt      ON pt.oid = p.prorettype
    WHERE fn.nspname = 'public' AND p.proname = 'auth_user_role'
    LIMIT 1;

    IF v_role_fn_return_type = 'user_role' THEN
        RAISE NOTICE '[PASS] C-2 [SI] auth_user_role() returns public.user_role (enum), not TEXT.';
    ELSIF v_role_fn_return_type IS NULL THEN
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-2 [SI] auth_user_role() function not found in public schema.';
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-2 [SI] auth_user_role() return type is ''%'' — expected ''user_role'' enum.',
            v_role_fn_return_type;
    END IF;

    -- ── C-3 [SI]: Default commission is Rs. 30, not Rs. 35 ────
    SELECT p.prosrc
    INTO v_fn_source
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'create_sales_order_with_items'
    LIMIT 1;

    IF v_fn_source IS NOT NULL THEN
        v_commission_default_correct := (
            v_fn_source ILIKE '%v_comm_rate%30.00%'
            OR v_fn_source ILIKE '%commission%30.00%'
        );
        v_no_bad_default := NOT (v_fn_source ILIKE '%35.00%');

        IF v_commission_default_correct AND v_no_bad_default THEN
            RAISE NOTICE '[PASS] C-3 [SI] create_sales_order_with_items defaults commission to Rs. 30.00, not 35.00.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-3 [SI] Commission default mismatch. found_30=%, no_35=%',
                v_commission_default_correct, v_no_bad_default;
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-3 [SI] create_sales_order_with_items function not found.';
    END IF;

    -- ── C-4 [SI]: Sales order created Pending-first, then items, then transitioned ──
    IF v_fn_source IS NOT NULL THEN
        v_sales_fn_pending_first := (
            v_fn_source ILIKE '%Pending%'
            AND v_fn_source ILIKE '%INSERT INTO public.sale_items%'
            AND v_fn_source ILIKE '%UPDATE public.sales_orders%'
            AND v_fn_source ILIKE '%SET status = p_status%'
            AND POSITION('Pending' IN v_fn_source) < POSITION('INSERT INTO public.sale_items' IN v_fn_source)
            AND POSITION('INSERT INTO public.sale_items' IN v_fn_source) < POSITION('UPDATE public.sales_orders' IN v_fn_source)
        );
        IF v_sales_fn_pending_first THEN
            RAISE NOTICE '[PASS] C-4 [SI] create_sales_order_with_items uses atomic sequence: Header Pending -> Sale Items -> Final Status.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-4 [SI] create_sales_order_with_items does not follow atomic Pending-first insertion order.';
        END IF;
    ELSE
        RAISE NOTICE '[SKIP] C-4 [SI] Skipped — function source unavailable (caught in C-3).';
    END IF;

    -- ── C-5 [SI]: Reconciliation allows only NULL→value, gated on Super_Admin ──
    SELECT p.prosrc
    INTO v_rec_fn_src
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'handle_sales_order_immutability'
    LIMIT 1;

    IF v_rec_fn_src IS NOT NULL THEN
        v_sales_fn_reconcile_safe := (
            v_rec_fn_src ILIKE '%OLD.commission_rate_snapshot IS NULL%'
            AND v_rec_fn_src ILIKE '%Super_Admin%'
            AND v_rec_fn_src ILIKE '%v_is_reconciling%'
        );
        IF v_sales_fn_reconcile_safe THEN
            RAISE NOTICE '[PASS] C-5 [SI] Reconciliation is NULL→value only, gated on Super_Admin.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-5 [SI] handle_sales_order_immutability does not correctly gate reconciliation to NULL snapshots only.';
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-5 [SI] handle_sales_order_immutability trigger function not found.';
    END IF;

    -- ── C-6 [SI]: Person ledger trigger uses TG_OP guards (no raw OLD on INSERT) ──
    SELECT p.prosrc
    INTO v_person_fn_src
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'handle_person_ledger_entry_workflow'
    LIMIT 1;

    IF v_person_fn_src IS NOT NULL THEN
        v_person_trigger_safe := (
            v_person_fn_src ILIKE '%TG_OP = ''INSERT''%'
            AND v_person_fn_src ILIKE '%TG_OP = ''UPDATE''%'
            AND (
                POSITION('OLD.' IN v_person_fn_src) = 0
                OR POSITION('TG_OP = ''INSERT''' IN v_person_fn_src) < POSITION('OLD.' IN v_person_fn_src)
            )
        );
        IF v_person_trigger_safe THEN
            RAISE NOTICE '[PASS] C-6 [SI] handle_person_ledger_entry_workflow correctly separates INSERT and UPDATE paths (OLD guarded).';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-6 [SI] handle_person_ledger_entry_workflow missing TG_OP guards — unsafe OLD reference on INSERT possible.';
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-6 [SI] handle_person_ledger_entry_workflow function not found.';
    END IF;

    -- ── C-7 [SI]: Settlement trigger uses TG_OP guards ─────────
    SELECT p.prosrc
    INTO v_settlement_fn_src
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'handle_distributor_settlement_workflow'
    LIMIT 1;

    IF v_settlement_fn_src IS NOT NULL THEN
        v_settlement_trigger_safe := (
            v_settlement_fn_src ILIKE '%TG_OP = ''INSERT''%'
            AND v_settlement_fn_src ILIKE '%TG_OP = ''UPDATE''%'
            AND (
                POSITION('OLD.' IN v_settlement_fn_src) = 0
                OR POSITION('TG_OP = ''INSERT''' IN v_settlement_fn_src) < POSITION('OLD.' IN v_settlement_fn_src)
            )
        );
        IF v_settlement_trigger_safe THEN
            RAISE NOTICE '[PASS] C-7 [SI] handle_distributor_settlement_workflow correctly separates INSERT and UPDATE paths (OLD guarded).';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-7 [SI] handle_distributor_settlement_workflow missing TG_OP guards — unsafe OLD reference on INSERT possible.';
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-7 [SI] handle_distributor_settlement_workflow function not found.';
    END IF;

    -- ── C-8 [SI]: Person ledger cancellation uses exact ownership triple-check ──
    IF v_person_fn_src IS NOT NULL THEN
        v_person_cancel_ownership := (
            v_person_fn_src ILIKE '%originating_ledger_entry_id = NEW.id%'
            AND v_person_fn_src ILIKE '%person_id = NEW.person_id%'
            AND v_person_fn_src ILIKE '%id = NEW.expense_id%'
        );
        IF v_person_cancel_ownership THEN
            RAISE NOTICE '[PASS] C-8 [SI] Person ledger cancellation uses triple-ownership check (expense_id + person_id + originating_entry_id).';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-8 [SI] Person ledger cancellation does not enforce full ownership.';
        END IF;
    ELSE
        RAISE NOTICE '[SKIP] C-8 [SI] Skipped — function source unavailable (caught in C-6).';
    END IF;

    -- ── C-9 [SI] (v3.0 Req 2): sale_items immutability handles DELETE without referencing NEW ──
    SELECT p.prosrc
    INTO v_sale_items_fn_src
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'prevent_approved_sale_items_mutation'
    LIMIT 1;

    IF v_sale_items_fn_src IS NOT NULL THEN
        v_sale_items_tgop_safe := (
            v_sale_items_fn_src ILIKE '%TG_OP = ''DELETE''%'
            AND v_sale_items_fn_src ILIKE '%OLD.sale_order_id%'
            AND v_sale_items_fn_src ILIKE '%RETURN OLD%'
            AND NOT (v_sale_items_fn_src ILIKE '%COALESCE(NEW.sale_order_id%')
        );
        IF v_sale_items_tgop_safe THEN
            RAISE NOTICE '[PASS] C-9 [SI] prevent_approved_sale_items_mutation handles TG_OP = ''DELETE'' safely without referencing NEW.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-9 [SI] prevent_approved_sale_items_mutation accesses NEW on DELETE or lacks explicit TG_OP separation.';
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-9 [SI] prevent_approved_sale_items_mutation function not found.';
    END IF;

    -- ── C-10 [SI] (v3.0 Req 3): Expense double-counting prevention (linked expenses strictly Payment) ──
    SELECT p.prosrc
    INTO v_fn_source
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'create_person_ledger_entry_with_expense'
    LIMIT 1;

    IF v_fn_source IS NOT NULL AND v_person_fn_src IS NOT NULL THEN
        v_expense_double_count_safe := (
            v_fn_source ILIKE '%p_entry_type != ''Payment''%'
            AND v_fn_source ILIKE '%double-counting%'
            AND v_person_fn_src ILIKE '%NEW.entry_type != ''Payment''%'
        );
        IF v_expense_double_count_safe THEN
            RAISE NOTICE '[PASS] C-10 [SI] Expense double-counting strictly prevented: linked expenses restricted to Payment entries only.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-10 [SI] Linked expenses can still be created for Work_Earning or Advance (double-counting risk).';
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-10 [SI] Function create_person_ledger_entry_with_expense not found for double-counting check.';
    END IF;

    -- ── C-11 [SI] (v3.0 Req 4): Sales order workflow server-side authorization on INSERT and UPDATE ──
    IF v_rec_fn_src IS NOT NULL THEN
        v_sales_auth_safe := (
            v_rec_fn_src ILIKE '%TG_OP = ''INSERT''%'
            AND v_rec_fn_src ILIKE '%TG_OP = ''UPDATE''%'
            AND v_rec_fn_src ILIKE '%sales.approve%'
            AND v_rec_fn_src ILIKE '%OLD.status = ''Cancelled''%'
        );
        IF v_sales_auth_safe THEN
            RAISE NOTICE '[PASS] C-11 [SI] handle_sales_order_immutability enforces server-side authorization on both INSERT and UPDATE, preventing reactivation.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-11 [SI] handle_sales_order_immutability missing INSERT/UPDATE authorization guards.';
        END IF;
    ELSE
        RAISE NOTICE '[SKIP] C-11 [SI] Skipped — handle_sales_order_immutability source unavailable (caught in C-5).';
    END IF;

    -- ── C-12 [SI] (v3.0 Req 6): reconcile_historical_sales_order_rates validates bounds & writes audit_logs ──
    SELECT p.prosrc
    INTO v_fn_source
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'reconcile_historical_sales_order_rates'
    LIMIT 1;

    IF v_fn_source IS NOT NULL THEN
        v_reconcile_audit_safe := (
            v_fn_source ILIKE '%500.00%'
            AND v_fn_source ILIKE '%INSERT INTO public.audit_logs%'
            AND v_fn_source ILIKE '%RECONCILE_RATES%'
            AND v_fn_source ILIKE '%Super_Admin%'
        );
        IF v_reconcile_audit_safe THEN
            RAISE NOTICE '[PASS] C-12 [SI] reconcile_historical_sales_order_rates validates rate bounds and records audit_logs entry.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-12 [SI] reconcile_historical_sales_order_rates missing rate validation or audit logging.';
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] C-12 [SI] reconcile_historical_sales_order_rates function not found.';
    END IF;

    -- ── C-13 [SI] (v3.0 Req 7): Settlements enforced Pending-first on INSERT ──
    IF v_settlement_fn_src IS NOT NULL THEN
        v_settle_insert_pending := (
            v_settlement_fn_src ILIKE '%TG_OP = ''INSERT''%'
            AND v_settlement_fn_src ILIKE '%NEW.status = ''Approved''%'
            AND v_settlement_fn_src ILIKE '%prohibited%'
        );
        IF v_settle_insert_pending THEN
            RAISE NOTICE '[PASS] C-13 [SI] handle_distributor_settlement_workflow prohibits direct INSERT with Approved status.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] C-13 [SI] handle_distributor_settlement_workflow allows direct INSERT as Approved, bypassing balance checks.';
        END IF;
    ELSE
        RAISE NOTICE '[SKIP] C-13 [SI] Skipped — settlement workflow source unavailable.';
    END IF;

    -- ══════════════════════════════════════════════════════════════════════
    -- SECTION D: FUNCTIONS & TRIGGERS
    -- ══════════════════════════════════════════════════════════════════════
    RAISE NOTICE '';
    RAISE NOTICE '── Section D: Functions & Triggers ────────────────────────────────────────';

    -- ── D-1 [SI]: All 7 RPC functions deployed ─────────────────────────────
    FOREACH v_fn IN ARRAY v_expected_fns LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public' AND p.proname = v_fn
        ) THEN
            v_missing_functions := array_append(v_missing_functions, v_fn);
        END IF;
    END LOOP;

    IF array_length(v_missing_functions, 1) IS NULL THEN
        RAISE NOTICE '[PASS] D-1 [SI] All 7 server-side RPC functions present.';
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] D-1 [SI] Missing RPC functions: %', v_missing_functions;
    END IF;

    -- ── D-2 [SI]: All workflow and immutability triggers present ───────────
    FOREACH v_trg IN ARRAY v_expected_triggers LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger t
            JOIN pg_class c ON c.oid = t.tgrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND t.tgname = v_trg AND NOT t.tgisinternal
        ) THEN
            v_missing_triggers := array_append(v_missing_triggers, v_trg);
        END IF;
    END LOOP;

    IF array_length(v_missing_triggers, 1) IS NULL THEN
        RAISE NOTICE '[PASS] D-2 [SI] All 11 workflow and immutability triggers deployed.';
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] D-2 [SI] Missing triggers: %', v_missing_triggers;
    END IF;

    -- ── D-3 [SI]: has_permission() uses parameter name req_perm ───────────
    SELECT p.proargnames[1]
    INTO v_has_perm_argname
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'has_permission'
    LIMIT 1;

    IF v_has_perm_argname = 'req_perm' THEN
        RAISE NOTICE '[PASS] D-3 [SI] has_permission() parameter is named ''req_perm'' — compatible with existing RLS policies.';
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] D-3 [SI] has_permission() parameter name is ''%'' — expected ''req_perm''. Existing RLS policies may break.',
            COALESCE(v_has_perm_argname, '<not found>');
    END IF;

    -- ── D-4 [SI]: Settlement trigger fires on BOTH INSERT and UPDATE ───────
    SELECT t.tgtype
    INTO v_settle_tgtype
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND t.tgname = 'trg_distributor_settlement_workflow'
      AND NOT t.tgisinternal;

    IF v_settle_tgtype IS NOT NULL
       AND (v_settle_tgtype & 4)  > 0
       AND (v_settle_tgtype & 16) > 0
    THEN
        RAISE NOTICE '[PASS] D-4 [SI] trg_distributor_settlement_workflow fires on both INSERT and UPDATE (tgtype=%).',
            v_settle_tgtype;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] D-4 [SI] trg_distributor_settlement_workflow tgtype=% — does not cover both INSERT and UPDATE.',
            v_settle_tgtype;
    END IF;

    -- ── D-5 [SI]: Person ledger trigger fires on BOTH INSERT and UPDATE ────
    SELECT t.tgtype
    INTO v_person_tgtype
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND t.tgname = 'trg_person_ledger_workflow'
      AND NOT t.tgisinternal;

    IF v_person_tgtype IS NOT NULL
       AND (v_person_tgtype & 4)  > 0
       AND (v_person_tgtype & 16) > 0
    THEN
        RAISE NOTICE '[PASS] D-5 [SI] trg_person_ledger_workflow fires on both INSERT and UPDATE (tgtype=%).',
            v_person_tgtype;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] D-5 [SI] trg_person_ledger_workflow tgtype=% — does not cover both INSERT and UPDATE.',
            v_person_tgtype;
    END IF;

    -- ── D-6 [SI]: Sales order immutability trigger fires on BOTH INSERT and UPDATE ──
    SELECT t.tgtype
    INTO v_so_trg_tgtype
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND t.tgname = 'trg_sales_order_immutability'
      AND NOT t.tgisinternal;

    IF v_so_trg_tgtype IS NOT NULL
       AND (v_so_trg_tgtype & 4)  > 0
       AND (v_so_trg_tgtype & 16) > 0
    THEN
        RAISE NOTICE '[PASS] D-6 [SI] trg_sales_order_immutability fires on both INSERT and UPDATE (tgtype=%).',
            v_so_trg_tgtype;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] D-6 [SI] trg_sales_order_immutability tgtype=% — does not cover both INSERT and UPDATE.',
            v_so_trg_tgtype;
    END IF;

    -- ══════════════════════════════════════════════════════════════════════
    -- SECTION E: VIEWS & SECURITY
    -- ══════════════════════════════════════════════════════════════════════
    RAISE NOTICE '';
    RAISE NOTICE '── Section E: Views & Security ─────────────────────────────────────────────';

    -- ── E-1 [SI]: v_unreconciled_sales_orders view exists ─────────────────
    IF EXISTS (
        SELECT 1 FROM information_schema.views
        WHERE table_schema = 'public' AND table_name = 'v_unreconciled_sales_orders'
    ) THEN
        EXECUTE 'SELECT COUNT(*) FROM public.v_unreconciled_sales_orders' INTO v_unreconciled_count;
        RAISE NOTICE '[PASS] E-1 [SI] View v_unreconciled_sales_orders active. Unreconciled historical orders: %', v_unreconciled_count;
        IF v_unreconciled_count > 0 THEN
            RAISE NOTICE '       ACTION REQUIRED: Run reconcile_historical_sales_order_rates() as Super_Admin before approving settlements.';
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] E-1 [SI] View v_unreconciled_sales_orders is missing.';
    END IF;

    -- ── E-2 [SI]: Column-level privilege — authenticated cannot UPDATE status directly ──
    BEGIN
        v_e2_passed := NOT has_column_privilege(
            'authenticated',
            'public.person_ledger_entries',
            'status',
            'UPDATE'
        );
        IF v_e2_passed THEN
            RAISE NOTICE '[PASS] E-2 [SI] Column privilege: ''authenticated'' cannot directly UPDATE status on person_ledger_entries.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] E-2 [SI] SECURITY VIOLATION: ''authenticated'' has direct UPDATE privilege on person_ledger_entries.status!';
        END IF;
    EXCEPTION
        WHEN undefined_object THEN
            RAISE NOTICE '[WARN] E-2 [SI] Role ''authenticated'' not found — privilege check skipped. Verify Supabase auth roles are provisioned.';
        WHEN undefined_table THEN
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] E-2 [SI] Table person_ledger_entries not found for privilege check.';
    END;

    -- ── E-3 [SI]: All SECURITY DEFINER functions have safe search_path ────
    SELECT array_agg(f.name ORDER BY f.name)
    INTO v_unsafe_fns
    FROM unnest(ARRAY[
        'auth_user_role', 'has_permission',
        'create_sales_order_with_items',
        'create_person_ledger_entry_with_expense',
        'approve_person_ledger_entry', 'cancel_person_ledger_entry',
        'approve_distributor_settlement', 'cancel_distributor_settlement',
        'reconcile_historical_sales_order_rates',
        'handle_person_ledger_entry_workflow',
        'handle_distributor_settlement_workflow',
        'handle_sales_order_immutability',
        'handle_recovery_immutability', 'handle_expense_immutability',
        'prevent_approved_sale_items_mutation'
    ]) AS f(name)
    LEFT JOIN (
        SELECT p.proname, p.prosecdef, p.proconfig
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
    ) p ON p.proname = f.name
    WHERE p.proname IS NULL
       OR p.prosecdef IS NOT TRUE
       OR p.proconfig IS NULL
       OR NOT EXISTS (
           SELECT 1 FROM unnest(p.proconfig) cfg
           WHERE cfg ILIKE 'search_path=%'
             AND cfg ILIKE '%public%'
             AND cfg ILIKE '%pg_temp%'
       );

    IF array_length(v_unsafe_fns, 1) IS NULL THEN
        RAISE NOTICE '[PASS] E-3 [SI] All 15 security-critical functions verified: SECURITY DEFINER with search_path = public, pg_temp.';
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] E-3 [SI] Functions missing, not SECURITY DEFINER, or missing safe search_path: %', v_unsafe_fns;
    END IF;

    -- ══════════════════════════════════════════════════════════════════════
    -- SECTION F: FINANCIAL CONSISTENCY SPOT-CHECKS
    -- ══════════════════════════════════════════════════════════════════════
    RAISE NOTICE '';
    RAISE NOTICE '── Section F: Financial Consistency Spot-Checks ────────────────────────────';

    -- ── F-1 [DV]: No Approved settlement with NULL recovery_id where type is Against_Outstanding ──
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'distributor_settlements') THEN
        EXECUTE 'SELECT COUNT(*) FROM public.distributor_settlements WHERE settlement_type::TEXT = ''Commission_Against_Outstanding'' AND status = ''Approved'' AND recovery_id IS NULL'
        INTO v_bad_settlements;

        IF v_bad_settlements = 0 THEN
            RAISE NOTICE '[PASS] F-1 [DV] No approved Commission_Against_Outstanding settlements with missing recovery link.';
        ELSE
            v_all_passed := FALSE;
            RAISE NOTICE '[FAIL] F-1 [DV] % approved Commission_Against_Outstanding settlement(s) have NULL recovery_id — atomic creation failed.', v_bad_settlements;
        END IF;
    ELSE
        v_all_passed := FALSE;
        RAISE NOTICE '[FAIL] F-1 [DV] distributor_settlements table missing.';
    END IF;

    -- ── F-2 [DV]: Approved person ledger entries with NULL expense_id (informational audit) ──
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'person_ledger_entries') THEN
        EXECUTE 'SELECT COUNT(*) FROM public.person_ledger_entries WHERE entry_type::TEXT = ''Payment'' AND status = ''Approved'' AND expense_id IS NULL'
        INTO v_bad_entries;

        RAISE NOTICE '[INFO] F-2 [DV] Approved Payment entries with NULL expense_id: % (direct payments without operational expense link).',
            v_bad_entries;
    ELSE
        RAISE NOTICE '[WARN] F-2 [DV] person_ledger_entries table missing — skipped entry audit.';
    END IF;

    -- ── F-3 [DV]: Approved sales orders with snapshot rates for reference ──
    IF v_has_so_comm_snap THEN
        EXECUTE 'SELECT COUNT(*) FROM public.sales_orders WHERE status::TEXT IN (''Approved'', ''Posted'') AND commission_rate_snapshot IS NOT NULL'
        INTO v_orders_with_snaps;

        EXECUTE 'SELECT COUNT(*) FROM public.sales_orders WHERE status::TEXT IN (''Approved'', ''Posted'') AND commission_rate_snapshot IS NULL'
        INTO v_orders_null_snaps;

        RAISE NOTICE '[INFO] F-3 [DV] Approved/Posted orders with commission snapshot: %, without (need reconciliation): %',
            v_orders_with_snaps, v_orders_null_snaps;

        IF v_orders_null_snaps > 0 THEN
            RAISE NOTICE '       ACTION REQUIRED: % orders need reconciliation via reconcile_historical_sales_order_rates() before settlements can be approved.',
                v_orders_null_snaps;
        END IF;
    ELSE
        RAISE NOTICE '[WARN] F-3 [DV] commission_rate_snapshot column missing from sales_orders.';
    END IF;

    -- ── F-4 [DV]: No Approved recovery with payment_method='Adjustment' outside settlements ──
    SELECT COUNT(*) INTO v_adj_recoveries
    FROM public.recoveries
    WHERE payment_method = 'Adjustment' AND status = 'Approved';

    RAISE NOTICE '[INFO] F-4 [DV] Approved recoveries with payment_method=''Adjustment'': % (expect 0 or settlement-linked only).', v_adj_recoveries;

    -- ══════════════════════════════════════════════════════════════════════
    -- OVERALL RESULT
    -- ══════════════════════════════════════════════════════════════════════
    RAISE NOTICE '';
    RAISE NOTICE '──────────────────────────────────────────────────────────────────────────────';
    IF v_all_passed THEN
        RAISE NOTICE '>>> OVERALL VERIFICATION: [PASS] — v3.0 migration applied correctly. <<<';
        RAISE NOTICE '    Review [INFO] notices above for any manual reconciliation actions needed.';
    ELSE
        RAISE NOTICE '>>> OVERALL VERIFICATION: [FAIL] — Review [FAIL] items above before production use. <<<';
    END IF;
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'EXECUTION ORDER REMINDER:';
    RAISE NOTICE '  STEP 1: preflight_check.sql                  (read-only diagnostic)';
    RAISE NOTICE '  STEP 2: production_phase2_migration.sql v3.0  (transactional migration)';
    RAISE NOTICE '  STEP 3: post_migration_verification.sql v3.0  (this script — read-only)';
    RAISE NOTICE '==============================================================================';
END $$;

ROLLBACK;

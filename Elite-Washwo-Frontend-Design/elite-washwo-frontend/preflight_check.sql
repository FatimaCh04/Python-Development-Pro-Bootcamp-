-- ==============================================================================
-- ELITE WASHWO ERP — PREFLIGHT SCHEMA AUDIT & DIAGNOSTIC SCRIPT (READ-ONLY)
-- Target: Supabase PostgreSQL 17.6 Production Instance
-- SAFETY: Purely read-only diagnostic checks. Zero DDL, zero DML, zero mutations.
-- ==============================================================================

DO $$
DECLARE
    v_pg_version TEXT;
    v_db_name TEXT;
    v_table_count INT;
    v_so_salesman_nullable TEXT;
    v_so_customer_nullable TEXT;
    v_rec_salesman_nullable TEXT;
    v_rec_customer_nullable TEXT;
    v_exp_salesman_nullable TEXT;
    v_has_so_dist_col BOOLEAN;
    v_has_rec_dist_col BOOLEAN;
    v_has_exp_dist_col BOOLEAN;
    v_has_inv_dist_col BOOLEAN;
    v_has_comm_snap BOOLEAN;
    v_has_adv_snap BOOLEAN;
    v_has_welf_snap BOOLEAN;
    v_has_adv_rate_settings BOOLEAN;
    v_has_welf_rate_settings BOOLEAN;
    v_has_persons BOOLEAN;
    v_has_person_entries BOOLEAN;
    v_has_dist_settlements BOOLEAN;
    v_sales_count INT := 0;
    v_recoveries_count INT := 0;
    v_expenses_count INT := 0;
    v_distributors_count INT := 0;
    v_null_dist_sales INT := 0;
    v_null_dist_recs INT := 0;
    v_enum_has_issue BOOLEAN;
    v_enum_has_good_ret BOOLEAN;
    v_enum_has_dam_ret BOOLEAN;
    v_rls_all_enabled BOOLEAN := TRUE;
    v_rec RECORD;
BEGIN
    SELECT version() INTO v_pg_version;
    SELECT current_database() INTO v_db_name;

    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  ELITE WASHWO ERP — PHASE 2 PREFLIGHT DIAGNOSTIC REPORT';
    RAISE NOTICE '==============================================================================';
    RAISE NOTICE 'Database: %', v_db_name;
    RAISE NOTICE 'PostgreSQL Version: %', v_pg_version;
    RAISE NOTICE 'Timestamp: %', NOW();
    RAISE NOTICE '------------------------------------------------------------------------------';

    -- 1. Check existing tables in public schema
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    RAISE NOTICE '[CHECK 1] Existing public base tables count: %', v_table_count;

    -- 2. Audit nullability of salesman_id & customer_id on sales_orders & recoveries
    SELECT is_nullable INTO v_so_salesman_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'salesman_id';

    SELECT is_nullable INTO v_so_customer_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'customer_id';

    SELECT is_nullable INTO v_rec_salesman_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'recoveries' AND column_name = 'salesman_id';

    SELECT is_nullable INTO v_rec_customer_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'recoveries' AND column_name = 'customer_id';

    SELECT is_nullable INTO v_exp_salesman_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'expenses' AND column_name = 'salesman_id';

    RAISE NOTICE '[CHECK 2] Column Nullability:';
    RAISE NOTICE '    - sales_orders.salesman_id nullable: % (Action needed if NO: DROP NOT NULL)', COALESCE(v_so_salesman_nullable, 'COLUMN MISSING');
    RAISE NOTICE '    - sales_orders.customer_id nullable: % (Action needed if NO: DROP NOT NULL)', COALESCE(v_so_customer_nullable, 'COLUMN MISSING');
    RAISE NOTICE '    - recoveries.salesman_id nullable:   % (Action needed if NO: DROP NOT NULL)', COALESCE(v_rec_salesman_nullable, 'COLUMN MISSING');
    RAISE NOTICE '    - recoveries.customer_id nullable:   % (Action needed if NO: DROP NOT NULL)', COALESCE(v_rec_customer_nullable, 'COLUMN MISSING');
    RAISE NOTICE '    - expenses.salesman_id nullable:     % (Action needed if NO: DROP NOT NULL)', COALESCE(v_exp_salesman_nullable, 'COLUMN MISSING');

    -- 3. Check presence of distributor_id foreign keys
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'distributor_id') INTO v_has_so_dist_col;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'recoveries' AND column_name = 'distributor_id') INTO v_has_rec_dist_col;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'expenses' AND column_name = 'distributor_id') INTO v_has_exp_dist_col;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'inventory_transactions' AND column_name = 'distributor_id') INTO v_has_inv_dist_col;

    RAISE NOTICE '[CHECK 3] Distributor Columns:';
    RAISE NOTICE '    - sales_orders.distributor_id exists: %', v_has_so_dist_col;
    RAISE NOTICE '    - recoveries.distributor_id exists:   %', v_has_rec_dist_col;
    RAISE NOTICE '    - expenses.distributor_id exists:     %', v_has_exp_dist_col;
    RAISE NOTICE '    - inventory_transactions.distributor_id exists: %', v_has_inv_dist_col;

    -- 4. Check snapshot columns on sales_orders
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'commission_rate_snapshot') INTO v_has_comm_snap;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'advertisement_rate_snapshot') INTO v_has_adv_snap;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'sales_orders' AND column_name = 'welfare_rate_snapshot') INTO v_has_welf_snap;

    RAISE NOTICE '[CHECK 4] Sales Order Snapshot Columns:';
    RAISE NOTICE '    - commission_rate_snapshot:    %', v_has_comm_snap;
    RAISE NOTICE '    - advertisement_rate_snapshot: %', v_has_adv_snap;
    RAISE NOTICE '    - welfare_rate_snapshot:        %', v_has_welf_snap;

    -- 5. Check global_settings table columns
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'global_settings' AND column_name = 'advertisement_rate') INTO v_has_adv_rate_settings;
    SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'global_settings' AND column_name = 'welfare_rate') INTO v_has_welf_rate_settings;

    RAISE NOTICE '[CHECK 5] Global Settings Columns:';
    RAISE NOTICE '    - global_settings.advertisement_rate exists: % (Action needed if FALSE: ADD COLUMN)', v_has_adv_rate_settings;
    RAISE NOTICE '    - global_settings.welfare_rate exists:       % (Action needed if FALSE: ADD COLUMN)', v_has_welf_rate_settings;

    -- 6. Check existence of Phase 2 tables
    SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'persons') INTO v_has_persons;
    SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'person_ledger_entries') INTO v_has_person_entries;
    SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'distributor_settlements') INTO v_has_dist_settlements;

    RAISE NOTICE '[CHECK 6] Phase 2 Domain Tables:';
    RAISE NOTICE '    - public.persons exists:                 %', v_has_persons;
    RAISE NOTICE '    - public.person_ledger_entries exists:   %', v_has_person_entries;
    RAISE NOTICE '    - public.distributor_settlements exists: %', v_has_dist_settlements;

    -- 7. Audit historical records
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'sales_orders') THEN
        EXECUTE 'SELECT COUNT(*) FROM public.sales_orders' INTO v_sales_count;
        IF v_has_so_dist_col THEN
            EXECUTE 'SELECT COUNT(*) FROM public.sales_orders WHERE distributor_id IS NULL' INTO v_null_dist_sales;
        ELSE
            v_null_dist_sales := v_sales_count;
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'recoveries') THEN
        EXECUTE 'SELECT COUNT(*) FROM public.recoveries' INTO v_recoveries_count;
        IF v_has_rec_dist_col THEN
            EXECUTE 'SELECT COUNT(*) FROM public.recoveries WHERE distributor_id IS NULL' INTO v_null_dist_recs;
        ELSE
            v_null_dist_recs := v_recoveries_count;
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'expenses') THEN
        EXECUTE 'SELECT COUNT(*) FROM public.expenses' INTO v_expenses_count;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'distributors') THEN
        EXECUTE 'SELECT COUNT(*) FROM public.distributors' INTO v_distributors_count;
    END IF;

    RAISE NOTICE '[CHECK 7] Existing Historical Record Counts:';
    RAISE NOTICE '    - sales_orders total: % (Expected ~19, NULL distributor_id: %)', v_sales_count, v_null_dist_sales;
    RAISE NOTICE '    - recoveries total:   % (Expected ~6, NULL distributor_id: %)', v_recoveries_count, v_null_dist_recs;
    RAISE NOTICE '    - expenses total:     % (Expected ~11)', v_expenses_count;
    RAISE NOTICE '    - distributors total: % (Expected ~3)', v_distributors_count;

    -- 8. Audit transaction_type ENUM values
    SELECT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'transaction_type' AND e.enumlabel = 'Distributor_Issue'
    ) INTO v_enum_has_issue;

    SELECT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'transaction_type' AND e.enumlabel = 'Distributor_Good_Return'
    ) INTO v_enum_has_good_ret;

    SELECT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'transaction_type' AND e.enumlabel = 'Distributor_Damaged_Return'
    ) INTO v_enum_has_dam_ret;

    RAISE NOTICE '[CHECK 8] transaction_type ENUM Values:';
    RAISE NOTICE '    - Distributor_Issue exists:          %', v_enum_has_issue;
    RAISE NOTICE '    - Distributor_Good_Return exists:    %', v_enum_has_good_ret;
    RAISE NOTICE '    - Distributor_Damaged_Return exists: %', v_enum_has_dam_ret;

    -- 9. Check RLS status on core tables
    FOR v_rec IN 
        SELECT relname, relrowsecurity 
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'r'
        ORDER BY relname
    LOOP
        IF NOT v_rec.relrowsecurity THEN
            v_rls_all_enabled := FALSE;
            RAISE NOTICE '    WARNING: RLS is DISABLED on table public.%', v_rec.relname;
        END IF;
    END LOOP;
    RAISE NOTICE '[CHECK 9] RLS Enabled on All Public Tables: %', v_rls_all_enabled;

    RAISE NOTICE '==============================================================================';
    RAISE NOTICE '  PREFLIGHT DIAGNOSTIC COMPLETE — NO MODIFICATIONS MADE TO DATABASE';
    RAISE NOTICE '==============================================================================';
END $$;

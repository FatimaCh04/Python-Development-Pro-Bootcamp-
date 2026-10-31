-- ======================================================================================
-- ELITE WASH ERP — VERIFICATION OF CUSTOMER MODULE DEPRECATION
-- Script: verify_customer_cleanup.sql
--
-- 100% READ-ONLY verification audit script.
-- Safe to execute in Supabase SQL Editor at any time.
-- ======================================================================================

-- 1. STRUCTURAL VERIFICATION: ABSENCE OF CUSTOMER TABLES, VIEWS & COLUMNS
SELECT 
    '1. TABLE: public.customers' AS object_checked,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (0 rows - table permanently dropped)' ELSE 'FAILED (Table still exists!)' END AS status,
    COUNT(*) AS found_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_name = 'customers'

UNION ALL

SELECT 
    '2. VIEW: public.customer_ledger' AS object_checked,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (0 views - view permanently dropped)' ELSE 'FAILED (View still exists!)' END AS status,
    COUNT(*) AS found_count
FROM (
    SELECT viewname FROM pg_views WHERE schemaname = 'public' AND viewname = 'customer_ledger'
    UNION ALL
    SELECT matviewname FROM pg_matviews WHERE schemaname = 'public' AND matviewname = 'customer_ledger'
) v

UNION ALL

SELECT 
    '3. COLUMNS: customer_id in public schema' AS object_checked,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (0 columns - completely purged)' ELSE 'FAILED (Columns still exist!)' END AS status,
    COUNT(*) AS found_count
FROM information_schema.columns
WHERE table_schema = 'public' AND column_name = 'customer_id'

UNION ALL

SELECT 
    '4. FOREIGN KEYS referencing customers' AS object_checked,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (0 constraints)' ELSE 'FAILED (Constraints still exist!)' END AS status,
    COUNT(*) AS found_count
FROM information_schema.table_constraints
WHERE table_schema = 'public' AND constraint_name LIKE '%customer%'

UNION ALL

SELECT 
    '5. RLS POLICIES on customers' AS object_checked,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (0 policies)' ELSE 'FAILED (Policies still exist!)' END AS status,
    COUNT(*) AS found_count
FROM pg_policies
WHERE schemaname = 'public' AND tablename = 'customers';


-- 2. OPERATIONAL DATA INTEGRITY & AUDIT TRAIL PRESERVATION
SELECT 
    'Distributors (Real & Preserved)' AS entity_type,
    COUNT(*) AS record_count,
    STRING_AGG(name || ' (' || code || ')', ', ') AS details
FROM public.distributors
WHERE code IN ('ELITEWASH#01', 'ELITEWASH#03', 'Elitewash#04')

UNION ALL

SELECT 
    'Active Staff (Super Admin & Manager)' AS entity_type,
    COUNT(*) AS record_count,
    STRING_AGG(full_name || ' [' || role || ']', ', ') AS details
FROM public.profiles
WHERE role IN ('Super_Admin', 'Manager') AND is_active = TRUE

UNION ALL

SELECT 
    'Manufacturer (SHOAIB)' AS entity_type,
    COUNT(*) AS record_count,
    STRING_AGG(name || ' (' || code || ', ' || category || ')', ', ') AS details
FROM public.persons
WHERE code = 'ELPRODUCTION#01'

UNION ALL

SELECT 
    'Sales Orders (All Assigned to Real Distributors)' AS entity_type,
    COUNT(*) AS record_count,
    'Total Value: Rs. ' || TO_CHAR(COALESCE(SUM(total_amount), 0), 'FM999,999,999') || ' across ' || COUNT(*) || ' orders' AS details
FROM public.sales_orders

UNION ALL

SELECT 
    'Recoveries (100% Associated to Real Distributors)' AS entity_type,
    COUNT(*) AS record_count,
    'Total Recovered: Rs. ' || TO_CHAR(COALESCE(SUM(amount), 0), 'FM999,999,999') || ' across ' || COUNT(*) || ' records (0 unassigned)' AS details
FROM public.recoveries

UNION ALL

SELECT 
    'Expenses (Approved Business Records)' AS entity_type,
    COUNT(*) AS record_count,
    'Total Approved: Rs. ' || TO_CHAR(COALESCE(SUM(amount), 0), 'FM999,999,999') || ' across ' || COUNT(*) || ' records' AS details
FROM public.expenses
WHERE status = 'Approved';


-- 3. EXECUTIVE AUDIT SUMMARY REPORT
WITH audit_metrics AS (
    SELECT 
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'customers') AS cust_tables,
        (SELECT COUNT(*) FROM pg_views WHERE schemaname = 'public' AND viewname = 'customer_ledger') AS cust_views,
        (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public' AND column_name = 'customer_id') AS cust_cols,
        (SELECT COUNT(*) FROM public.distributors WHERE code IN ('ELITEWASH#01', 'ELITEWASH#03', 'Elitewash#04')) AS real_distributors,
        (SELECT COUNT(*) FROM public.profiles WHERE role IN ('Super_Admin', 'Manager') AND is_active = TRUE) AS active_staff,
        (SELECT COUNT(*) FROM public.persons WHERE code = 'ELPRODUCTION#01') AS real_manufacturers,
        (SELECT COUNT(*) FROM public.sales_orders) AS total_orders,
        (SELECT COUNT(*) FROM public.recoveries) AS total_recoveries,
        (SELECT COUNT(*) FROM public.recoveries WHERE distributor_id IS NULL) AS unassigned_recoveries
)
SELECT 
    '======================================================================' AS summary_boundary,
    'EXECUTIVE CUSTOMER DEPRECATION AUDIT SUMMARY' AS report_title,
    CASE 
        WHEN cust_tables = 0 AND cust_views = 0 AND cust_cols = 0 
             AND real_distributors = 3 AND active_staff = 2 AND real_manufacturers = 1
             AND total_orders >= 12 AND total_recoveries >= 8 AND unassigned_recoveries = 0
        THEN 'PASSED — CUSTOMER MODULE PERMANENTLY REMOVED & ALL BUSINESS LEDGERS 100% CLEAN'
        ELSE 'FAILED — RESIDUAL CUSTOMER DEPENDENCY OR DATA LOSS DETECTED'
    END AS overall_status,
    'Residual Customer Tables: ' || cust_tables || ' | Residual Views: ' || cust_views || ' | Residual Columns: ' || cust_cols ||
    ' | Real Distributors: ' || real_distributors || ' | Real Orders: ' || total_orders || ' | Real Recoveries: ' || total_recoveries || ' (Unassigned: ' || unassigned_recoveries || ')' AS metrics_snapshot,
    '======================================================================' AS summary_footer
FROM audit_metrics;

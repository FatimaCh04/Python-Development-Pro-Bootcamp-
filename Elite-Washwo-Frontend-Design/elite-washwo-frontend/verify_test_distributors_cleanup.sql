-- ==============================================================================
-- ELITE WASHWO ERP — POST-CLEANUP VERIFICATION QUERY SUITE (READ-ONLY)
-- Purpose: Inspect and verify database state after running cleanup_test_distributors.sql
-- Target Database: Supabase PostgreSQL 17.6 Production Instance
-- SAFETY: Purely read-only diagnostic SELECT statements. Zero DDL, zero DML.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. VERIFY PURGE OF TARGET TEST DISTRIBUTORS & DEPENDENT RECORDS (ALL MUST BE 0)
-- ------------------------------------------------------------------------------
SELECT 
    'Target Distributors (abc, xyz)' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.distributors
WHERE id IN ('df674217-1088-4ac2-89d6-e3263aaa1a3c', '4cb3f479-07c4-40d5-8c67-67340c104d2f')

UNION ALL

SELECT 
    'Target Sales / Bookings' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.sales_orders
WHERE distributor_id IN ('df674217-1088-4ac2-89d6-e3263aaa1a3c', '4cb3f479-07c4-40d5-8c67-67340c104d2f')

UNION ALL

SELECT 
    'Target Sale Line Items' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.sale_items
WHERE sale_order_id IN (
    SELECT id FROM public.sales_orders 
    WHERE distributor_id IN ('df674217-1088-4ac2-89d6-e3263aaa1a3c', '4cb3f479-07c4-40d5-8c67-67340c104d2f')
)

UNION ALL

SELECT 
    'Target Inventory Transactions' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.inventory_transactions
WHERE distributor_id IN ('df674217-1088-4ac2-89d6-e3263aaa1a3c', '4cb3f479-07c4-40d5-8c67-67340c104d2f')

UNION ALL

SELECT 
    'Target Distributor Settlements' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.distributor_settlements
WHERE distributor_id IN ('df674217-1088-4ac2-89d6-e3263aaa1a3c', '4cb3f479-07c4-40d5-8c67-67340c104d2f')

UNION ALL

SELECT 
    'Target Test Expense (EXP-MUK163IU / dist_id)' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.expenses
WHERE distributor_id IN ('df674217-1088-4ac2-89d6-e3263aaa1a3c', '4cb3f479-07c4-40d5-8c67-67340c104d2f')
   OR reference_number = 'EXP-MUK163IU'

UNION ALL

SELECT 
    'Target Recoveries' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.recoveries
WHERE distributor_id IN ('df674217-1088-4ac2-89d6-e3263aaa1a3c', '4cb3f479-07c4-40d5-8c67-67340c104d2f');

-- ------------------------------------------------------------------------------
-- 2. VERIFY PRESERVATION OF REAL PRODUCTION DISTRIBUTORS
-- ------------------------------------------------------------------------------
SELECT 
    id, code, name, id_card, phone, commission, is_active, created_at
FROM public.distributors
ORDER BY created_at ASC;

-- ------------------------------------------------------------------------------
-- 3. VERIFY RECONCILED COMPANY STOCK BALANCES
-- ------------------------------------------------------------------------------
SELECT 
    p.name AS product_name,
    pp.name AS packaging_name,
    pp.id AS packaging_id,
    COALESCE(SUM(CASE 
        WHEN it.transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN it.quantity
        WHEN it.transaction_type IN ('Adjustment', 'Reversal') AND it.category = 'Sellable Stock' THEN it.quantity
        WHEN it.transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -it.quantity
        ELSE 0 
    END), 0) AS live_sellable_stock,
    COALESCE(SUM(CASE 
        WHEN it.category = 'Damaged Stock' AND it.transaction_type IN ('Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Distributor_Damaged_Return', 'Damage') THEN it.quantity
        WHEN it.category = 'Damaged Stock' AND it.transaction_type IN ('Adjustment', 'Reversal') THEN it.quantity
        ELSE 0 
    END), 0) AS live_damaged_stock
FROM public.product_packaging pp
JOIN public.products p ON p.id = pp.product_id
LEFT JOIN public.inventory_transactions it ON it.packaging_id = pp.id AND it.status IN ('Approved', 'Posted')
GROUP BY p.name, pp.name, pp.id
ORDER BY p.name, pp.name;

-- ------------------------------------------------------------------------------
-- 4. VERIFY AUDIT TRAIL LOGGING OF ADMINISTRATIVE CLEANUP
-- ------------------------------------------------------------------------------
SELECT 
    created_at, table_name, action, record_id, performed_by, old_data
FROM public.audit_logs
WHERE action = 'ADMIN_PURGE_TEST_DISTRIBUTORS' 
   OR (old_data::TEXT LIKE '%df674217-1088-4ac2-89d6-e3263aaa1a3c%' OR old_data::TEXT LIKE '%4cb3f479-07c4-40d5-8c67-67340c104d2f%')
ORDER BY created_at DESC
LIMIT 20;

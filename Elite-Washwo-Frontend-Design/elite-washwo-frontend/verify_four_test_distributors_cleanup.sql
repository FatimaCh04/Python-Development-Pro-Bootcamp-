-- ==============================================================================
-- ELITE WASHWO ERP — POST-CLEANUP VERIFICATION QUERY SUITE (READ-ONLY)
-- Purpose: Inspect and verify database state after running cleanup_four_test_distributors.sql
-- Target Database: Supabase PostgreSQL 17.6 Production Instance
-- SAFETY: Purely read-only diagnostic SELECT statements. Zero DDL, zero DML.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. VERIFY COMPLETE PURGE OF THE 4 TEST DISTRIBUTORS & DEPENDENT RECORDS
--    (ALL TARGET RECORD COUNTS MUST RETURN 0)
-- ------------------------------------------------------------------------------
SELECT 
    'Target Distributors (abc, xyz-1, ali, xyz-2)' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.distributors
WHERE id IN (
    'df674217-1088-4ac2-89d6-e3263aaa1a3c',
    '4cb3f479-07c4-40d5-8c67-67340c104d2f',
    '11cc9861-4234-4984-a0b3-faedba3ad03d',
    '9bfa9e35-75c2-43c6-b536-d941dd29864b'
)

UNION ALL

SELECT 
    'Target Sales Orders & Bookings' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.sales_orders
WHERE distributor_id IN (
    'df674217-1088-4ac2-89d6-e3263aaa1a3c',
    '4cb3f479-07c4-40d5-8c67-67340c104d2f',
    '11cc9861-4234-4984-a0b3-faedba3ad03d',
    '9bfa9e35-75c2-43c6-b536-d941dd29864b'
)

UNION ALL

SELECT 
    'Target Sale Line Items' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.sale_items
WHERE sale_order_id IN (
    SELECT id FROM public.sales_orders 
    WHERE distributor_id IN (
        'df674217-1088-4ac2-89d6-e3263aaa1a3c',
        '4cb3f479-07c4-40d5-8c67-67340c104d2f',
        '11cc9861-4234-4984-a0b3-faedba3ad03d',
        '9bfa9e35-75c2-43c6-b536-d941dd29864b'
    )
)

UNION ALL

SELECT 
    'Target Inventory Transactions' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.inventory_transactions
WHERE distributor_id IN (
    'df674217-1088-4ac2-89d6-e3263aaa1a3c',
    '4cb3f479-07c4-40d5-8c67-67340c104d2f',
    '11cc9861-4234-4984-a0b3-faedba3ad03d',
    '9bfa9e35-75c2-43c6-b536-d941dd29864b'
)

UNION ALL

SELECT 
    'Target Distributor Settlements' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.distributor_settlements
WHERE distributor_id IN (
    'df674217-1088-4ac2-89d6-e3263aaa1a3c',
    '4cb3f479-07c4-40d5-8c67-67340c104d2f',
    '11cc9861-4234-4984-a0b3-faedba3ad03d',
    '9bfa9e35-75c2-43c6-b536-d941dd29864b'
)

UNION ALL

SELECT 
    'Target Expenses (Strict UUID Match Only)' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.expenses
WHERE distributor_id IN (
    'df674217-1088-4ac2-89d6-e3263aaa1a3c',
    '4cb3f479-07c4-40d5-8c67-67340c104d2f',
    '11cc9861-4234-4984-a0b3-faedba3ad03d',
    '9bfa9e35-75c2-43c6-b536-d941dd29864b'
)

UNION ALL

SELECT 
    'Target Recoveries' AS record_category,
    COUNT(*) AS active_record_count,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED (Clean)' ELSE 'FAILED (Records still exist)' END AS audit_status
FROM public.recoveries
WHERE distributor_id IN (
    'df674217-1088-4ac2-89d6-e3263aaa1a3c',
    '4cb3f479-07c4-40d5-8c67-67340c104d2f',
    '11cc9861-4234-4984-a0b3-faedba3ad03d',
    '9bfa9e35-75c2-43c6-b536-d941dd29864b'
);

-- ------------------------------------------------------------------------------
-- 2. VERIFY EXACTLY THREE REAL DISTRIBUTORS REMAIN IN PRODUCTION
-- ------------------------------------------------------------------------------
SELECT 
    id, code, name, id_card, phone, commission, is_active, created_at
FROM public.distributors
ORDER BY created_at ASC;

-- Total count validation (Must be exactly 3)
SELECT 
    COUNT(*) AS total_distributors_in_database,
    CASE WHEN COUNT(*) = 3 THEN 'PASSED (Exactly 3 Real Distributors)' ELSE 'FAILED (Count != 3)' END AS audit_status
FROM public.distributors;

-- ------------------------------------------------------------------------------
-- 3. VERIFY PROTECTION TRIGGERS ARE PRESENT, CORRECTLY DEFINED & ENABLED
-- ------------------------------------------------------------------------------
SELECT 
    c.relname AS table_name,
    t.tgname AS trigger_name,
    p.proname AS attached_function,
    t.tgenabled AS trigger_status,
    CASE 
        WHEN t.tgenabled = 'A' THEN 'PASSED (Active - ENABLE ALWAYS)'
        WHEN t.tgenabled = 'O' THEN 'PASSED (Active - ORIGIN)'
        ELSE 'FAILED (Disabled or Replica Only)'
    END AS audit_status
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_proc p ON p.oid = t.tgfoid
JOIN (
    VALUES 
        ('sales_orders', 'trg_sales_order_prevent_delete', 'prevent_approved_sales_order_delete'),
        ('sale_items', 'trg_sale_items_immutability', 'prevent_approved_sale_items_mutation'),
        ('recoveries', 'trg_recovery_prevent_delete', 'prevent_approved_recovery_delete'),
        ('expenses', 'trg_expense_prevent_delete', 'prevent_approved_expense_delete'),
        ('distributor_settlements', 'trg_distributor_settlement_prevent_delete', 'prevent_approved_settlement_delete')
) AS wl(target_table, target_trigger, target_function)
  ON c.relname = wl.target_table 
 AND t.tgname = wl.target_trigger 
 AND p.proname = wl.target_function
WHERE n.nspname = 'public';

-- ------------------------------------------------------------------------------
-- 4. VERIFY RECONCILED COMPANY STOCK BALANCES (STANDARDIZED DASHBOARD RULES)
-- ------------------------------------------------------------------------------
-- A. Per-Packaging Stock Breakdown (warehouse scope: salesman_id IS NULL)
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
        WHEN it.category = 'Damaged Stock' AND it.transaction_type IN ('Adjustment', 'Reversal') THEN it.quantity
        WHEN it.category = 'Damaged Stock' OR it.transaction_type IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN it.quantity
        ELSE 0 
    END), 0) AS live_damaged_stock
FROM public.product_packaging pp
JOIN public.products p ON p.id = pp.product_id
LEFT JOIN public.inventory_transactions it 
       ON it.packaging_id = pp.id 
      AND it.status IN ('Approved', 'Posted')
      AND it.salesman_id IS NULL
GROUP BY p.name, pp.name, pp.id
ORDER BY p.name, pp.name;

-- B. Global ERP Dashboard Overview Stock (db.js fetchOverviewStats: salesman_id IS NULL)
SELECT 
    'Warehouse Sellable Stock (Dashboard)' AS metric,
    COALESCE(SUM(CASE 
        WHEN transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Distributor_Good_Return', 'Customer_Good_Return') THEN quantity
        WHEN transaction_type IN ('Salesman_Issue', 'Distributor_Issue', 'Damage', 'Expiry') THEN -quantity
        WHEN transaction_type IN ('Adjustment', 'Reversal') AND category = 'Sellable Stock' THEN quantity
        ELSE 0 
    END), 0) AS balance_quantity
FROM public.inventory_transactions
WHERE status IN ('Approved', 'Posted') AND salesman_id IS NULL

UNION ALL

SELECT 
    'Warehouse Damaged Stock (Dashboard)' AS metric,
    COALESCE(SUM(CASE 
        WHEN category = 'Damaged Stock' AND transaction_type IN ('Adjustment', 'Reversal') THEN quantity
        WHEN category = 'Damaged Stock' OR transaction_type IN ('Distributor_Damaged_Return', 'Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Damage', 'Expiry') THEN quantity
        ELSE 0 
    END), 0) AS balance_quantity
FROM public.inventory_transactions
WHERE status IN ('Approved', 'Posted') AND salesman_id IS NULL;

-- ------------------------------------------------------------------------------
-- 5. VERIFY REAL DISTRIBUTOR FINANCIAL BALANCES & PAYMENT BREAKDOWN
-- ------------------------------------------------------------------------------
SELECT 
    d.code AS distributor_code,
    d.name AS distributor_name,
    -- Delivered sales orders (excluding BKG- bookings)
    COALESCE((
        SELECT SUM(so.total_amount) 
        FROM public.sales_orders so 
        WHERE so.distributor_id = d.id 
          AND so.status IN ('Approved', 'Posted')
          AND so.reference_number NOT LIKE 'BKG-%'
    ), 0) AS approved_delivered_sales,
    -- Booking orders
    COALESCE((
        SELECT SUM(so.total_amount) 
        FROM public.sales_orders so 
        WHERE so.distributor_id = d.id 
          AND so.reference_number LIKE 'BKG-%'
    ), 0) AS booking_sales,
    -- Total recoveries
    COALESCE((
        SELECT SUM(rec.amount) 
        FROM public.recoveries rec 
        WHERE rec.distributor_id = d.id AND rec.status IN ('Approved', 'Posted')
    ), 0) AS total_approved_recoveries,
    -- Cash recoveries
    COALESCE((
        SELECT SUM(rec.amount) 
        FROM public.recoveries rec 
        WHERE rec.distributor_id = d.id 
          AND rec.status IN ('Approved', 'Posted')
          AND rec.payment_method = 'Cash'
    ), 0) AS cash_recoveries,
    -- Bank recoveries
    COALESCE((
        SELECT SUM(rec.amount) 
        FROM public.recoveries rec 
        WHERE rec.distributor_id = d.id 
          AND rec.status IN ('Approved', 'Posted')
          AND rec.payment_method != 'Cash'
          AND rec.payment_method != 'Adjustment'
    ), 0) AS bank_recoveries,
    -- Commission adjustment recoveries
    COALESCE((
        SELECT SUM(rec.amount) 
        FROM public.recoveries rec 
        WHERE rec.distributor_id = d.id 
          AND rec.status IN ('Approved', 'Posted')
          AND rec.payment_method = 'Adjustment'
    ), 0) AS adjustment_recoveries,
    -- Approved settlements
    COALESCE((
        SELECT SUM(ds.amount) 
        FROM public.distributor_settlements ds 
        WHERE ds.distributor_id = d.id AND ds.status = 'Approved'
    ), 0) AS total_approved_settlements,
    -- Outstanding balance (approved_delivered_sales - total_approved_recoveries)
    COALESCE((
        SELECT SUM(so.total_amount) 
        FROM public.sales_orders so 
        WHERE so.distributor_id = d.id 
          AND so.status IN ('Approved', 'Posted')
          AND so.reference_number NOT LIKE 'BKG-%'
    ), 0) -
    COALESCE((
        SELECT SUM(rec.amount) 
        FROM public.recoveries rec 
        WHERE rec.distributor_id = d.id AND rec.status IN ('Approved', 'Posted')
    ), 0) AS current_outstanding_balance
FROM public.distributors d
ORDER BY d.code;

-- ------------------------------------------------------------------------------
-- 6. VERIFY AUDIT TRAIL LOGGING OF ADMINISTRATIVE CLEANUP
-- ------------------------------------------------------------------------------
SELECT 
    created_at, table_name, action, record_id, performed_by, old_data
FROM public.audit_logs
WHERE action = 'ADMIN_PURGE_TEST_DISTRIBUTORS' 
   OR (
       old_data::TEXT LIKE '%df674217-1088-4ac2-89d6-e3263aaa1a3c%' OR
       old_data::TEXT LIKE '%4cb3f479-07c4-40d5-8c67-67340c104d2f%' OR
       old_data::TEXT LIKE '%11cc9861-4234-4984-a0b3-faedba3ad03d%' OR
       old_data::TEXT LIKE '%9bfa9e35-75c2-43c6-b536-d941dd29864b%'
   )
ORDER BY created_at DESC
LIMIT 25;

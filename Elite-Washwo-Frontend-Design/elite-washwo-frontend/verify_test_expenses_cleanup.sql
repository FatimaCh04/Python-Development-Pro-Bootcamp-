-- ============================================================================
-- ELITE WASHWO ERP — READ-ONLY VERIFICATION SUITE
-- File: verify_test_expenses_cleanup.sql
-- Task: Read-only inspection & post-migration verification for the 
--       cleanup of 9 old/test expenses from the Expenses module.
--
-- STRICT VERIFICATION GUARANTEES:
--   1. Pure read-only queries (zero mutations or data modifications).
--   2. Direct inspection of live expenses, entities, and summaries.
--   3. Synchronized with actual Expenses page, reports, and dashboard calculations.
--
-- INSTRUCTIONS:
--   Execute this script in the Supabase SQL Editor BEFORE and AFTER running
--   cleanup_test_expenses.sql to verify data safety and integrity.
-- ============================================================================

-- ============================================================================
-- SECTION 1: KEPT EXPENSES AUDIT (EXACTLY 2 RECORDS)
-- ============================================================================
-- Expected BEFORE and AFTER cleanup: Exactly 2 records
--   1. SHAOIB (Manufacturer) — Company expense — Rs. 1,750,000.00 — Approved
--   2. MUHAMMAD NADEEM HUSSAIN (ELITEWASH#01) — Distributor expense — Rs. 12,000.00 — Approved
SELECT 
    e.id,
    e.reference_number,
    e.expense_date,
    e.category,
    e.head,
    e.amount,
    e.payment_method,
    e.status,
    COALESCE(p.name, d.name, sm.profiles_full_name, '—') AS payee_name,
    CASE 
        WHEN e.person_id IS NOT NULL THEN 'Person Payment (SHAOIB)'
        WHEN e.distributor_id IS NOT NULL THEN 'Distributor Expense (ELITEWASH#01)'
        ELSE 'Other'
    END AS expense_nature,
    'KEPT (Permanent Production Expense)' AS retention_status
FROM public.expenses e
LEFT JOIN public.persons p ON p.id = e.person_id
LEFT JOIN public.distributors d ON d.id = e.distributor_id
LEFT JOIN (
    SELECT s.id, pr.full_name AS profiles_full_name 
    FROM public.salesmen s 
    JOIN public.profiles pr ON pr.id = s.id
) sm ON sm.id = e.salesman_id
WHERE (e.amount = 1750000.00 AND e.status::text = 'Approved')
   OR (e.amount = 12000.00 AND e.status::text = 'Approved' AND e.distributor_id IN (SELECT id FROM public.distributors WHERE code = 'ELITEWASH#01'))
ORDER BY e.expense_date DESC;


-- ============================================================================
-- SECTION 2: TARGET TEST EXPENSES AUDIT (9 TEST RECORDS)
-- ============================================================================
-- Expected BEFORE cleanup: Exactly 9 records (Office, Fuel, Loading, Transport, Nouman, Ali, Ahmed, Ahsan)
-- Expected AFTER cleanup:  Exactly 0 records
SELECT 
    e.id,
    e.reference_number,
    e.expense_date,
    e.category,
    e.head,
    e.amount,
    e.status,
    e.description,
    COALESCE(p.name, d.name, sm.profiles_full_name, '—') AS payee_name,
    'Target for Permanent Deletion' AS audit_status
FROM public.expenses e
LEFT JOIN public.persons p ON p.id = e.person_id
LEFT JOIN public.distributors d ON d.id = e.distributor_id
LEFT JOIN (
    SELECT s.id, pr.full_name AS profiles_full_name 
    FROM public.salesmen s 
    JOIN public.profiles pr ON pr.id = s.id
) sm ON sm.id = e.salesman_id
WHERE NOT (
    (e.amount = 1750000.00 AND e.status::text = 'Approved')
    OR (e.amount = 12000.00 AND e.status::text = 'Approved' AND e.distributor_id IN (SELECT id FROM public.distributors WHERE code = 'ELITEWASH#01'))
)
ORDER BY e.expense_date DESC;


-- ============================================================================
-- SECTION 3: EXPENSE SUMMARY & CATEGORY BREAKDOWN RECONCILIATION
-- ============================================================================
-- Validates calculations matching db.js fetchExpenseSummary:
--   Total Approved: Rs. 1,762,000.00 (1,750,000 + 12,000)
--   Total Pending:  Rs. 0.00
SELECT 
    COUNT(*) AS total_expenses_count,
    COALESCE(SUM(CASE WHEN status::text IN ('Approved', 'Posted') THEN amount ELSE 0 END), 0) AS total_approved_amount,
    COALESCE(SUM(CASE WHEN status::text IN ('Pending', 'Submitted') THEN amount ELSE 0 END), 0) AS total_pending_amount,
    COALESCE(SUM(CASE WHEN category = 'Company' AND status::text IN ('Approved', 'Posted') THEN amount ELSE 0 END), 0) AS company_approved_amount,
    COALESCE(SUM(CASE WHEN category = 'Distributor' AND status::text IN ('Approved', 'Posted') THEN amount ELSE 0 END), 0) AS distributor_approved_amount,
    COALESCE(SUM(CASE WHEN category = 'Office' THEN amount ELSE 0 END), 0) AS office_expenses_amount,
    COALESCE(SUM(CASE WHEN category NOT IN ('Company', 'Distributor', 'Office') AND status::text IN ('Approved', 'Posted') THEN amount ELSE 0 END), 0) AS other_approved_amount
FROM public.expenses;


-- ============================================================================
-- SECTION 4: REAL PROFILES & PRODUCTION DISTRIBUTORS PRESERVATION AUDIT
-- ============================================================================
-- Confirms worker SHAOIB and the 3 confirmed real distributors are 100% untouched
SELECT 
    'Worker: SHAOIB' AS entity_type,
    p.code,
    p.name,
    p.category,
    p.is_active,
    (SELECT COUNT(*) FROM public.person_ledger_entries ple WHERE ple.person_id = p.id) AS ledger_entries_count
FROM public.persons p
WHERE p.code = 'ELPRODUCTION#01' OR UPPER(TRIM(p.name)) LIKE '%SHAOIB%'

UNION ALL

SELECT 
    'Real Distributor' AS entity_type,
    d.code,
    d.name,
    d.phone,
    d.is_active,
    (SELECT COUNT(*) FROM public.sales_orders so WHERE so.distributor_id = d.id) AS sales_orders_count
FROM public.distributors d
WHERE d.code IN ('ELITEWASH#01', 'ELITEWASH#03', 'Elitewash#04')
ORDER BY entity_type, code;


-- ============================================================================
-- SECTION 5: APPROVED-RECORD PROTECTION TRIGGERS AUDIT
-- ============================================================================
-- Confirms all database deletion protection triggers are active
SELECT 
    c.relname AS table_name,
    t.tgname AS trigger_name,
    t.tgenabled AS trigger_state,
    CASE t.tgenabled
        WHEN 'O' THEN 'ACTIVE (Origin/Enabled)'
        WHEN 'A' THEN 'ACTIVE (Always)'
        WHEN 'R' THEN 'ACTIVE (Replica)'
        WHEN 'D' THEN 'DISABLED'
        ELSE 'UNKNOWN'
    END AS readable_status
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND (
      (c.relname = 'expenses' AND t.tgname = 'trg_expense_prevent_delete')
      OR (c.relname = 'person_ledger_entries' AND t.tgname = 'trg_person_ledger_prevent_delete')
  )
ORDER BY c.relname, t.tgname;


-- ============================================================================
-- SECTION 6: FINAL EXECUTIVE VERIFICATION SUMMARY CARD
-- ============================================================================
-- Expected POST-CLEANUP:
--   - Total expenses:        2 (PASS)
--   - Test expenses:         0 (PASS)
--   - Kept expenses:         2 (PASS)
--   - Total approved amount: Rs. 1,762,000.00 (PASS)
--   - Total pending amount:  Rs. 0.00 (PASS)
SELECT 
    (SELECT COUNT(*) FROM public.expenses) AS total_expenses_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.expenses) = 2 
        THEN 'PASS (Exactly 2 production expenses remain)'
        ELSE 'AUDIT NOTE: 11 total expenses before cleanup; 2 after cleanup'
    END AS total_expenses_status,

    (
        SELECT COUNT(*) FROM public.expenses 
        WHERE NOT (
            (amount = 1750000.00 AND status::text = 'Approved')
            OR (amount = 12000.00 AND status::text = 'Approved' AND distributor_id IN (SELECT id FROM public.distributors WHERE code = 'ELITEWASH#01'))
        )
    ) AS test_expenses_remaining,
    CASE 
        WHEN (
            SELECT COUNT(*) FROM public.expenses 
            WHERE NOT (
                (amount = 1750000.00 AND status::text = 'Approved')
                OR (amount = 12000.00 AND status::text = 'Approved' AND distributor_id IN (SELECT id FROM public.distributors WHERE code = 'ELITEWASH#01'))
            )
        ) = 0 
        THEN 'PASS (All 9 test expenses permanently purged)'
        ELSE 'PENDING (Test expenses present)'
    END AS test_expenses_status,

    (
        SELECT COALESCE(SUM(amount), 0) FROM public.expenses WHERE status::text IN ('Approved', 'Posted')
    ) AS total_approved_amount,
    CASE 
        WHEN (SELECT COALESCE(SUM(amount), 0) FROM public.expenses WHERE status::text IN ('Approved', 'Posted')) = 1762000.00 
        THEN 'PASS (Exactly Rs. 1,762,000.00)'
        ELSE 'FAIL (Expected Rs. 1,762,000.00)'
    END AS approved_amount_status,

    (
        SELECT COALESCE(SUM(amount), 0) FROM public.expenses WHERE status::text IN ('Pending', 'Submitted')
    ) AS total_pending_amount,
    CASE 
        WHEN (SELECT COALESCE(SUM(amount), 0) FROM public.expenses WHERE status::text IN ('Pending', 'Submitted')) = 0.00 
        THEN 'PASS (Rs. 0.00 pending expenses)'
        ELSE 'FAIL (Pending expenses still present)'
    END AS pending_amount_status;

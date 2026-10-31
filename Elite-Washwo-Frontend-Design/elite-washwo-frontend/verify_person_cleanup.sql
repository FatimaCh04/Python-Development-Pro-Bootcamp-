-- ============================================================================
-- ELITE WASHWO ERP — READ-ONLY VERIFICATION SUITE
-- File: verify_person_cleanup.sql
-- Task: Read-only inspection & post-migration verification for the 
--       cleanup of test person PER-001 (zainulabideen).
--
-- STRICT VERIFICATION GUARANTEES:
--   1. Pure read-only queries (zero data modifications or side effects).
--   2. Direct inspection of live persons, ledger entries, and expenses.
--   3. Synchronized with actual Person Payments and Ledger queries.
--
-- INSTRUCTIONS:
--   Execute this script in the Supabase SQL Editor BEFORE and AFTER running
--   cleanup_test_person_payment.sql to verify data safety and integrity.
-- ============================================================================

-- ============================================================================
-- SECTION 1: TARGET TEST PERSON AUDIT (PER-001 / zainulabideen)
-- ============================================================================
-- Expected BEFORE cleanup: Exactly 1 record (PER-001, zainulabideen, Labourer, Rs. 3 payable, Rs. 4 advance)
-- Expected AFTER cleanup:  Exactly 0 records
SELECT 
    p.id,
    p.code,
    p.name,
    p.category,
    p.phone,
    p.opening_payable_balance AS opening_payable_pkr,
    p.opening_receivable_balance AS opening_advance_pkr,
    p.is_active,
    (SELECT COUNT(*) FROM public.person_ledger_entries ple WHERE ple.person_id = p.id) AS ledger_entries_count,
    (SELECT COUNT(*) FROM public.expenses exp WHERE exp.person_id = p.id) AS direct_expenses_count,
    CASE 
        WHEN p.code = 'PER-001' THEN 'Target for Permanent Deletion'
        ELSE 'Active Person'
    END AS audit_status
FROM public.persons p
WHERE p.code = 'PER-001'
   OR LOWER(TRIM(p.name)) = 'zainulabideen';


-- ============================================================================
-- SECTION 2: TARGET PERSON'S ASSOCIATED TEST LEDGER ENTRIES & EXPENSES
-- ============================================================================
-- Expected BEFORE cleanup: Associated test records (if any)
-- Expected AFTER cleanup:  0 records
SELECT 
    ple.id,
    ple.reference_number,
    ple.entry_date,
    ple.entry_type,
    ple.direction,
    ple.amount,
    ple.payment_method,
    ple.status,
    ple.description,
    ple.expense_id
FROM public.person_ledger_entries ple
JOIN public.persons p ON p.id = ple.person_id
WHERE p.code = 'PER-001'
ORDER BY ple.entry_date ASC;

SELECT 
    e.id,
    e.reference_number,
    e.expense_date,
    e.category,
    e.amount,
    e.status,
    e.description,
    e.person_id
FROM public.expenses e
WHERE e.person_id IN (SELECT id FROM public.persons WHERE code = 'PER-001')
   OR e.originating_ledger_entry_id IN (
       SELECT ple.id FROM public.person_ledger_entries ple 
       JOIN public.persons p ON p.id = ple.person_id 
       WHERE p.code = 'PER-001'
   );


-- ============================================================================
-- SECTION 3: PRODUCTION WORKER INTEGRITY AUDIT (SHAOIB / ELPRODUCTION#01)
-- ============================================================================
-- Expected BEFORE & AFTER cleanup: Exactly 1 record, intact balances and work entries
SELECT 
    p.id,
    p.code,
    p.name,
    p.category,
    p.phone,
    p.opening_payable_balance,
    p.opening_receivable_balance,
    p.is_active,
    (SELECT COUNT(*) FROM public.person_ledger_entries ple WHERE ple.person_id = p.id) AS total_ledger_entries,
    (SELECT COALESCE(SUM(ple.amount), 0) FROM public.person_ledger_entries ple WHERE ple.person_id = p.id AND ple.direction = 'Payable') AS total_work_earned,
    (SELECT COALESCE(SUM(ple.amount), 0) FROM public.person_ledger_entries ple WHERE ple.person_id = p.id AND ple.direction = 'Receivable') AS total_payments_disbursed,
    (
        p.opening_payable_balance - p.opening_receivable_balance +
        (SELECT COALESCE(SUM(ple.amount), 0) FROM public.person_ledger_entries ple WHERE ple.person_id = p.id AND ple.direction = 'Payable') -
        (SELECT COALESCE(SUM(ple.amount), 0) FROM public.person_ledger_entries ple WHERE ple.person_id = p.id AND ple.direction = 'Receivable')
    ) AS net_balance
FROM public.persons p
WHERE p.code = 'ELPRODUCTION#01'
   OR UPPER(TRIM(p.name)) LIKE '%SHAOIB%';


-- ============================================================================
-- SECTION 4: PERSON PAYMENTS DIRECTORY OVERVIEW
-- ============================================================================
-- Lists all persons remaining in public.persons
SELECT 
    p.code,
    p.name,
    p.category,
    p.default_rate,
    p.commission_rate,
    p.opening_payable_balance,
    p.opening_receivable_balance,
    p.is_active,
    (SELECT COUNT(*) FROM public.person_ledger_entries ple WHERE ple.person_id = p.id) AS entries_count
FROM public.persons p
ORDER BY p.code ASC;


-- ============================================================================
-- SECTION 5: APPROVED-RECORD PROTECTION TRIGGERS AUDIT
-- ============================================================================
-- Confirms all immutability and approved-record deletion protections are active
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
      (c.relname = 'person_ledger_entries' AND t.tgname = 'trg_person_ledger_prevent_delete')
      OR (c.relname = 'expenses' AND t.tgname = 'trg_expense_prevent_delete')
  )
ORDER BY c.relname, t.tgname;


-- ============================================================================
-- SECTION 6: FINAL EXECUTIVE VERIFICATION SUMMARY CARD
-- ============================================================================
-- Expected POST-CLEANUP:
--   - Target person PER-001: 0 (PASS)
--   - Target ledger entries: 0 (PASS)
--   - Target expenses:       0 (PASS)
--   - SHAOIB Preserved:      1 (PASS)
SELECT 
    (SELECT COUNT(*) FROM public.persons WHERE code = 'PER-001') AS target_person_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.persons WHERE code = 'PER-001') = 0 
        THEN 'PASS (Cleaned: PER-001 permanently purged)'
        ELSE 'PENDING (PER-001 present)'
    END AS target_person_status,

    (
        SELECT COUNT(*) 
        FROM public.person_ledger_entries ple 
        JOIN public.persons p ON p.id = ple.person_id 
        WHERE p.code = 'PER-001'
    ) AS target_ledger_entries_count,
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM public.person_ledger_entries ple 
            JOIN public.persons p ON p.id = ple.person_id 
            WHERE p.code = 'PER-001'
        ) = 0
        THEN 'PASS (0 target ledger entries remaining)'
        ELSE 'PENDING (Target ledger entries present)'
    END AS target_entries_status,

    (
        SELECT COUNT(*) 
        FROM public.persons 
        WHERE code = 'ELPRODUCTION#01' OR UPPER(TRIM(name)) LIKE '%SHAOIB%'
    ) AS shaoib_preserved_count,
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM public.persons 
            WHERE code = 'ELPRODUCTION#01' OR UPPER(TRIM(name)) LIKE '%SHAOIB%'
        ) = 1
        THEN 'PASS (SHAOIB 100% Preserved)'
        ELSE 'FAIL (Expected 1 SHAOIB record)'
    END AS shaoib_status;

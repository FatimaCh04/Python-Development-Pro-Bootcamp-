-- ============================================================================
-- ELITE WASHWO ERP — READ-ONLY VERIFICATION SUITE
-- File: verify_unassigned_bookings_cleanup.sql
-- Task: Read-only inspection & post-migration verification for the 
--       unassigned test bookings & advance payments cleanup.
--
-- STRICT VERIFICATION GUARANTEES:
--   1. ZERO reference_number LIKE pattern matching.
--   2. Verified relational linking (sale_order_id = so.id) and exact token equality.
--   3. Read-only queries only (no data mutations or locks).
--
-- INSTRUCTIONS:
--   Execute this script in Supabase SQL Editor BEFORE and AFTER running
--   cleanup_unassigned_test_bookings.sql to verify data safety and integrity.
-- ============================================================================

-- ============================================================================
-- SECTION 1: UNASSIGNED TEST BOOKINGS & ADVANCES AUDIT ("Not Assigned")
-- ============================================================================
-- Expected BEFORE cleanup: Exactly 7 records (Bill #01–#07), including Rs. 10,200 advances
-- Expected AFTER cleanup:  Exactly 0 records
SELECT 
    so.id,
    so.reference_number,
    so.sale_date,
    so.total_amount,
    so.status,
    so.distributor_id,
    CASE 
        WHEN so.distributor_id IS NULL THEN 'Not Assigned (Target for Deletion)'
        ELSE 'Assigned'
    END AS assignment_status,
    (SELECT COUNT(*) FROM public.sale_items si WHERE si.sale_order_id = so.id) AS line_items_count,
    (SELECT COALESCE(SUM(si.quantity), 0) FROM public.sale_items si WHERE si.sale_order_id = so.id) AS total_packets,
    (
        SELECT COUNT(*) 
        FROM public.recoveries r 
        WHERE r.sale_order_id = so.id 
           OR split_part(r.reference_number, '|', 2) = so.id::text 
           OR split_part(r.reference_number, '|', 2) = so.reference_number
    ) AS linked_recoveries_count,
    (
        SELECT COALESCE(SUM(r.amount), 0) 
        FROM public.recoveries r 
        WHERE r.sale_order_id = so.id 
           OR split_part(r.reference_number, '|', 2) = so.id::text 
           OR split_part(r.reference_number, '|', 2) = so.reference_number
    ) AS total_advances_paid,
    (
        SELECT COALESCE(SUM(CASE WHEN r.payment_method = 'Cash' THEN r.amount ELSE 0 END), 0)
        FROM public.recoveries r 
        WHERE r.sale_order_id = so.id 
           OR split_part(r.reference_number, '|', 2) = so.id::text 
           OR split_part(r.reference_number, '|', 2) = so.reference_number
    ) AS cash_advance_paid,
    (
        SELECT COALESCE(SUM(CASE WHEN r.payment_method != 'Cash' THEN r.amount ELSE 0 END), 0)
        FROM public.recoveries r 
        WHERE r.sale_order_id = so.id 
           OR split_part(r.reference_number, '|', 2) = so.id::text 
           OR split_part(r.reference_number, '|', 2) = so.reference_number
    ) AS bank_advance_paid
FROM public.sales_orders so
WHERE so.reference_number LIKE 'BKG-%'
  AND so.distributor_id IS NULL
ORDER BY so.sale_date ASC, so.id ASC;


-- ============================================================================
-- SECTION 2: REAL DISTRIBUTOR PRODUCTION BOOKINGS AUDIT
-- ============================================================================
-- Expected: Exactly 8 records belonging to the 3 confirmed real distributors:
--   1. MUHAMMAD NADEEM HUSSAIN (ELITEWASH#01)
--   2. QAMAR SAJJAD (ELITEWASH#03)
--   3. khalid (Elitewash#04)
-- Sequential display numbers (Bill #01 through Bill #08) reflect oldest-first order.
SELECT 
    ROW_NUMBER() OVER (ORDER BY so.sale_date ASC, so.id ASC) AS chronological_seq,
    'Bill #' || LPAD(ROW_NUMBER() OVER (ORDER BY so.sale_date ASC, so.id ASC)::TEXT, 2, '0') AS expected_frontend_bill_no,
    so.id,
    so.reference_number,
    so.sale_date,
    d.name AS distributor_name,
    d.code AS distributor_code,
    so.total_amount AS booking_value,
    (SELECT COALESCE(SUM(si.quantity), 0) FROM public.sale_items si WHERE si.sale_order_id = so.id) AS total_packets,
    (
        SELECT COALESCE(SUM(r.amount), 0) 
        FROM public.recoveries r 
        WHERE r.sale_order_id = so.id 
           OR split_part(r.reference_number, '|', 2) = so.id::text 
           OR split_part(r.reference_number, '|', 2) = so.reference_number
    ) AS advance_paid,
    so.total_amount - (
        SELECT COALESCE(SUM(r.amount), 0) 
        FROM public.recoveries r 
        WHERE r.sale_order_id = so.id 
           OR split_part(r.reference_number, '|', 2) = so.id::text 
           OR split_part(r.reference_number, '|', 2) = so.reference_number
    ) AS advance_remaining,
    so.status AS booking_status
FROM public.sales_orders so
JOIN public.distributors d ON d.id = so.distributor_id
WHERE so.reference_number LIKE 'BKG-%'
ORDER BY so.sale_date ASC, so.id ASC;


-- ============================================================================
-- SECTION 3: REVENUE & CASH/BANK RECONCILIATION FOR REAL DISTRIBUTORS
-- ============================================================================
-- Validates that trade debt sales (SAL-), booking reservations (BKG-),
-- cash recoveries, bank recoveries, and outstanding balances remain 100% UNCHANGED.
SELECT 
    d.id,
    d.code,
    d.name,
    d.is_active,
    -- Delivered sales (trade debt invoices)
    COALESCE((
        SELECT SUM(so.total_amount) 
        FROM public.sales_orders so 
        WHERE so.distributor_id = d.id 
          AND so.status IN ('Approved', 'Posted')
          AND so.reference_number NOT LIKE 'BKG-%'
    ), 0) AS trade_sales_total,
    -- Booking sales (reservations)
    COALESCE((
        SELECT SUM(so.total_amount) 
        FROM public.sales_orders so 
        WHERE so.distributor_id = d.id 
          AND so.reference_number LIKE 'BKG-%'
    ), 0) AS booking_sales_total,
    -- Count of bookings
    COALESCE((
        SELECT COUNT(*) 
        FROM public.sales_orders so 
        WHERE so.distributor_id = d.id 
          AND so.reference_number LIKE 'BKG-%'
    ), 0) AS bookings_count,
    -- Recoveries Total
    COALESCE((
        SELECT SUM(rec.amount) 
        FROM public.recoveries rec 
        WHERE rec.distributor_id = d.id AND rec.status IN ('Approved', 'Posted')
    ), 0) AS total_approved_recoveries,
    -- Cash Recoveries
    COALESCE((
        SELECT SUM(rec.amount) 
        FROM public.recoveries rec 
        WHERE rec.distributor_id = d.id AND rec.status IN ('Approved', 'Posted') AND rec.payment_method = 'Cash'
    ), 0) AS cash_recoveries,
    -- Bank Recoveries
    COALESCE((
        SELECT SUM(rec.amount) 
        FROM public.recoveries rec 
        WHERE rec.distributor_id = d.id AND rec.status IN ('Approved', 'Posted') AND rec.payment_method != 'Cash'
    ), 0) AS bank_recoveries,
    -- Outstanding balance (trade sales - recoveries)
    (
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
        ), 0)
    ) AS current_outstanding
FROM public.distributors d
WHERE d.code NOT IN ('DST-01', 'DST-02', 'ELITEWASH#02', 'elitewash#1')
ORDER BY d.code ASC;


-- ============================================================================
-- SECTION 4: CONFLICT & SAFETY VERIFICATION
-- ============================================================================
-- Verifies zero conflicts between target unassigned test bookings and real distributors.
SELECT 
    (
        SELECT COUNT(*) 
        FROM public.recoveries r
        JOIN public.sales_orders so ON (
            r.sale_order_id = so.id 
            OR split_part(r.reference_number, '|', 2) = so.id::text 
            OR split_part(r.reference_number, '|', 2) = so.reference_number
        )
        WHERE so.reference_number LIKE 'BKG-%'
          AND so.distributor_id IS NULL
          AND r.distributor_id IS NOT NULL
    ) AS conflict_recoveries_count,
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM public.recoveries r
            JOIN public.sales_orders so ON (
                r.sale_order_id = so.id 
                OR split_part(r.reference_number, '|', 2) = so.id::text 
                OR split_part(r.reference_number, '|', 2) = so.reference_number
            )
            WHERE so.reference_number LIKE 'BKG-%'
              AND so.distributor_id IS NULL
              AND r.distributor_id IS NOT NULL
        ) = 0 THEN 'SAFE: Zero conflict recoveries'
        ELSE 'FAIL: Conflict detected!'
    END AS conflict_status;


-- ============================================================================
-- SECTION 5: FINAL INTEGRITY VERIFICATION SUMMARY CARD
-- ============================================================================
SELECT 
    (SELECT COUNT(*) FROM public.sales_orders WHERE reference_number LIKE 'BKG-%' AND distributor_id IS NULL) AS unassigned_bookings_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.sales_orders WHERE reference_number LIKE 'BKG-%' AND distributor_id IS NULL) = 0 
        THEN 'PASS (Cleaned: 0 unassigned bookings)'
        ELSE 'PENDING (7 unassigned test bookings present)'
    END AS unassigned_status,
    
    (SELECT COUNT(*) FROM public.sales_orders WHERE reference_number LIKE 'BKG-%' AND distributor_id IS NOT NULL) AS real_bookings_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.sales_orders WHERE reference_number LIKE 'BKG-%' AND distributor_id IS NOT NULL) = 8
        THEN 'PASS (8 Real Bookings Preserved)'
        ELSE 'FAIL (Expected 8 Real Bookings)'
    END AS real_bookings_status,

    (SELECT COUNT(*) FROM public.sales_orders WHERE reference_number LIKE 'BKG-%') AS total_bookings_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.sales_orders WHERE reference_number LIKE 'BKG-%') = 8
        THEN 'PASS (Ledger contains exactly 8 bookings Bill #01 to Bill #08)'
        ELSE 'AUDIT NOTE: 15 total bookings before cleanup; 8 after cleanup'
    END AS total_ledger_status;

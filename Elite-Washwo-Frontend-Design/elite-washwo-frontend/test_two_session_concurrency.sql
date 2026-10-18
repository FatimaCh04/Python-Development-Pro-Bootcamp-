-- ==============================================================================
-- ELITE WASHWO ERP — TWO-SESSION CONCURRENCY VERIFICATION TEST SUITE
-- Target: Supabase PostgreSQL 17.6 Test/Staging Environment
-- SAFETY NOTICE: For staging execution across two parallel database connections.
-- DO NOT EXECUTE ON PRODUCTION.
-- ==============================================================================
--
-- Instructions:
-- Open TWO independent database connections in psql, Supabase SQL Editor, or DBeaver:
--   Connection 1 = [SESSION A]
--   Connection 2 = [SESSION B]
--
-- Follow the exact interleaved step execution order (Step A1 -> Step B1 -> Step A2 ...)
-- ==============================================================================

-- ==============================================================================
-- RACE TEST 1: ATOMIC CROSS-BOOKING WAREHOUSE STOCK CONCURRENCY
-- Scenario: Only 10 pkts available in factory warehouse.
-- Two independent bookings (Booking A & Booking B) attempt to dispatch 10 pkts simultaneously.
-- Expected: Session A acquires lock, succeeds. Session B blocks, wakes up, detects 0 stock, and aborts.
-- ==============================================================================

-- [SETUP - Run once in Session A]
-- Ensure test packaging has exactly 10 pkts of sellable stock
-- Ensure Booking A and Booking B exist for 10 pkts each

-- Step A1: [SESSION A] Begin transaction and initiate dispatch for Booking A
BEGIN;
SELECT public.dispatch_partial_booking_fulfillment(
    'BKG-A-UUID',
    '[{"booking_item_id": "ITEM-A-UUID", "packaging_id": "PKG-UUID", "quantity": 10, "unit_price": 350.00}]'::JSONB,
    '2026-10-18 10:00:00+00'::TIMESTAMPTZ,
    'Session A dispatch'
);
-- Notice: product_packaging row is now locked FOR UPDATE by Session A! DO NOT COMMIT YET.

-- Step B1: [SESSION B] Simultaneously attempt dispatch for Booking B on same packaging
BEGIN;
SELECT public.dispatch_partial_booking_fulfillment(
    'BKG-B-UUID',
    '[{"booking_item_id": "ITEM-B-UUID", "packaging_id": "PKG-UUID", "quantity": 10, "unit_price": 350.00}]'::JSONB,
    '2026-10-18 10:00:00+00'::TIMESTAMPTZ,
    'Session B dispatch'
);
-- OBSERVATION: Session B immediately BLOCKS (waits on row lock held by Session A).

-- Step A2: [SESSION A] Commit transaction
COMMIT;
-- OBSERVATION: Session A commits successfully, creating SAL-A and deducting 10 pkts.

-- Step B2: [SESSION B] Check Session B output
-- OBSERVATION: Session B unblocks, re-evaluates warehouse sellable stock under exclusive lock,
-- sees Available = 0 pkts, and terminates with exception:
-- 'ERROR: Insufficient factory warehouse sellable stock for packaging PKG-UUID. Available: 0 pkts, Total Requested: 10 pkts'
ROLLBACK;


-- ==============================================================================
-- RACE TEST 2: CONCURRENT IDEMPOTENCY KEY RACE
-- Scenario: Network retry submits the identical idempotency key simultaneously in two sessions.
-- Expected: One session inserts row; second session hits unique_violation, independently retrieves
-- the existing record, verifies payload hash match, and returns idempotent_replay: true.
-- ==============================================================================

-- Step A1: [SESSION A] Begin transaction with idempotency key
BEGIN;
SELECT public.allocate_recovery_to_invoice(
    'REC-UUID',
    'SALE-UUID',
    1000.00,
    'Concurrent idempotency test',
    'IDEM-RACE-KEY-001'
);
-- Row inserted into invoice_payment_allocations; uncommitted.

-- Step B1: [SESSION B] Simultaneously attempt identical allocation with same key
SELECT public.allocate_recovery_to_invoice(
    'REC-UUID',
    'SALE-UUID',
    1000.00,
    'Concurrent idempotency test',
    'IDEM-RACE-KEY-001'
);
-- OBSERVATION: Session B waits for Session A's transaction resolution.

-- Step A2: [SESSION A] Commit
COMMIT;

-- Step B2: [SESSION B] Output evaluation
-- OBSERVATION: Session B unblocks, catches unique_violation, fetches committed row,
-- verifies idempotency_hash match, and returns:
-- {"success": true, "idempotent_replay": true, "allocated_amount": 1000.00, "status": "Approved"}


-- ==============================================================================
-- RACE TEST 3: INVOICE OVER-ALLOCATION RACE (STRICT CAPPING)
-- Scenario: Invoice has payable balance of Rs. 1,000.
-- Session A attempts to allocate Rs. 700. Session B attempts to allocate Rs. 700.
-- Expected: Row-level lock on sales_orders serializes requests. Session A allocates Rs. 700.
-- Session B sees remaining balance is only Rs. 300, and is strictly rejected.
-- ==============================================================================

-- Step A1: [SESSION A]
BEGIN;
SELECT public.allocate_recovery_to_invoice('REC-A-UUID', 'SALE-UUID', 700.00, 'Session A allocation');

-- Step B1: [SESSION B]
BEGIN;
SELECT public.allocate_recovery_to_invoice('REC-B-UUID', 'SALE-UUID', 700.00, 'Session B allocation');
-- OBSERVATION: Session B blocks on sales_orders row lock.

-- Step A2: [SESSION A]
COMMIT;

-- Step B2: [SESSION B]
-- OBSERVATION: Session B unblocks, recalculates v_available_sale (1000 - 700 = 300),
-- sees 700 > 300, and aborts with:
-- 'ERROR: Cannot allocate Rs. 700: Invoice payable balance is only Rs. 300 (Strictly capped at invoice total).'
ROLLBACK;


-- ==============================================================================
-- RACE TEST 4: CONCURRENT PHYSICAL RETURNS RACE (RETURN CAPPING)
-- Scenario: Sale issued 10 pkts total.
-- Session A attempts return of 8 pkts. Session B attempts return of 8 pkts simultaneously.
-- Expected: Row lock on sales_orders serializes returns. Session A logs 8 pkts.
-- Session B sees 8 pkts already returned, calculates 8 + 8 > 10, and aborts.
-- ==============================================================================

-- Step A1: [SESSION A]
BEGIN;
SELECT public.record_verified_distributor_stock_return(
    'SALE-UUID', 'DIST-UUID', 'PKG-UUID', 8, 'Good', 'Session A return of 8 pkts'
);

-- Step B1: [SESSION B]
BEGIN;
SELECT public.record_verified_distributor_stock_return(
    'SALE-UUID', 'DIST-UUID', 'PKG-UUID', 8, 'Good', 'Session B return of 8 pkts'
);
-- OBSERVATION: Session B blocks on sales_orders row lock.

-- Step A2: [SESSION A]
COMMIT;

-- Step B2: [SESSION B]
-- OBSERVATION: Session B unblocks, calculates v_already_returned_qty = 8,
-- detects 8 + 8 = 16 > 10, and aborts with:
-- 'ERROR: Return quantity exceeds issued quantity: Sale issued 10 pkts, already returned 8 pkts, requested return 8 pkts (Max returnable: 2 pkts)'
ROLLBACK;

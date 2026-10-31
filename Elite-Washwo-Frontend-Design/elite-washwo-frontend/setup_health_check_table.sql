-- ======================================================================================
-- ELITE WASH ERP — DEDICATED READ-ONLY HEALTH CHECK TABLE FOR SUPABASE ACTIVITY
-- Script: setup_health_check_table.sql
--
-- PURPOSE:
--   Creates a lightweight, single-row table used by the scheduled GitHub Actions
--   workflow to generate legitimate database activity on Supabase.
--
-- SAFETY:
--   - Isolated from all operational business tables.
--   - Strictly read-only for public/anon/authenticated roles.
--   - Zero risk to orders, recoveries, expenses, distributors, or inventory.
-- ======================================================================================

BEGIN;

-- 1. Create isolated lightweight health check table
CREATE TABLE IF NOT EXISTS public.system_health_check (
    id INT PRIMARY KEY DEFAULT 1,
    service_name TEXT NOT NULL DEFAULT 'Elite Wash ERP Supabase Engine',
    status TEXT NOT NULL DEFAULT 'HEALTHY',
    last_verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Populate single static row
INSERT INTO public.system_health_check (id, service_name, status, last_verified_at)
VALUES (1, 'Elite Wash ERP Supabase Engine', 'HEALTHY', NOW())
ON CONFLICT (id) DO UPDATE 
SET status = 'HEALTHY',
    last_verified_at = NOW();

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.system_health_check ENABLE ROW LEVEL SECURITY;

-- 4. Grant read-only SELECT to anon and authenticated roles
DROP POLICY IF EXISTS "Public and staff can read health check" ON public.system_health_check;
CREATE POLICY "Public and staff can read health check" ON public.system_health_check
    FOR SELECT USING (true);

-- 5. Revoke write permissions explicitly from public, anon, and authenticated roles
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.system_health_check FROM anon, authenticated;

COMMIT;

-- Verification query
SELECT * FROM public.system_health_check;

-- ===============================================================================
-- PHASE 1: FOUNDATION ALIGNMENT MIGRATION
-- Adds required columns to support upcoming Teacher Requirements (Expenses, Recoveries, Settings)
-- ===============================================================================

-- 1. RECOVERIES: Add fields for Today's Recovery requirements
ALTER TABLE public.recoveries
ADD COLUMN IF NOT EXISTS account_detail text,
ADD COLUMN IF NOT EXISTS tid text,
ADD COLUMN IF NOT EXISTS notes text;

-- 2. EXPENSES: Add fields for new Expense Structure
ALTER TABLE public.expenses
ADD COLUMN IF NOT EXISTS account_detail text,
ADD COLUMN IF NOT EXISTS tid text,
ADD COLUMN IF NOT EXISTS head text;

-- 3. SETTINGS: Global settings table for Advertisement/Welfare adjustments
CREATE TABLE IF NOT EXISTS public.global_settings (
    id integer PRIMARY KEY DEFAULT 1,
    advertisement_opening_balance numeric DEFAULT 0,
    welfare_opening_balance numeric DEFAULT 0,
    updated_at timestamptz DEFAULT now()
);

-- Ensure only one row exists for settings
INSERT INTO public.global_settings (id, advertisement_opening_balance, welfare_opening_balance)
VALUES (1, 0, 0)
ON CONFLICT (id) DO NOTHING;

-- RLS for global_settings
ALTER TABLE public.global_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Super_Admin can manage global_settings"
    ON public.global_settings
    FOR ALL
    TO authenticated
    USING ( (SELECT role FROM profiles WHERE id = auth.uid()) = 'Super_Admin' );

CREATE POLICY "Everyone can read global_settings"
    ON public.global_settings
    FOR SELECT
    TO authenticated
    USING ( true );

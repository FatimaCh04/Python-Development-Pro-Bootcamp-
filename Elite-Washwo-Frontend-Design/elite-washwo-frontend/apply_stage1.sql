-- ==============================================================================
-- STAGE 1: COMPLETE SCHEMA & RLS FOUNDATION (IDEMPOTENT MIGRATION)
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ENUMS (Idempotent creation)
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('Super_Admin', 'Manager', 'Salesman');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE inventory_category AS ENUM ('Sellable Stock', 'Damaged Stock', 'Expired Stock', 'Unsellable Stock');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE transaction_type AS ENUM (
        'Production', 'Purchase', 'Salesman_Issue', 'Sale', 
        'Salesman_Good_Return', 'Salesman_Damaged_Return', 
        'Customer_Good_Return', 'Customer_Damaged_Return', 
        'Adjustment', 'Expiry', 'Damage', 'Reversal'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE transaction_status AS ENUM ('Pending', 'Submitted', 'Approved', 'Posted', 'Cancelled');
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- 2. CORE TABLES (Idempotent)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    role user_role NOT NULL DEFAULT 'Salesman',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS salesmen (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE UNIQUE,
    code TEXT NOT NULL UNIQUE,
    route TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_packaging (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    units_per_package INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    packaging_id UUID NOT NULL REFERENCES product_packaging(id) ON DELETE CASCADE,
    unit_cost DECIMAL(12, 2) NOT NULL,
    sales_price DECIMAL(12, 2) NOT NULL,
    effective_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    default_salesman_id UUID REFERENCES salesmen(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_number TEXT NOT NULL UNIQUE,
    transaction_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    packaging_id UUID NOT NULL REFERENCES product_packaging(id),
    category inventory_category NOT NULL,
    transaction_type transaction_type NOT NULL,
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(12, 2) NOT NULL,
    total_cost DECIMAL(12, 2) NOT NULL,
    salesman_id UUID REFERENCES salesmen(id),
    customer_id UUID REFERENCES customers(id),
    status transaction_status NOT NULL DEFAULT 'Pending',
    notes TEXT,
    created_by UUID REFERENCES profiles(id),
    approved_by UUID REFERENCES profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
DO $$ BEGIN
    ALTER TABLE inventory_transactions ADD CONSTRAINT chk_total_cost CHECK (total_cost = quantity * unit_cost);
EXCEPTION WHEN duplicate_object THEN null; END $$;
CREATE INDEX IF NOT EXISTS idx_inv_trans_salesman ON inventory_transactions(salesman_id);
CREATE INDEX IF NOT EXISTS idx_inv_trans_type ON inventory_transactions(transaction_type);

CREATE TABLE IF NOT EXISTS sales_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_number TEXT NOT NULL UNIQUE,
    sale_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    salesman_id UUID NOT NULL REFERENCES salesmen(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    total_amount DECIMAL(12, 2) NOT NULL,
    status transaction_status NOT NULL DEFAULT 'Submitted',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sale_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_order_id UUID NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
    packaging_id UUID NOT NULL REFERENCES product_packaging(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL
);
DO $$ BEGIN
    ALTER TABLE sale_items ADD CONSTRAINT chk_sale_subtotal CHECK (subtotal = quantity * unit_price);
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS recoveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_number TEXT NOT NULL UNIQUE,
    recovery_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    salesman_id UUID NOT NULL REFERENCES salesmen(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    sale_order_id UUID REFERENCES sales_orders(id),
    amount DECIMAL(12, 2) NOT NULL,
    payment_method TEXT NOT NULL,
    status transaction_status NOT NULL DEFAULT 'Submitted',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
DO $$ BEGIN
    ALTER TABLE recoveries ADD CONSTRAINT chk_payment_method CHECK (payment_method IN ('Cash', 'Bank', 'Cheque'));
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_number TEXT NOT NULL UNIQUE,
    expense_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    salesman_id UUID NOT NULL REFERENCES salesmen(id),
    category TEXT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    description TEXT,
    paid_by TEXT DEFAULT 'Salesman',
    payment_method TEXT DEFAULT 'Cash',
    status transaction_status NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_closings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    closing_date DATE NOT NULL,
    salesman_id UUID NOT NULL REFERENCES salesmen(id),
    submitted_stock JSONB,
    submitted_cash DECIMAL(12, 2),
    expected_stock JSONB,
    expected_cash DECIMAL(12, 2),
    status transaction_status NOT NULL DEFAULT 'Pending',
    approved_by UUID REFERENCES profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(closing_date, salesman_id)
);

CREATE TABLE IF NOT EXISTS variances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    daily_closing_id UUID NOT NULL REFERENCES daily_closings(id) ON DELETE CASCADE,
    variance_type TEXT NOT NULL,
    amount_or_quantity DECIMAL(12, 2) NOT NULL,
    reason TEXT,
    status transaction_status NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    action TEXT NOT NULL,
    old_data JSONB,
    new_data JSONB,
    performed_by UUID REFERENCES profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permissions (
    id TEXT PRIMARY KEY,
    description TEXT,
    module TEXT
);

CREATE TABLE IF NOT EXISTS user_permissions (
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    permission_id TEXT REFERENCES permissions(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, permission_id)
);

-- Seed Permissions (using ON CONFLICT DO NOTHING)
INSERT INTO permissions (id, module, description) VALUES
('sales.view', 'Sales', 'View all sales'),
('sales.create', 'Sales', 'Create new sales'),
('sales.edit', 'Sales', 'Edit pending sales'),
('sales.approve', 'Sales', 'Approve submitted sales'),
('inventory.view', 'Inventory', 'View all inventory transactions and balances'),
('inventory.create', 'Inventory', 'Create inventory issues and returns'),
('inventory.adjust', 'Inventory', 'Adjust inventory quantities'),
('inventory.approve', 'Inventory', 'Approve inventory transactions'),
('returns.view', 'Returns', 'View all returns'),
('returns.create', 'Returns', 'Create returns'),
('returns.approve', 'Returns', 'Approve pending returns'),
('expenses.view', 'Expenses', 'View all expenses'),
('expenses.create', 'Expenses', 'Create company expenses'),
('expenses.approve', 'Expenses', 'Approve submitted expenses'),
('expenses.reimburse', 'Expenses', 'Mark expenses as reimbursed'),
('ledger.view', 'Ledger', 'View master ledgers'),
('ledger.export', 'Ledger', 'Export ledger data'),
('settlement.view', 'Settlement', 'View settlements'),
('settlement.create', 'Settlement', 'Create settlements'),
('settlement.approve', 'Settlement', 'Approve settlements'),
('audit.view', 'Audit', 'View audit logs'),
('reports.view', 'Reports', 'View business reports'),
('settings.manage', 'Settings', 'Manage system settings')
ON CONFLICT (id) DO NOTHING;

-- 3. VIEWS (CREATE OR REPLACE)
CREATE OR REPLACE VIEW warehouse_inventory_balances AS
SELECT 
    packaging_id,
    category,
    SUM(CASE WHEN transaction_type IN ('Production', 'Purchase', 'Salesman_Good_Return', 'Customer_Good_Return') THEN quantity
             WHEN transaction_type IN ('Salesman_Issue', 'Adjustment', 'Damage', 'Expiry') THEN -quantity
             ELSE 0 END) as balance_quantity
FROM inventory_transactions
WHERE status IN ('Approved', 'Posted') AND salesman_id IS NULL
GROUP BY packaging_id, category;

CREATE OR REPLACE VIEW salesman_stock_balances AS
SELECT 
    salesman_id,
    packaging_id,
    SUM(CASE WHEN transaction_type = 'Salesman_Issue' THEN quantity
             WHEN transaction_type IN ('Sale', 'Salesman_Good_Return', 'Salesman_Damaged_Return') THEN -quantity
             ELSE 0 END) as balance_quantity
FROM inventory_transactions
WHERE status IN ('Approved', 'Posted') AND salesman_id IS NOT NULL
GROUP BY salesman_id, packaging_id;

CREATE OR REPLACE VIEW customer_ledger AS
SELECT 
    customer_id,
    SUM(CASE WHEN type = 'Sale' THEN amount ELSE -amount END) as outstanding_balance
FROM (
    SELECT customer_id, 'Sale' as type, total_amount as amount FROM sales_orders WHERE status IN ('Approved', 'Posted')
    UNION ALL
    SELECT customer_id, 'Recovery' as type, amount FROM recoveries WHERE status IN ('Approved', 'Posted')
) as combined
GROUP BY customer_id;

-- 4. HELPER FUNCTIONS
CREATE OR REPLACE FUNCTION public.auth_user_role() RETURNS public.user_role AS $$
DECLARE
  v_role public.user_role;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid() LIMIT 1;
  RETURN v_role;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE OR REPLACE FUNCTION public.auth_salesman_id() RETURNS UUID AS $$
DECLARE
  v_sid UUID;
BEGIN
  SELECT id INTO v_sid FROM public.salesmen WHERE profile_id = auth.uid() LIMIT 1;
  RETURN v_sid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE OR REPLACE FUNCTION public.has_permission(req_perm TEXT) RETURNS BOOLEAN AS $$
DECLARE
    u_role public.user_role;
BEGIN
    SELECT role INTO u_role FROM public.profiles WHERE id = auth.uid() LIMIT 1;
    IF u_role = 'Super_Admin' THEN RETURN TRUE; END IF;
    IF u_role = 'Manager' THEN
        RETURN EXISTS (SELECT 1 FROM public.user_permissions WHERE user_id = auth.uid() AND permission_id = req_perm);
    END IF;
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- 5. AUDIT LOG TRIGGER
CREATE OR REPLACE FUNCTION log_audit_event() RETURNS TRIGGER AS $$
DECLARE
    user_id UUID;
BEGIN
    BEGIN
        user_id := auth.uid();
    EXCEPTION WHEN OTHERS THEN
        user_id := NULL;
    END;
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (table_name, record_id, action, new_data, performed_by) VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW), user_id);
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (table_name, record_id, action, old_data, new_data, performed_by) VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), user_id);
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_logs (table_name, record_id, action, old_data, performed_by) VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD), user_id);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

DO $$ BEGIN
    DROP TRIGGER IF EXISTS audit_inventory_transactions ON inventory_transactions;
    CREATE TRIGGER audit_inventory_transactions AFTER INSERT OR UPDATE OR DELETE ON inventory_transactions FOR EACH ROW EXECUTE FUNCTION log_audit_event();
    
    DROP TRIGGER IF EXISTS audit_sales_orders ON sales_orders;
    CREATE TRIGGER audit_sales_orders AFTER INSERT OR UPDATE OR DELETE ON sales_orders FOR EACH ROW EXECUTE FUNCTION log_audit_event();
    
    DROP TRIGGER IF EXISTS audit_recoveries ON recoveries;
    CREATE TRIGGER audit_recoveries AFTER INSERT OR UPDATE OR DELETE ON recoveries FOR EACH ROW EXECUTE FUNCTION log_audit_event();
END $$;

-- 6. STRICT RLS POLICIES (DROP EXISTING & RECREATE)
DO $$ 
DECLARE 
  pol RECORD; 
BEGIN 
  FOR pol IN SELECT policyname, tablename FROM pg_policies WHERE schemaname = 'public' 
  LOOP 
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', pol.policyname, pol.tablename); 
  END LOOP; 
END $$;

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE salesmen ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_packaging ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE sale_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE recoveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_closings ENABLE ROW LEVEL SECURITY;
ALTER TABLE variances ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_permissions ENABLE ROW LEVEL SECURITY;

-- Profiles
CREATE POLICY "Super Admins can manage all profiles" ON profiles FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Users can read own profile" ON profiles FOR SELECT USING (id = auth.uid());
CREATE POLICY "Managers can read profiles" ON profiles FOR SELECT USING (public.has_permission('settings.manage'));

-- Salesmen
CREATE POLICY "Super Admins can manage all salesmen" ON salesmen FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Managers can read salesmen" ON salesmen FOR SELECT USING (public.auth_user_role() = 'Manager');
CREATE POLICY "Salesmen can read salesmen" ON salesmen FOR SELECT USING (public.auth_user_role() = 'Salesman');

-- Products & Pricing
CREATE POLICY "Anyone can view products" ON products FOR SELECT USING (true);
CREATE POLICY "Anyone can view packaging" ON product_packaging FOR SELECT USING (true);
CREATE POLICY "Anyone can view prices" ON product_prices FOR SELECT USING (true);
CREATE POLICY "Super Admins manage products" ON products FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Super Admins manage packaging" ON product_packaging FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Super Admins manage prices" ON product_prices FOR ALL USING (public.auth_user_role() = 'Super_Admin');

-- Customers
CREATE POLICY "Anyone can view customers" ON customers FOR SELECT USING (true);
CREATE POLICY "Super Admins manage customers" ON customers FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Managers manage customers" ON customers FOR ALL USING (public.has_permission('settings.manage'));

-- Inventory Transactions (Strict)
CREATE POLICY "Admins manage inventory" ON inventory_transactions FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Managers view inventory" ON inventory_transactions FOR SELECT USING (public.has_permission('inventory.view') OR public.has_permission('returns.view'));
CREATE POLICY "Managers insert inventory" ON inventory_transactions FOR INSERT WITH CHECK (public.has_permission('inventory.create') OR public.has_permission('returns.create'));
CREATE POLICY "Managers update inventory" ON inventory_transactions FOR UPDATE USING (public.has_permission('inventory.approve') OR public.has_permission('returns.approve'));
CREATE POLICY "Salesmen view own inventory" ON inventory_transactions FOR SELECT USING (salesman_id = public.auth_salesman_id());
CREATE POLICY "Salesmen insert pending returns" ON inventory_transactions FOR INSERT WITH CHECK (
    salesman_id = public.auth_salesman_id() AND 
    transaction_type IN ('Salesman_Good_Return', 'Salesman_Damaged_Return') AND
    status = 'Pending'
);
-- Notice: Salesmen have NO update policy on inventory_transactions, preventing self-approval.

-- Sales Orders
CREATE POLICY "Admins manage sales" ON sales_orders FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Managers view sales" ON sales_orders FOR SELECT USING (public.has_permission('sales.view'));
CREATE POLICY "Managers insert sales" ON sales_orders FOR INSERT WITH CHECK (public.has_permission('sales.create'));
CREATE POLICY "Managers update sales" ON sales_orders FOR UPDATE USING (public.has_permission('sales.edit') OR public.has_permission('sales.approve'));
CREATE POLICY "Salesmen view own sales" ON sales_orders FOR SELECT USING (salesman_id = public.auth_salesman_id());
CREATE POLICY "Salesmen insert pending sales" ON sales_orders FOR INSERT WITH CHECK (salesman_id = public.auth_salesman_id() AND status = 'Submitted');
CREATE POLICY "Salesmen update pending sales" ON sales_orders FOR UPDATE USING (salesman_id = public.auth_salesman_id() AND status IN ('Pending', 'Submitted')) WITH CHECK (status IN ('Pending', 'Submitted'));

-- Sale Items
CREATE POLICY "Admins manage sale items" ON sale_items FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Anyone view sale items" ON sale_items FOR SELECT USING (true);
CREATE POLICY "Salesmen insert sale items" ON sale_items FOR INSERT WITH CHECK (true);

-- Recoveries
CREATE POLICY "Admins manage recoveries" ON recoveries FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Managers view recoveries" ON recoveries FOR SELECT USING (public.has_permission('sales.view'));
CREATE POLICY "Managers insert recoveries" ON recoveries FOR INSERT WITH CHECK (public.has_permission('sales.create'));
CREATE POLICY "Managers update recoveries" ON recoveries FOR UPDATE USING (public.has_permission('sales.approve'));
CREATE POLICY "Salesmen view own recoveries" ON recoveries FOR SELECT USING (salesman_id = public.auth_salesman_id());
CREATE POLICY "Salesmen insert submitted recoveries" ON recoveries FOR INSERT WITH CHECK (salesman_id = public.auth_salesman_id() AND status = 'Submitted');
-- Notice: Salesmen have NO update policy on recoveries.

-- Expenses
CREATE POLICY "Admins manage expenses" ON expenses FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Managers view expenses" ON expenses FOR SELECT USING (public.has_permission('expenses.view'));
CREATE POLICY "Managers insert expenses" ON expenses FOR INSERT WITH CHECK (public.has_permission('expenses.create'));
CREATE POLICY "Managers update expenses" ON expenses FOR UPDATE USING (public.has_permission('expenses.approve'));
CREATE POLICY "Salesmen view own expenses" ON expenses FOR SELECT USING (salesman_id = public.auth_salesman_id());
CREATE POLICY "Salesmen insert pending expenses" ON expenses FOR INSERT WITH CHECK (salesman_id = public.auth_salesman_id() AND status = 'Pending');
CREATE POLICY "Salesmen update pending expenses" ON expenses FOR UPDATE USING (salesman_id = public.auth_salesman_id() AND status = 'Pending') WITH CHECK (status = 'Pending');

-- Closings & Variances
CREATE POLICY "Admins manage closings" ON daily_closings FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Salesmen read own closings" ON daily_closings FOR SELECT USING (salesman_id = public.auth_salesman_id());
CREATE POLICY "Managers read closings" ON daily_closings FOR SELECT USING (public.has_permission('ledger.view'));
CREATE POLICY "Admins manage variances" ON variances FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Managers read variances" ON variances FOR SELECT USING (public.has_permission('ledger.view'));

-- Audit Logs
CREATE POLICY "Admins manage audit logs" ON audit_logs FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Managers view audit logs" ON audit_logs FOR SELECT USING (public.has_permission('audit.view'));
-- Notice: Audit logs are inserted by SECURITY DEFINER triggers, bypassing RLS, which is correct.

-- User Permissions
CREATE POLICY "Super Admins manage permissions" ON user_permissions FOR ALL USING (public.auth_user_role() = 'Super_Admin');
CREATE POLICY "Users read own permissions" ON user_permissions FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Anyone read permissions lookup" ON permissions FOR SELECT USING (true);


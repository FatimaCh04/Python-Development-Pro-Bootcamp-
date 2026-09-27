import re

with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# ──────────────────────────────────────────────
# 1. REORDER NAV + rename Salesman Ledger
# ──────────────────────────────────────────────
new_nav = """const NAV = [
  { group: 'Operations', items: [
    { key: 'overview',   label: 'Dashboard',          roles: ['Super_Admin', 'Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg> },
    { key: 'distributors', label: 'Distributors',    roles: ['Super_Admin', 'Manager', 'Salesman'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg> },
    { key: 'booking',    label: 'Booking Ledger',    roles: ['Super_Admin', 'Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg> },
    { key: 'sales',      label: 'Sales',             roles: ['Super_Admin', 'Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M6 2 3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg> },
    { key: 'salesman',   label: 'Distributor Ledger',roles: null, icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-3.5 3-6 7-6s7 2.5 7 6"/></svg> },
    { key: 'stock',      label: 'Stock & Returns',   roles: null, icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/></svg> },
    { key: 'expenses',   label: 'Expenses',          roles: null, icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18"/></svg> },
    { key: 'customers',  label: 'Customers',         roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="9" cy="8" r="3"/><path d="M2 20c0-3 3-5 7-5s7 2 7 5"/><circle cx="18" cy="8" r="2.3"/><path d="M15 13.5c2.4.4 4 1.8 4 4.5"/></svg> },
  ]},
  { group: 'Product & Reports', items: [
    { key: 'product',    label: 'Surf Product',      roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M20 7l-8-4-8 4 8 4 8-4z"/><path d="M4 7v10l8 4 8-4V7"/><path d="M12 11v10"/></svg> },
    { key: 'reports',    label: 'Reports',           roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 19V5M10 19V9M16 19v-6M22 19H2"/></svg> },
  ]},
  { group: 'Finance & Control', items: [
    { key: 'settlement', label: 'Settlement',        roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 4h16v16H4z"/><path d="M8 9h8M8 13h8M8 17h4"/></svg> },
    { key: 'audit',      label: 'Audit Trail',       roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg> },
  ]},
  { group: 'System', items: [
    { key: 'settings',   label: 'Settings',          roles: ['Super_Admin'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="3"/><path d="M12 1v3M12 20v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M1 12h3M20 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/></svg> },
  ]},
];"""

# Replace entire NAV block
c = re.sub(r'const NAV = \[.*?\];', new_nav, c, flags=re.DOTALL)

# ──────────────────────────────────────────────
# 2. PAGE_TITLES updates
# ──────────────────────────────────────────────
c = c.replace("salesman: ['Salesman Ledger', 'Complete stock, financial & expense ledger per salesman'],",
              "salesman: ['Distributor Ledger', 'Complete stock, financial & expense ledger per distributor'],")
c = c.replace("stock: ['Stock & Returns', 'Salesman returns, condition tracking & daily reconciliation'],",
              "stock: ['Stock & Returns', 'Distributor returns, condition tracking & daily reconciliation'],")
c = c.replace("settlement: ['Settlement', 'Periodic salesman settlement statement'],",
              "settlement: ['Settlement', 'Periodic distributor settlement statement'],")

# ──────────────────────────────────────────────
# 3. Branding: visible text only (not variables/imports)
# ──────────────────────────────────────────────
c = c.replace('<p>Loading Elite Washwo...</p>', '<p>Loading Elite Wash...</p>')
c = c.replace('<div className="brand-name">Elite Washwo</div>', '<div className="brand-name">Elite Wash</div>')
c = c.replace('Elite Washwo ERP - All balances derived from transactions. No manual overwrite.',
              'Elite Wash ERP — All balances derived from transactions. No manual overwrite.')

# ──────────────────────────────────────────────
# 4. SalesmanPage → visible Distributor Ledger labels only
# ──────────────────────────────────────────────
# The chips show salesmen names — keep the component functional, just rename visible headings
# (inner component page header and tile labels)
c = c.replace("label: 'Current stock'", "label: 'Distributor stock'")
c = c.replace("label: 'Today's sales'", "label: \"Today's sales\"")  # keep as-is
c = c.replace("label: 'Pending reimbursement'", "label: 'Distributor expense'")

# ──────────────────────────────────────────────
# 5. Settlement: visible terminology
# ──────────────────────────────────────────────
c = c.replace('<h2>Salesman settlement</h2>', '<h2>Distributor Settlement</h2>')
c = c.replace('<label>Select Salesman</label>', '<label>Select Distributor</label>')
c = c.replace("Select a salesman above to view their settlement.",
              "Select a distributor above to view their settlement.")

# ──────────────────────────────────────────────
# 6. Customers: remove Create Sale button + "All Salesmen" filter select
# ──────────────────────────────────────────────
# Remove Create Sale button
c = c.replace("""<button className={showSale ? 'btn ghost' : 'btn primary'} onClick={()=>setShowSale(s=>!s)}>{showSale?'Cancel Sale':'Create Sale'}</button>""", '')
# Remove showSale / SalesForm render
c = c.replace("{showSale && <SalesForm onCancel={() => setShowSale(false)} onSuccess={() => {setShowSale(false); reload();}} />}", '')

# Remove the salesman filter dropdown from the header (replace "All Salesmen" select with nothing)
c = c.replace("""<select 
              value={salesmanFilter} 
              onChange={e => { setSalesmanFilter(e.target.value); setPage(1); }}
              style={{padding:'4px 8px',fontSize:12,border:'1px solid var(--line)',borderRadius:6,background:'var(--panel)',color:'var(--text)',outline:'none'}}
            >
              <option value="All">All Salesmen</option>
              {(salesmen||[]).map(s => (
                <option key={s.id} value={s.id}>{s.profiles?.full_name || s.code}</option>
              ))}
            </select>""", '')

# Remove "Salesman" column header and its td from customer table
c = c.replace('<thead><tr><th>Customer</th><th>Area</th><th>Salesman</th><th>Outstanding</th></tr></thead>',
              '<thead><tr><th>Customer</th><th>Area</th><th>Outstanding</th></tr></thead>')
c = c.replace("<td>{c.salesmen?.profiles?.full_name||'-'}</td>", '')

# Remove Salesman column from returns table
c = c.replace('<thead><tr><th>Reference</th><th>Date</th><th>Customer</th><th>Salesman</th><th>Type</th><th>Qty</th><th>Status</th></tr></thead>',
              '<thead><tr><th>Reference</th><th>Date</th><th>Customer</th><th>Type</th><th>Qty</th><th>Status</th></tr></thead>')
c = c.replace("<td>{r.salesmen?.profiles?.full_name||'-'}</td>", '')

with open('src/main.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('All targeted changes applied to main.jsx')

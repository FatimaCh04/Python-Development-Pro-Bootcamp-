import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';
import SettingsPage from './components/SettingsPage';
import DistributorsPage from './components/DistributorsPage';
import SalesPage from './components/SalesPage';
import StockPage from './components/StockPage';
import OverviewPage from './components/OverviewPage';
import ExpensesPage from './components/ExpensesPage';
import ReportsPage from './components/ReportsPage';
import BookingPage from './components/BookingPage';
import {
  fetchOverviewStats, fetchRecentAuditLogs, fetchSalesmenSnapshot, fetchChartData,
  fetchSalesmen, fetchSalesmanStats, fetchSalesmanStockLedger, fetchSalesmanFinLedger, fetchSalesmanExpLedger,
  fetchInventoryTransactions, submitStockReturn, approveTransaction,
  fetchExpenses, submitExpense, updateExpenseStatus, fetchExpenseSummary,
  fetchCustomers, addCustomer, fetchCustomerReturns,
  fetchProducts, fetchProductMovement, fetchPackagings,
  fetchSalesmanSettlement, fetchAuditLogs,
  submitSale, addProduct, updateProduct, deleteProduct
} from './lib/db';

const fmtNum = (n) => Number(n || 0).toLocaleString('en-PK');
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' }) : 'No date';
const fmtTime = (d) => d ? new Date(d).toLocaleString('en-PK', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'No date';

function useAsync(fn, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setData(await fn()); } catch (e) { setError(e.message); } finally { setLoading(false); }
  }, deps);
  useEffect(() => { load(); }, [load]);
  return { data, loading, error, reload: load };
}

function Spinner() { return React.createElement('div', { style: { padding: 40, textAlign: 'center', color: 'var(--text-dim)', fontSize: 13 } }, 'Loading...'); }
function Empty({ msg }) { return React.createElement('tr', null, React.createElement('td', { colSpan: 10, style: { textAlign: 'center', color: 'var(--text-dim)', padding: 24, fontSize: 12 } }, msg || 'No records found.')); }

function statusBadge(s) {
  const map = { Approved: 'green', Posted: 'green', Pending: 'amber', Submitted: 'amber', Cancelled: 'gray', Rejected: 'red' };
  return <span className={`badge ${map[s] || 'gray'}`}>{s}</span>;
}

function Msg({ msg }) {
  if (!msg) return null;
  const isErr = msg.startsWith('err:');
  return <div style={{ padding: '8px 12px', marginBottom: 12, borderRadius: 4, fontSize: 12, background: isErr ? 'var(--red-soft)' : 'var(--green-soft)', color: isErr ? 'var(--red)' : 'var(--green)' }}>{msg.replace(/^(ok|err):/, '')}</div>;
}



function Root() { return <AuthProvider><AppRouter /></AuthProvider>; }

function AppRouter() {
  const { session, loading } = useAuth();
  if (loading) return (
    <div className="splash-loader">
      <img src="/elitewash-logo.jpg" className="brand-mark" style={{objectFit:"cover", background:"none"}} alt="EW" />
      <p>Loading Elite Wash...</p>
    </div>
  );
  if (!session) return <Login />;
  return <App />;
}

const NAV = [
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
];

const PAGE_TITLES = {
  booking: ['Booking & Orders', 'Manage customer bookings and recoveries'],
  overview: ['Overview', new Date().toLocaleDateString('en-PK',{weekday:'long',day:'numeric',month:'long',year:'numeric'})],
  salesman: ['Distributor Ledger', 'Complete stock, financial & expense ledger per distributor'],
  stock: ['Stock & Returns', 'Distributor returns, condition tracking & daily reconciliation'],
  expenses: ['Expenses', 'Submission, approval & reimbursement tracking'],
  customers: ['Customers', 'Directory, ledgers & customer returns'],
  distributors: ['Distributors', 'Manage distributor information and commission details.'],
  product: ['Surf Product', 'Stock, pricing, movement & profitability'],
  settlement: ['Settlement', 'Periodic distributor settlement statement'],
  reports: ['Reports', 'Daily closing, movement, expense & profitability reports'],
  audit: ['Audit Trail', 'Immutable history of every transaction'],
  settings: ['Settings', 'System configuration & permission management'],
};

function AccessDenied({ msg }) {
  return (
    <div className="panel" style={{textAlign:'center',padding:'48px 24px'}}>
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--text-dim)" strokeWidth="1.4" style={{marginBottom:12}}><circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/></svg>
      <div style={{fontSize:14,fontWeight:600,marginBottom:6}}>Access Denied</div>
      <div style={{fontSize:12.5,color:'var(--text-dim)'}}>{msg || 'You do not have permission to view this page.'}</div>
    </div>
  );
}

function App() {
  const { user, role, hasPermission, logout } = useAuth();
  const displayName = user?.full_name || 'Admin';
  const displayRole = role ? role.replace(/_/g, ' ') : 'Administrator';
  const defaultPage = role === 'Salesman' ? 'salesman' : 'overview';
  const [activePage, setActivePage] = useState(defaultPage);
  const [globalSearch, setGlobalSearch] = useState('');

  useEffect(() => {
    if (role === 'Salesman' && activePage === 'overview') setActivePage('salesman');
  }, [role, activePage]);

  const [title, subtitle] = PAGE_TITLES[activePage] || [activePage, ''];
  const handleLogout = async () => { try { await logout(); } catch(e) { console.error(e); } };

  const visibleNav = NAV.map(section => ({
    ...section,
    items: section.items.filter(item => !item.roles || item.roles.includes(role))
  })).filter(section => section.items.length > 0);

  const navigate = (page) => setActivePage(page);

  const renderPage = () => {
    switch(activePage) {
      case 'booking':
        return <BookingPage />;

      case 'overview':
        if (role === 'Salesman') return <AccessDenied msg="Salesmen cannot access company overview." />;
        return <OverviewPage navigate={navigate} searchTerm={globalSearch}/>;
      case 'salesman':
        if (role === 'Manager' && !hasPermission('ledger.view') && !hasPermission('sales.view')) return <AccessDenied msg="You need the 'ledger.view' or 'sales.view' permission to view salesman ledgers." />;
        return <SalesmanPage searchTerm={globalSearch}/>;
      case 'stock':
        if (role === 'Manager' && !hasPermission('inventory.view') && !hasPermission('returns.view')) return <AccessDenied msg="You need the 'inventory.view' or 'returns.view' permission to access Stock & Returns." />;
        return <StockPage searchTerm={globalSearch}/>;
      case 'expenses':
        if (role === 'Manager' && !hasPermission('expenses.view')) return <AccessDenied msg="You need the 'expenses.view' permission to access Expenses." />;
        return <ExpensesPage searchTerm={globalSearch}/>;
      case 'distributors':
        return <DistributorsPage searchTerm={globalSearch}/>;
      case 'sales':
        return <SalesPage searchTerm={globalSearch}/>;
      case 'customers':
        if (role === 'Salesman') return <AccessDenied msg="Salesmen cannot access the customer directory."/>;
        if (role === 'Manager' && !hasPermission('sales.view')) return <AccessDenied msg="You need the sales.view permission to access customers."/>;
        return <CustomersPage searchTerm={globalSearch}/>;
      case 'product':
        if (role === 'Salesman') return <AccessDenied msg="Salesmen cannot access product management."/>;
        if (role === 'Manager' && !hasPermission('inventory.view')) return <AccessDenied msg="You need the inventory.view permission to access products."/>;
        return <ProductPage searchTerm={globalSearch}/>;
      case 'settlement':
        if (role === 'Salesman') return <AccessDenied msg="Salesmen cannot access settlement."/>;
        if (role === 'Manager' && !hasPermission('settlement.view')) return <AccessDenied msg="You need the settlement.view permission to access settlement."/>;
        return <SettlementPage searchTerm={globalSearch}/>;
      case 'reports':
        if (role === 'Salesman') return <AccessDenied msg="Salesmen cannot access reports."/>;
        if (role === 'Manager' && !hasPermission('reports.view')) return <AccessDenied msg="You need the reports.view permission to access reports."/>;
        return <ReportsPage/>;
      case 'audit':
        if (role === 'Salesman') return <AccessDenied msg="Salesmen cannot access the audit trail."/>;
        if (role === 'Manager' && !hasPermission('audit.view')) return <AccessDenied msg="You need the audit.view permission to access the audit trail."/>;
        return <AuditPage searchTerm={globalSearch}/>;
      case 'settings':
        if (role !== 'Super_Admin') return <AccessDenied msg="Only Super Admin can access Settings."/>;
        return <SettingsPage searchTerm={globalSearch}/>;
      default:
        return <AccessDenied msg="Page not found."/>;
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <img src="/elitewash-logo.jpg" className="brand-mark" style={{objectFit:"cover", background:"none"}} alt="EW" />
          <div><div className="brand-name">Elite Wash</div><div className="brand-sub">Surf Stock &amp; Ledger Control</div></div>
        </div>
        <div className="sidebar-nav-scroll">
        {visibleNav.map(section => (
          <React.Fragment key={section.group}>
            <div className="nav-group-label">{section.group}</div>
            <ul className="nav">
              {section.items.map(item => (
                <li key={item.key} className={`nav-item${activePage===item.key? ' active':''}`} onClick={() => navigate(item.key)}>
                  {item.icon}{item.label}
                </li>
              ))}
            </ul>
          </React.Fragment>
        ))}
        </div>
        <div className="sidebar-footer">
          <div style={{fontSize:11,color:'#5C6B80',marginBottom:6}}>Signed in as: <span style={{color:'#8CA0AB'}}>{displayName}</span></div>
          <button className="logout-btn" onClick={handleLogout}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            Sign out
          </button>
        </div>
      </aside>
      <div className="main">
        <div className="content">
          <div className="page-enter" key={activePage}>
            {renderPage()}
          </div>
        </div>
        <footer className="note">Elite Wash ERP — All balances derived from transactions. No manual overwrite.</footer>
      </div>
    </div>
  );
}


function SalesmanPage({ searchTerm = '' }) {
  const { role, user } = useAuth();
  const [activeTab, setActiveTab] = useState('stockLedger');
  const [selectedId, setSelectedId] = useState(null);
  const [localSearch, setLocalSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const { data: salesmen, loading: sl } = useAsync(fetchSalesmen);
  
  const selected = (salesmen||[]).find(s => s.id === selectedId) || (salesmen||[])[0];
  const sid = selected?.id;

  useEffect(() => {
    if (!salesmen?.length) return;
    if (role === 'Salesman') {
      const own = salesmen.find(s => s.profile_id === user?.id);
      if (own) setSelectedId(own.id);
    } else if (!selectedId) {
      setSelectedId(salesmen[0].id);
    }
  }, [salesmen, role, user]);

  const { data: stats, loading: tl } = useAsync(() => sid ? fetchSalesmanStats(sid) : Promise.resolve(null), [sid]);
  const { data: stock, loading: stL } = useAsync(() => sid ? fetchSalesmanStockLedger(sid) : Promise.resolve([]), [sid, activeTab]);
  const { data: fin,   loading: fL } = useAsync(() => sid ? fetchSalesmanFinLedger(sid) : Promise.resolve([]), [sid, activeTab]);
  const { data: exp,   loading: eL } = useAsync(() => sid ? fetchSalesmanExpLedger(sid) : Promise.resolve([]), [sid, activeTab]);

  useEffect(() => { setPage(1); }, [activeTab, statusFilter, localSearch, searchTerm]);

  if (sl) return <Spinner/>;
  const st = stats || {};

  const query = (localSearch || searchTerm).trim().toLowerCase();

  const filteredStock = (stock || []).filter(r => {
    if (statusFilter !== 'All' && r.status !== statusFilter) return false;
    if (!query) return true;
    return (
      (r.reference_number || '').toLowerCase().includes(query) ||
      (r.transaction_type || '').toLowerCase().includes(query) ||
      (r.status || '').toLowerCase().includes(query) ||
      fmtDate(r.transaction_date).toLowerCase().includes(query)
    );
  });

  const filteredFin = (fin || []).filter(r => {
    if (statusFilter !== 'All' && r.status !== statusFilter) return false;
    if (!query) return true;
    return (
      (r.ref || '').toLowerCase().includes(query) ||
      (r.type || '').toLowerCase().includes(query) ||
      (r.status || '').toLowerCase().includes(query) ||
      fmtDate(r.date).toLowerCase().includes(query)
    );
  });

  const filteredExp = (exp || []).filter(r => {
    if (statusFilter !== 'All' && r.status !== statusFilter) return false;
    if (!query) return true;
    return (
      (r.category || '').toLowerCase().includes(query) ||
      (r.description || '').toLowerCase().includes(query) ||
      (r.status || '').toLowerCase().includes(query) ||
      fmtDate(r.expense_date).toLowerCase().includes(query)
    );
  });

  const paginatedStock = filteredStock.slice((page - 1) * pageSize, page * pageSize);
  const paginatedFin = filteredFin.slice((page - 1) * pageSize, page * pageSize);
  const paginatedExp = filteredExp.slice((page - 1) * pageSize, page * pageSize);

  const isFiltered = localSearch || statusFilter !== 'All';
  const resetFilters = () => { setLocalSearch(''); setStatusFilter('All'); setPage(1); };

  return (
    <>
      <div className="panel" style={{marginBottom:20}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:14}}>
          <div style={{display:'flex',alignItems:'center',gap:14}}>
            <div className="avatar" style={{width:52,height:52,fontSize:17}}>{selected?.profiles?.full_name?.substring(0,2)?.toUpperCase()||'--'}</div>
            <div>
              <div style={{fontSize:16,fontWeight:600}}>{selected?.profiles?.full_name||'-'} - #{selected?.code||'-'}</div>
              <div style={{fontSize:12,color:'var(--text-dim)'}}>Route: {selected?.route||'-'}</div>
            </div>
          </div>
          <div className="chip-list">
            {role === 'Salesman' ? (
              <div className="chip active">{selected?.profiles?.full_name||selected?.code}</div>
            ) : (
              (salesmen||[]).map(s => (
                <div key={s.id} className={`chip${s.id===selectedId?' active':''}`} onClick={() => setSelectedId(s.id)}>
                  {s.profiles?.full_name||s.code}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {tl ? <Spinner/> : (
        <div className="grid g4" style={{marginBottom:20}}>
          <div className="tile teal"><div className="bar"/><div className="label">Current stock</div><div className="num">{fmtNum(st.stock)} pkts</div></div>
          <div className="tile green"><div className="bar"/><div className="label">Today's sales</div><div className="num">Rs. {fmtNum(st.todaySalesAmt)}</div></div>
          <div className="tile amber"><div className="bar"/><div className="label">Outstanding</div><div className="num">Rs. {fmtNum(st.outstanding)}</div></div>
          <div className="tile red"><div className="bar"/><div className="label">Pending reimbursement</div><div className="num">Rs. {fmtNum(st.pendingReimb)}</div></div>
        </div>
      )}

      <div className="panel">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,borderBottom:'1px solid var(--line)',paddingBottom:12,marginBottom:16}}>
          <div className="tabs" style={{margin:0,border:0}}>
            {[['stockLedger','Stock Ledger'],['finLedger','Financial Ledger'],['expLedger','Expense Ledger']].map(([k,l]) => (
              <div key={k} className={`tab${activeTab===k?' active':''}`} onClick={() => setActiveTab(k)}>{l}</div>
            ))}
          </div>

          <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}>
            <input 
              type="text" 
              placeholder="Filter by ref, type, date..." 
              value={localSearch} 
              onChange={e => setLocalSearch(e.target.value)} 
              style={{padding:'5px 10px',fontSize:12,border:'1px solid var(--line)',borderRadius:6,background:'var(--panel)',color:'var(--text)',outline:'none',width:190}}
            />
            <div className="chip-list" style={{gap:4}}>
              {['All', 'Approved', 'Pending'].map(st => (
                <div key={st} className={`chip${statusFilter===st?' active':''}`} onClick={() => setStatusFilter(st)} style={{padding:'4px 10px',fontSize:11}}>
                  {st}
                </div>
              ))}
            </div>
            {isFiltered && (
              <span className="link" onClick={resetFilters} style={{color:'var(--red)',fontSize:12}}>Reset</span>
            )}
          </div>
        </div>

        {activeTab === 'stockLedger' && (
          stL ? <Spinner/> : (
            <div>
              <table>
                <thead><tr><th>Date</th><th>Transaction</th><th>Reference</th><th>In</th><th>Out</th><th>Status</th></tr></thead>
                <tbody>
                  {paginatedStock.length===0 ? <Empty msg={isFiltered || query ? "No matching stock transactions found." : "No stock transactions yet."}/> :
                    paginatedStock.map(r => (
                      <tr key={r.id}>
                        <td>{fmtDate(r.transaction_date)}</td>
                        <td>{r.transaction_type?.replace(/_/g,' ')}</td>
                        <td style={{fontSize:11,color:'var(--text-dim)'}}>{r.reference_number}</td>
                        <td className="num-cell">{r.transaction_type==='Salesman_Issue'?r.quantity:'-'}</td>
                        <td className="num-cell">{['Sale','Salesman_Good_Return','Salesman_Damaged_Return'].includes(r.transaction_type)?r.quantity:'-'}</td>
                        <td>{statusBadge(r.status)}</td>
                      </tr>
                    ))
                  }
                </tbody>
              </table>
              <Pagination page={page} pageSize={pageSize} total={filteredStock.length} onPageChange={setPage} />
            </div>
          )
        )}

        {activeTab === 'finLedger' && (
          fL ? <Spinner/> : (
            <div>
              <table>
                <thead><tr><th>Date</th><th>Type</th><th>Reference</th><th>Debit</th><th>Credit</th><th>Balance</th><th>Status</th></tr></thead>
                <tbody>
                  {paginatedFin.length===0 ? <Empty msg={isFiltered || query ? "No matching financial records found." : "No financial transactions yet."}/> :
                    paginatedFin.map((r,i) => (
                      <tr key={i}>
                        <td>{fmtDate(r.date)}</td>
                        <td>{r.type}</td>
                        <td style={{fontSize:11,color:'var(--text-dim)'}}>{r.ref}</td>
                        <td className="num-cell">{r.debit?`Rs. ${fmtNum(r.debit)}`:'-'}</td>
                        <td className="num-cell">{r.credit?`Rs. ${fmtNum(r.credit)}`:'-'}</td>
                        <td className="num-cell" style={{color:r.balance>0?'var(--red)':'var(--green)'}}>Rs. {fmtNum(Math.abs(r.balance))}</td>
                        <td>{statusBadge(r.status)}</td>
                      </tr>
                    ))
                  }
                </tbody>
              </table>
              <Pagination page={page} pageSize={pageSize} total={filteredFin.length} onPageChange={setPage} />
            </div>
          )
        )}

        {activeTab === 'expLedger' && (
          eL ? <Spinner/> : (
            <div>
              <table>
                <thead><tr><th>Date</th><th>Category</th><th>Amount</th><th>Description</th><th>Status</th></tr></thead>
                <tbody>
                  {paginatedExp.length===0 ? <Empty msg={isFiltered || query ? "No matching expenses found." : "No expenses yet."}/> :
                    paginatedExp.map(r => (
                      <tr key={r.id}>
                        <td>{fmtDate(r.expense_date)}</td>
                        <td>{r.category}</td>
                        <td className="num-cell">Rs. {fmtNum(r.amount)}</td>
                        <td style={{fontSize:11,color:'var(--text-dim)'}}>{r.description||'-'}</td>
                        <td>{statusBadge(r.status)}</td>
                      </tr>
                    ))
                  }
                </tbody>
              </table>
              <Pagination page={page} pageSize={pageSize} total={filteredExp.length} onPageChange={setPage} />
            </div>
          )
        )}
      </div>
    </>
  );
}

function Pagination({ page, pageSize, total, onPageChange }) {
  if (total <= pageSize) return null;
  const totalPages = Math.ceil(total / pageSize);
  const start = (page - 1) * pageSize;
  const end = Math.min(start + pageSize, total);

  return (
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginTop:14,paddingTop:12,borderTop:'1px solid var(--line)',fontSize:12,color:'var(--text-dim)'}}>
      <div>Showing {start + 1}â€"{end} of {total} records</div>
      <div style={{display:'flex',gap:6,alignItems:'center'}}>
        <button className="btn" disabled={page <= 1} onClick={() => onPageChange(page - 1)} style={{padding:'4px 10px',fontSize:12}}>Previous</button>
        <span style={{fontSize:12,color:'var(--text)'}}>Page {page} of {totalPages}</span>
        <button className="btn" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)} style={{padding:'4px 10px',fontSize:12}}>Next</button>
      </div>
    </div>
  );
}


function CustomersPage({ searchTerm = '' }) {
  const { data: customers, loading: cl, reload } = useAsync(fetchCustomers);
  const { data: salesmen } = useAsync(fetchSalesmen);
  const { data: cReturns, loading: rl } = useAsync(fetchCustomerReturns);
  const [showAdd, setShowAdd] = useState(false);
  const [showSale, setShowSale] = useState(false);
  const [form, setForm] = useState({ code:'', name:'', phone:'', address:'', default_salesman_id:'' });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  // Search & Filter state
  const [localSearch, setLocalSearch] = useState('');
  const [salesmanFilter, setSalesmanFilter] = useState('All');
  const [page, setPage] = useState(1);
  const [returnSearch, setReturnSearch] = useState('');
  const [returnPage, setReturnPage] = useState(1);
  const pageSize = 15;

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.code || !form.name) { setMsg('err:Code and name required.'); return; }
    setSaving(true); setMsg('');
    try {
      await addCustomer(form);
      setMsg('ok:Customer added.');
      setForm({code:'',name:'',phone:'',address:'',default_salesman_id:''});
      setShowAdd(false); reload();
    } catch(e) { setMsg('err:'+e.message); } finally { setSaving(false); }
  };

  const query = (localSearch || searchTerm).trim().toLowerCase();

  const filteredCustomers = (customers || []).filter(c => {
    if (salesmanFilter !== 'All' && c.default_salesman_id !== salesmanFilter) return false;
    if (!query) return true;
    return (
      (c.name || '').toLowerCase().includes(query) ||
      (c.code || '').toLowerCase().includes(query) ||
      (c.phone || '').toLowerCase().includes(query) ||
      (c.address || '').toLowerCase().includes(query) ||
      (c.salesmen?.profiles?.full_name || '').toLowerCase().includes(query)
    );
  });

  const paginatedCustomers = filteredCustomers.slice((page - 1) * pageSize, page * pageSize);
  const isCustFiltered = localSearch || salesmanFilter !== 'All';
  const resetCustFilters = () => { setLocalSearch(''); setSalesmanFilter('All'); setPage(1); };

  const retQuery = (returnSearch || searchTerm).trim().toLowerCase();
  const filteredReturns = (cReturns || []).filter(r => {
    if (!retQuery) return true;
    return (
      (r.reference_number || '').toLowerCase().includes(retQuery) ||
      (r.customers?.name || '').toLowerCase().includes(retQuery) ||
      (r.salesmen?.profiles?.full_name || '').toLowerCase().includes(retQuery) ||
      (r.transaction_type || '').toLowerCase().includes(retQuery) ||
      (r.status || '').toLowerCase().includes(retQuery) ||
      fmtDate(r.transaction_date).toLowerCase().includes(retQuery)
    );
  });
  const paginatedReturns = filteredReturns.slice((returnPage - 1) * pageSize, returnPage * pageSize);

  return (
    <>
      <div className="panel">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,marginBottom:14}}>
          <div className="section-head" style={{margin:0}}>
            <h2>Customer directory</h2>
          </div>
          <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}>
            <input 
              type="text" 
              placeholder="Search name, code, phone..." 
              value={localSearch} 
              onChange={e => { setLocalSearch(e.target.value); setPage(1); }}
              style={{padding:'5px 10px',fontSize:12,border:'1px solid var(--line)',borderRadius:6,background:'var(--panel)',color:'var(--text)',outline:'none',width:190}}
            />
            
            {isCustFiltered && (
              <span className="link" onClick={resetCustFilters} style={{color:'var(--red)',fontSize:12}}>Reset</span>
            )}
            
              <button className={showAdd ? 'btn ghost' : 'btn primary'} onClick={()=>setShowAdd(s=>!s)}>{showAdd?'Cancel':'Add customer'}</button>
          </div>
        </div>

        

          {showAdd && (
          <form onSubmit={handleAdd} style={{marginBottom:20,padding:16,background:'#FAFBF8',borderRadius:6,border:'1px solid var(--line)'}}>
            <Msg msg={msg} />
            <div className="form-grid">
              <div className="field"><label>Code *</label><input placeholder="e.g. CUST-001" value={form.code} onChange={e=>setForm(f=>({...f,code:e.target.value}))}/></div>
              <div className="field"><label>Name *</label><input placeholder="Customer name" value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))}/></div>
              <div className="field"><label>Phone</label><input placeholder="03xx-xxxxxxx" value={form.phone} onChange={e=>setForm(f=>({...f,phone:e.target.value}))}/></div>
              <div className="field">
                <label>Default Salesman</label>
                <select value={form.default_salesman_id} onChange={e=>setForm(f=>({...f,default_salesman_id:e.target.value}))}>
                  <option value="">-- None --</option>
                  {(salesmen||[]).map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
                </select>
              </div>
              <div className="field" style={{gridColumn:'1/-1'}}><label>Address</label><input placeholder="Area / locality" value={form.address} onChange={e=>setForm(f=>({...f,address:e.target.value}))}/></div>
            </div>
            <button type="submit" className="btn primary" style={{marginTop:12}} disabled={saving}>{saving?'Saving...':'Add Customer'}</button>
          </form>
        )}

        {cl ? <Spinner/> : (
          <div>
            <table>
              <thead><tr><th>Customer</th><th>Area</th><th>Outstanding</th></tr></thead>
              <tbody>
                {paginatedCustomers.length===0 ? <Empty msg={isCustFiltered || query ? "No customers found matching search criteria." : "No customers yet."}/> :
                  paginatedCustomers.map(c=>(
                    <tr key={c.id}>
                      <td><div style={{fontWeight:600}}>{c.name}</div><div style={{fontSize:11,color:'var(--text-dim)'}}>{c.code}</div></td>
                      <td>{c.address||'-'}</td>
                      
                      <td className="num-cell" style={{color:c.outstanding>0?'var(--red)':'inherit'}}>Rs. {fmtNum(c.outstanding)}</td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
            <Pagination page={page} pageSize={pageSize} total={filteredCustomers.length} onPageChange={setPage} />
          </div>
        )}
      </div>

      <div className="panel" style={{marginTop:20}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,marginBottom:14}}>
          <div className="section-head" style={{margin:0}}><h2>Customer returns</h2></div>
          <div style={{display:'flex',gap:8,alignItems:'center'}}>
            <input 
              type="text" 
              placeholder="Search returns..." 
              value={returnSearch} 
              onChange={e => { setReturnSearch(e.target.value); setReturnPage(1); }}
              style={{padding:'5px 10px',fontSize:12,border:'1px solid var(--line)',borderRadius:6,background:'var(--panel)',color:'var(--text)',outline:'none',width:190}}
            />
            {returnSearch && (
              <span className="link" onClick={() => setReturnSearch('')} style={{color:'var(--red)',fontSize:12}}>Reset</span>
            )}
          </div>
        </div>

        {rl ? <Spinner/> : (
          <div>
            <table>
              <thead><tr><th>Reference</th><th>Date</th><th>Customer</th><th>Type</th><th>Qty</th><th>Status</th></tr></thead>
              <tbody>
                {paginatedReturns.length===0 ? <Empty msg={retQuery ? "No matching customer returns found." : "No customer returns yet."}/> :
                  paginatedReturns.map(r=>(
                    <tr key={r.id}>
                      <td style={{fontSize:11}}>{r.reference_number}</td>
                      <td>{fmtDate(r.transaction_date)}</td>
                      <td>{r.customers?.name||'-'}</td>
                      
                      <td>{r.transaction_type?.replace(/_/g,' ')}</td>
                      <td className="num-cell">{r.quantity}</td>
                      <td>{statusBadge(r.status)}</td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
            <Pagination page={returnPage} pageSize={pageSize} total={filteredReturns.length} onPageChange={setReturnPage} />
          </div>
        )}
      </div>
    </>
  );
}

function ProductPage({ searchTerm = '' }) {
  const { role } = useAuth();
  const { data: products, loading: pl, reload } = useAsync(fetchProducts);
  const { data: movement, loading: ml } = useAsync(fetchProductMovement);
  const mv = movement || {};

  const [localSearch, setLocalSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const query = (localSearch || searchTerm).trim().toLowerCase();

  // Add/Edit Product form state
  const [showAdd, setShowAdd] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [form, setForm] = useState({ name: '', code: '', packagingName: '', unitCost: '', salesPrice: '', pkgId: null, productId: null, priceId: null });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const handleAddProduct = async (e) => {
    e.preventDefault();
    if (!form.name || !form.code || !form.packagingName || !form.unitCost || !form.salesPrice) {
      setMsg('err:All fields are required.');
      return;
    }
    setSaving(true); setMsg('');
    try {
      if (editMode) {
        await updateProduct(form);
        setMsg('ok:Product updated successfully.');
      } else {
        await addProduct(form);
        setMsg('ok:Product added successfully.');
      }
      setForm({ name: '', code: '', packagingName: '', unitCost: '', salesPrice: '', pkgId: null, productId: null, priceId: null });
      setShowAdd(false);
      setEditMode(false);
      reload();
    } catch (e) {
      setMsg('err:' + e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (r) => {
    setForm({
      name: r.productName,
      code: r.productCode || '',
      packagingName: r.packagingName,
      unitCost: r.unitCost || '',
      salesPrice: r.salesPrice || '',
      pkgId: r.id,
      productId: r.productId,
      priceId: r.priceId
    });
    setEditMode(true);
    setShowAdd(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (r) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    setMsg('');
    try {
      await deleteProduct(r.id, r.productId);
      setMsg('ok:Product deleted successfully.');
      reload();
    } catch (e) {
      setMsg('err:' + e.message);
    }
  };

  const canManage = role === 'Super_Admin' || role === 'Manager';

  const allPriceRows = (products || []).flatMap(p =>
    (p.product_packaging || []).map(pkg => {
      const price = pkg.product_prices?.[0];
      return {
        id: pkg.id,
        productId: p.id,
        priceId: price?.id,
        productName: p.name,
        productCode: p.code,
        packagingName: pkg.name,
        unitCost: price?.unit_cost,
        salesPrice: price?.sales_price
      };
    })
  );

  const filteredPrices = allPriceRows.filter(r => {
    if (!query) return true;
    return (
      r.productName.toLowerCase().includes(query) ||
      (r.productCode || '').toLowerCase().includes(query) ||
      r.packagingName.toLowerCase().includes(query)
    );
  });

  const paginatedPrices = filteredPrices.slice((page - 1) * pageSize, page * pageSize);
  const isFiltered = !!localSearch;

  return (
    <>
      <div className="grid g4" style={{marginBottom:20}}>
        <div className="tile teal"><div className="bar"/><div className="label">Production</div><div className="num">{fmtNum(mv.production)}</div></div>
        <div className="tile green"><div className="bar"/><div className="label">Salesman returns</div><div className="num">{fmtNum(mv.salesman_returns)}</div></div>
        <div className="tile amber"><div className="bar"/><div className="label">Damaged / adjustments</div><div className="num">{fmtNum(mv.damaged)}</div></div>
        <div className="tile red"><div className="bar"/><div className="label">Closing stock (warehouse)</div><div className="num">{fmtNum(mv.closing)}</div></div>
      </div>

      <div className="panel">
        <div className="section-head"><h2>Stock movement report</h2></div>
        {ml ? <Spinner/> : (
          <table>
            <tbody>
              <tr><td>Production</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.production)}</td></tr>
              <tr><td>Salesman issues (dispatched)</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.salesman_issues)}</td></tr>
              <tr><td>Salesman returns</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.salesman_returns)}</td></tr>
              <tr><td>Customer returns</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.customer_returns)}</td></tr>
              <tr><td>Damaged</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.damaged)}</td></tr>
              <tr><td>Adjustments</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.adjustments)}</td></tr>
              <tr><td><strong>Closing stock</strong></td><td className="num-cell" style={{textAlign:'right'}}><strong>{fmtNum(mv.closing)}</strong></td></tr>
            </tbody>
          </table>
        )}
      </div>

      <div className="panel" style={{marginTop:20}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,marginBottom:14}}>
          <div className="section-head" style={{margin:0}}><h2>Products &amp; pricing</h2></div>
          <div style={{display:'flex',gap:8,alignItems:'center'}}>
            <input
              type="text"
              placeholder="Search product or packaging..."
              value={localSearch}
              onChange={e => { setLocalSearch(e.target.value); setPage(1); }}
              style={{padding:'5px 10px',fontSize:12,border:'1px solid var(--line)',borderRadius:6,background:'var(--panel)',color:'var(--text)',outline:'none',width:200}}
            />
            {isFiltered && (
              <span className="link" onClick={() => { setLocalSearch(''); setPage(1); }} style={{color:'var(--red)',fontSize:12}}>Reset</span>
            )}
            {canManage && (
              <button className={showAdd ? 'btn ghost' : 'btn primary'} onClick={() => { 
                if(showAdd) { setShowAdd(false); setEditMode(false); setForm({ name: '', code: '', packagingName: '', unitCost: '', salesPrice: '', pkgId: null, productId: null, priceId: null }); }
                else { setShowAdd(true); } 
              }}>
                {showAdd ? 'Cancel' : '+ Add Product'}
              </button>
            )}
          </div>
        </div>

        {canManage && showAdd && (
          <form onSubmit={handleAddProduct} style={{marginBottom:20,padding:16,background:'#FAFBF8',borderRadius:6,border:'1px solid var(--line)'}}>
            <div style={{fontWeight:600,fontSize:13,marginBottom:12}}>{editMode ? 'Edit Product' : 'Add New Product'}</div>
            <Msg msg={msg} />
            <div className="form-grid">
              <div className="field">
                <label>Product Name *</label>
                <input value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} placeholder="e.g. Elite Wash" />
              </div>
              <div className="field">
                <label>Product Code *</label>
                <input value={form.code} onChange={e=>setForm(f=>({...f,code:e.target.value}))} placeholder="e.g. ELW-001" />
              </div>
              <div className="field">
                <label>Packaging / Variant *</label>
                <input value={form.packagingName} onChange={e=>setForm(f=>({...f,packagingName:e.target.value}))} placeholder="e.g. 1kg, 500g, Sachet" />
              </div>
              <div className="field">
                <label>Cost Price (Rs.) *</label>
                <input type="number" min="0" step="0.01" value={form.unitCost} onChange={e=>setForm(f=>({...f,unitCost:e.target.value}))} placeholder="e.g. 90" />
              </div>
              <div className="field">
                <label>Sales Price (Rs.) *</label>
                <input type="number" min="0" step="0.01" value={form.salesPrice} onChange={e=>setForm(f=>({...f,salesPrice:e.target.value}))} placeholder="e.g. 120" />
              </div>
            </div>
            <button type="submit" className="btn primary" style={{marginTop:12}} disabled={saving}>{saving ? 'Saving...' : (editMode ? 'Update Product' : 'Save Product')}</button>
          </form>
        )}
        {!showAdd && <Msg msg={msg} />}

        {pl ? <Spinner/> : (
          <div>
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Packaging</th>
                  <th>Cost price</th>
                  <th>Sales price</th>
                  {canManage && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {paginatedPrices.length===0 ? <Empty msg={isFiltered || query ? "No products found matching search criteria." : "No products found. Add your first product using the button above."}/> :
                  paginatedPrices.map(r => (
                    <tr key={r.id}>
                      <td>{r.productName}</td>
                      <td>{r.packagingName}</td>
                      <td className="num-cell">Rs. {fmtNum(r.unitCost)}</td>
                      <td className="num-cell">Rs. {fmtNum(r.salesPrice)}</td>
                      {canManage && (
                        <td>
                          <span className="link" onClick={() => handleEdit(r)}>Edit</span>
                          <span className="link" onClick={() => handleDelete(r)} style={{color:'var(--red)', marginLeft: 8}}>Delete</span>
                        </td>
                      )}
                    </tr>
                  ))
                }
              </tbody>
            </table>
            <Pagination page={page} pageSize={pageSize} total={filteredPrices.length} onPageChange={setPage} />
          </div>
        )}
      </div>
    </>
  );
}

function SettlementPage({ searchTerm = '' }) {
  const { data: salesmen } = useAsync(fetchSalesmen);
  const [selectedId, setSelectedId] = useState('');
  const { data: settlement, loading: sl } = useAsync(() => selectedId ? fetchSalesmanSettlement(selectedId) : Promise.resolve(null), [selectedId]);
  
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const query = (searchTerm || '').trim().toLowerCase();
  const filteredSalesmen = (salesmen || []).filter(s => !query || (s.profiles?.full_name || '').toLowerCase().includes(query) || (s.code || '').toLowerCase().includes(query));
  
  const selected = (salesmen||[]).find(s=>s.id===selectedId);
  const sv = settlement||{};

  const handleApprove = async () => {
    if (!selectedId) return;
    setSaving(true);
    setMsg('');
    try {
      // Dynamically import or assume approveSettlement is available
      // It might not be imported in main.jsx, so let's import it at the top or use window logic
      const { approveSettlement } = await import('./lib/db.js');
      await approveSettlement(selectedId);
      setMsg('ok:Settlement approved successfully.');
    } catch(err) {
      setMsg('error:' + err.message);
    }
    setSaving(false);
  };

  return (
    <div className="panel">
      <div className="section-head"><h2>Distributor Settlement</h2></div>
      <div className="field" style={{marginBottom:20,maxWidth:300}}>
        <label>Select Distributor</label>
        <select value={selectedId} onChange={e => { setSelectedId(e.target.value); setMsg(''); }}>
          <option value="">-- Select --</option>
          {filteredSalesmen.map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
        </select>
      </div>

      {msg && (
        <div style={{ padding: '8px 12px', marginBottom: 14, borderRadius: 6, fontSize: 12,
          background: msg.startsWith('error') ? 'var(--red-soft)' : 'var(--green-soft)',
          color: msg.startsWith('error') ? 'var(--red)' : 'var(--green)' }}>
          {msg.replace(/^(ok|error):/, '')}
        </div>
      )}

      {selectedId && (sl ? <Spinner/> : (
        <>
          <div className="grid g3" style={{marginBottom:18}}>
            <div className="panel-flat"><div style={{fontSize:12,color:'var(--text-dim)'}}>Net sales</div><div className="num" style={{fontSize:20}}>Rs. {fmtNum(sv.netSales)}</div></div>
            <div className="panel-flat"><div style={{fontSize:12,color:'var(--text-dim)'}}>Recovery</div><div className="num" style={{fontSize:20}}>Rs. {fmtNum(sv.recovery)}</div></div>
            <div className="panel-flat"><div style={{fontSize:12,color:'var(--text-dim)'}}>Outstanding</div><div className="num" style={{fontSize:20}}>Rs. {fmtNum(sv.outstanding)}</div></div>
          </div>
          <table>
            <tbody>
              <tr><td>Sales (net)</td><td className="num-cell" style={{textAlign:'right'}}>+ Rs. {fmtNum(sv.netSales)}</td></tr>
              <tr><td>Recovery received</td><td className="num-cell" style={{textAlign:'right'}}>− Rs. {fmtNum(sv.recovery)}</td></tr>
              <tr><td>Reimbursement payable (approved expenses)</td><td className="num-cell" style={{textAlign:'right'}}>+ Rs. {fmtNum(sv.reimbursable)}</td></tr>
              <tr><td><strong>Net settlement position</strong></td><td className="num-cell" style={{textAlign:'right'}}>
                <strong style={{color:sv.net>0?'var(--red)':'var(--green)'}}>
                  {sv.net>0?`Rs. ${fmtNum(sv.net)} payable by ${selected?.profiles?.full_name||'salesman'}`:`Rs. ${fmtNum(Math.abs(sv.net||0))} payable to ${selected?.profiles?.full_name||'salesman'}`}
                </strong>
              </td></tr>
            </tbody>
          </table>
          <div className="btn-row" style={{marginTop:16}}>
            <button className="btn primary" onClick={handleApprove} disabled={saving}>
              {saving ? 'Approving...' : 'Approve settlement'}
            </button>
          </div>
        </>
      ))}

      {!selectedId && <div style={{padding:24,textAlign:'center',color:'var(--text-dim)',fontSize:13}}>Select a distributor above to view their settlement.</div>}
    </div>
  );
}
function AuditPage({ searchTerm = '' }) {
  const { data: logs, loading: ll } = useAsync(fetchAuditLogs);

  const [localSearch, setLocalSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('All');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const query = (localSearch || searchTerm).trim().toLowerCase();

  const filteredLogs = (logs || []).filter(l => {
    if (actionFilter !== 'All' && l.action !== actionFilter) return false;
    if (!query) return true;
    return (
      (l.table_name || '').toLowerCase().includes(query) ||
      (l.profiles?.full_name || '').toLowerCase().includes(query) ||
      (l.action || '').toLowerCase().includes(query) ||
      (l.record_id || '').toLowerCase().includes(query) ||
      fmtTime(l.created_at).toLowerCase().includes(query)
    );
  });

  const paginatedLogs = filteredLogs.slice((page - 1) * pageSize, page * pageSize);
  const isFiltered = localSearch || actionFilter !== 'All';
  const resetFilters = () => { setLocalSearch(''); setActionFilter('All'); setPage(1); };

  return (
    <div className="panel">
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,marginBottom:14}}>
        <div className="section-head" style={{margin:0}}><h2>Audit trail</h2></div>
        <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}>
          <input 
            type="text" 
            placeholder="Search action, table, user..." 
            value={localSearch} 
            onChange={e => { setLocalSearch(e.target.value); setPage(1); }}
            style={{padding:'5px 10px',fontSize:12,border:'1px solid var(--line)',borderRadius:6,background:'var(--panel)',color:'var(--text)',outline:'none',width:190}}
          />
          <div className="chip-list" style={{gap:4}}>
            {['All', 'INSERT', 'UPDATE', 'DELETE'].map(act => (
              <div key={act} className={`chip${actionFilter===act?' active':''}`} onClick={() => { setActionFilter(act); setPage(1); }} style={{padding:'4px 10px',fontSize:11}}>
                {act}
              </div>
            ))}
          </div>
          {isFiltered && (
            <span className="link" onClick={resetFilters} style={{color:'var(--red)',fontSize:12}}>Reset</span>
          )}
        </div>
      </div>

      {ll ? <Spinner/> : (
        <div>
          <table>
            <thead><tr><th>Timestamp</th><th>User</th><th>Table</th><th>Action</th></tr></thead>
            <tbody>
              {paginatedLogs.length===0 ? <Empty msg={isFiltered || query ? "No matching audit records found." : "No audit logs yet."}/> :
                paginatedLogs.map(l=>(
                  <tr key={l.id}>
                    <td style={{fontSize:11}}>{fmtTime(l.created_at)}</td>
                    <td>{l.profiles?.full_name||'System'}</td>
                    <td style={{fontSize:11}}>{l.table_name}</td>
                    <td><span className={`badge ${l.action==='INSERT'?'green':l.action==='UPDATE'?'amber':'red'}`}>{l.action}</span></td>
                  </tr>
                ))
              }
            </tbody>
          </table>
          <Pagination page={page} pageSize={pageSize} total={filteredLogs.length} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById('root')).render(<Root/>);
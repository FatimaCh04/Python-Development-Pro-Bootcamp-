import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';
import SettingsPage from './components/SettingsPage';
import { exportToCsv, generatePdf, printReport, shareOnWhatsApp } from './lib/exportUtils';
import {
  fetchOverviewStats, fetchRecentAuditLogs, fetchSalesmenSnapshot, fetchChartData,
  fetchSalesmen, fetchSalesmanStats, fetchSalesmanStockLedger, fetchSalesmanFinLedger, fetchSalesmanExpLedger,
  fetchInventoryTransactions, submitStockReturn, approveTransaction,
  fetchExpenses, submitExpense, updateExpenseStatus, fetchExpenseSummary,
  fetchCustomers, addCustomer, fetchCustomerReturns,
  fetchProducts, fetchProductMovement, fetchPackagings,
  fetchSalesmanSettlement, fetchAuditLogs,
  closeTodayLedger, fetchDailyClosingReport, fetchProfitabilityReport, fetchVarianceReport, approveSettlement
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
      <div className="brand-mark">EW</div>
      <p>Loading Elite Washwo...</p>
    </div>
  );
  if (!session) return <Login />;
  return <App />;
}

const NAV = [
  { group: 'Operations', items: [
    { key: 'overview',   label: 'Overview',        roles: ['Super_Admin', 'Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg> },
    { key: 'salesman',   label: 'Salesman Ledger', roles: null, icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-3.5 3-6 7-6s7 2.5 7 6"/></svg> },
    { key: 'stock',      label: 'Stock & Returns', roles: null, icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/></svg> },
    { key: 'expenses',   label: 'Expenses',        roles: null, icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18"/></svg> },
    { key: 'customers',  label: 'Customers',       roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="9" cy="8" r="3"/><path d="M2 20c0-3 3-5 7-5s7 2 7 5"/><circle cx="18" cy="8" r="2.3"/><path d="M15 13.5c2.4.4 4 1.8 4 4.5"/></svg> },
  ]},
  { group: 'Product & Reports', items: [
    { key: 'product',    label: 'Surf Product',    roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M20 7l-8-4-8 4 8 4 8-4z"/><path d="M4 7v10l8 4 8-4V7"/><path d="M12 11v10"/></svg> },
    { key: 'settlement', label: 'Settlement',      roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 4h16v16H4z"/><path d="M8 9h8M8 13h8M8 17h4"/></svg> },
    { key: 'reports',    label: 'Reports',         roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 19V5M10 19V9M16 19v-6M22 19H2"/></svg> },
    { key: 'audit',      label: 'Audit Trail',     roles: ['Super_Admin','Manager'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg> },
  ]},
  { group: 'System', items: [
    { key: 'settings',   label: 'Settings',        roles: ['Super_Admin'], icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="3"/><path d="M12 1v3M12 20v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M1 12h3M20 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/></svg> },
  ]},
];

const PAGE_TITLES = {
  overview: ['Overview', new Date().toLocaleDateString('en-PK',{weekday:'long',day:'numeric',month:'long',year:'numeric'})],
  salesman: ['Salesman Ledger', 'Complete stock, financial & expense ledger per salesman'],
  stock: ['Stock & Returns', 'Salesman returns, condition tracking & daily reconciliation'],
  expenses: ['Expenses', 'Submission, approval & reimbursement tracking'],
  customers: ['Customers', 'Directory, ledgers & customer returns'],
  product: ['Surf Product', 'Stock, pricing, movement & profitability'],
  settlement: ['Settlement', 'Periodic salesman settlement statement'],
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
          <div className="brand-mark">EW</div>
          <div><div className="brand-name">Elite Washwo</div><div className="brand-sub">Surf Stock &amp; Ledger Control</div></div>
        </div>
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
        <div className="sidebar-footer">
          Elite Washwo ERP v1.0<br/>Signed in as: {displayName}
          <button className="logout-btn" onClick={handleLogout}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            Sign out
          </button>
        </div>
      </aside>
      <div className="main">
        <div className="topbar">
          <div><div className="page-title">{title}</div><div className="page-sub">{subtitle}</div></div>
          <div className="topbar-right">
            <div className="search-box">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
              <input 
                type="text" 
                placeholder="Search across page..." 
                value={globalSearch} 
                onChange={e => setGlobalSearch(e.target.value)} 
              />
              {globalSearch && (
                <span onClick={() => setGlobalSearch('')} style={{cursor:'pointer',fontSize:12,color:'var(--text-dim)',padding:'0 4px',lineHeight:1}}>✕</span>
              )}
            </div>
            <div className="bell"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M6 8a6 6 0 0112 0c0 4 1.5 5 1.5 6.5H4.5C4.5 13 6 12 6 8z"/><path d="M9.5 17a2.5 2.5 0 005 0"/></svg></div>
            <div className="user-chip">
              <div className="avatar">{displayName.substring(0,2).toUpperCase()}</div>
              <div className="user-meta"><div className="name">{displayName}</div><div className="role">{displayRole}</div></div>
            </div>
          </div>
        </div>
        <div className="content">
          <div className="page-enter" key={activePage}>
            {renderPage()}
          </div>
        </div>
        <footer className="note">Elite Washwo ERP - All balances derived from transactions. No manual overwrite.</footer>
      </div>
    </div>
  );
}
function OverviewPage({ navigate, searchTerm = '' }) {
  const { data: stats, loading: sl, reload: reloadStats } = useAsync(fetchOverviewStats);
  const [closing, setClosing] = useState(false);
  const [closeMsg, setCloseMsg] = useState('');

  const handleCloseLedger = async () => {
    if (!window.confirm("Are you sure you want to close today's ledger for all active salesmen?")) return;
    setClosing(true);
    setCloseMsg('');
    try {
      const res = await closeTodayLedger();
      setCloseMsg(`ok:Ledger closed successfully for ${res.count} salesmen.`);
      reloadStats();
    } catch (err) {
      setCloseMsg('err:' + err.message);
    } finally {
      setClosing(false);
    }
  };
  const { data: logs,  loading: ll } = useAsync(fetchRecentAuditLogs);
  const { data: snap,  loading: nl } = useAsync(fetchSalesmenSnapshot);
  const { data: chart, loading: cl } = useAsync(fetchChartData);
  const chart1Ref = useRef(null); const chart2Ref = useRef(null);

  useEffect(() => {
    if (!chart || !window.Chart) return;
    const ctx1 = document.getElementById('salesChart');
    const ctx2 = document.getElementById('stockChart');
    if (!ctx1 || !ctx2) return;
    if (chart1Ref.current) chart1Ref.current.destroy();
    if (chart2Ref.current) chart2Ref.current.destroy();
    
    chart1Ref.current = new window.Chart(ctx1, {
      type: 'line',
      data: {
        labels: chart.labels,
        datasets: [
          {label:'Sales',data:chart.sales,borderColor:'#0E7C86',backgroundColor:'rgba(14,124,134,.08)',tension:.35,fill:true,pointRadius:3},
          {label:'Recovery',data:chart.recovery,borderColor:'#E0932E',backgroundColor:'rgba(224,147,46,.08)',tension:.35,fill:true,pointRadius:3}
        ]
      },
      options: { plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } } }, scales: { y: { grid: { color: '#EFEBE0' } }, x: { grid: { display: false } } } }
    });
    
    const total = chart.sales.reduce((s,n) => s+n, 0) || 1;
    const recovery_t = chart.recovery.reduce((s,n) => s+n, 0);
    chart2Ref.current = new window.Chart(ctx2, {
      type: 'doughnut',
      data: {
        labels: ['Sales','Recovery','Outstanding'],
        datasets: [{data:[total, recovery_t, Math.max(0,total-recovery_t)], backgroundColor:['#0E7C86','#2F9E63','#E0932E'], borderWidth:0}]
      },
      options: { plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } } }, cutout: '62%' }
    });
    return () => { chart1Ref.current?.destroy(); chart2Ref.current?.destroy(); };
  }, [chart]);

  if (sl || cl) return <Spinner/>;
  const s = stats || {};

  return (
    <>
      <Msg msg={closeMsg} />
      <div className="ledger-hero">
        <div className="top">
          <div>
            <h1>Today's tally — {new Date().toLocaleDateString('en-PK',{day:'numeric',month:'long',year:'numeric'})}</h1>
            <div className="sub">Across {snap?.length||0} active salesmen · Surf packets only</div>
          </div>
          <button className="btn" onClick={handleCloseLedger} disabled={closing} style={{background:'rgba(255,255,255,.1)',color:'#fff',borderColor:'rgba(255,255,255,.2)'}}>
            {closing ? "Closing ledger..." : "Close today's ledger"}
          </button>
        </div>
        <div className="tally-row">
          <div className="tally"><div className="num">{fmtNum(s.sellable)}</div><div className="lbl">Sellable stock (pkts)</div></div>
          <div className="tally"><div className="num">Rs. <span>{fmtNum(s.salesTotal)}</span></div><div className="lbl">Sales this month</div></div>
          <div className="tally"><div className="num">Rs. <span>{fmtNum(s.recoveryToday)}</span></div><div className="lbl">Recovery today</div></div>
          <div className="tally"><div className="num">Rs. <span>{fmtNum(s.outstanding)}</span></div><div className="lbl">Outstanding</div></div>
          <div className="tally"><div className="num">{fmtNum(s.damaged)}</div><div className="lbl">Damaged (pkts)</div></div>
        </div>
      </div>

      <div className="grid g4" style={{marginBottom:20}}>
        <div className="tile teal"><div className="bar"/><div className="label">Company sellable stock</div><div className="num">{fmtNum(s.sellable)} pkts</div></div>
        <div className="tile amber"><div className="bar"/><div className="label">Pending reimbursements</div><div className="num">Rs. {fmtNum(s.pendingReimb)}</div></div>
        <div className="tile green"><div className="bar"/><div className="label">Today's recovery</div><div className="num">Rs. {fmtNum(s.recoveryToday)}</div></div>
        <div className="tile red"><div className="bar"/><div className="label">Total outstanding</div><div className="num">Rs. {fmtNum(s.outstanding)}</div></div>
      </div>

      <div className="grid g2">
        <div className="panel">
          <div className="section-head"><h2>Sales &amp; recovery — last 7 days</h2><span className="link" onClick={() => navigate('reports')}>View report</span></div>
          <canvas id="salesChart" height="150"/>
        </div>
        <div className="panel">
          <div className="section-head"><h2>Surf — movement breakdown</h2></div>
          <canvas id="stockChart" height="150"/>
        </div>
      </div>

      <div className="grid g2" style={{marginTop:20}}>
        <div className="panel">
          <div className="section-head"><h2>Recent activity</h2><span className="link" onClick={() => navigate('audit')}>Full audit trail</span></div>
          <div className="timeline">
            {ll ? <div style={{padding:12,color:'var(--text-dim)',fontSize:12}}>Loading...</div> :
              filteredLogs.length===0 ? <div style={{padding:12,color:'var(--text-dim)',fontSize:12}}>No matching activity found.</div> :
              filteredLogs.map(l => (
                <div key={l.id} className="tl-item">
                  <div className="tl-dot" style={{background: l.action==='INSERT'?'var(--teal)':l.action==='UPDATE'?'var(--amber)':'var(--red)'}}/>
                  <div className="tl-body">
                    <div className="t">{l.action} on {l.table_name} by {l.profiles?.full_name||'System'}</div>
                    <div className="d">{fmtTime(l.created_at)}</div>
                  </div>
                </div>
              ))
            }
          </div>
        </div>
        <div className="panel">
          <div className="section-head"><h2>Salesmen snapshot</h2></div>
          {nl ? <Spinner/> : (
            <table>
              <thead><tr><th>Salesman</th><th>Stock</th><th>Outstanding</th><th>Status</th></tr></thead>
              <tbody>
                {(snap||[]).length===0 ? <Empty msg="No salesmen found. Add salesmen to Supabase."/> :
                  filteredSnap.map(sm => (
                    <tr key={sm.id}>
                      <td>{sm.name}</td>
                      <td className="num-cell">{fmtNum(sm.stock)} pkts</td>
                      <td className="num-cell">Rs. {fmtNum(sm.outstanding)}</td>
                      <td><span className={`badge ${sm.outstanding>0?'amber':'green'}`}>{sm.outstanding>0?'Open':'Closed'}</span></td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}

function SalesmanPage({ searchTerm = '' }) {
  const { role, user } = useAuth();
  const [selectedId, setSelectedId] = useState(null);
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
  }, [salesmen, role]);

  const { data: stats, loading: tl } = useAsync(() => sid ? fetchSalesmanStats(sid) : Promise.resolve(null), [sid]);
  const { data: stock, loading: stL } = useAsync(() => sid ? fetchSalesmanStockLedger(sid) : Promise.resolve([]), [sid, activeTab]);
  const { data: fin,   loading: fL } = useAsync(() => sid ? fetchSalesmanFinLedger(sid) : Promise.resolve([]), [sid, activeTab]);
  const { data: exp,   loading: eL } = useAsync(() => sid ? fetchSalesmanExpLedger(sid) : Promise.resolve([]), [sid, activeTab]);

  if (sl) return <Spinner/>;
  const st = stats || {};

  return (
    <>
      <div className="panel" style={{marginBottom:20}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:14}}>
          <div style={{display:'flex',alignItems:'center',gap:14}}>
            <div className="avatar" style={{width:52,height:52,fontSize:17}}>{selected?.profiles?.full_name?.substring(0,2)?.toUpperCase()||'--'}</div>
            <div>
              <div style={{fontSize:16,fontWeight:600}}>{selected?.profiles?.full_name||'—'} · #{selected?.code||'—'}</div>
              <div style={{fontSize:12,color:'var(--text-dim)'}}>Route: {selected?.route||'—'}</div>
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
        <div className="tabs">
          {[['stockLedger','Stock Ledger'],['finLedger','Financial Ledger'],['expLedger','Expense Ledger']].map(([k,l]) => (
            <div key={k} className={`tab${activeTab===k?' active':''}`} onClick={() => setActiveTab(k)}>{l}</div>
          ))}
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
                        <td className="num-cell">{r.transaction_type==='Salesman_Issue'?r.quantity:'—'}</td>
                        <td className="num-cell">{['Sale','Salesman_Good_Return','Salesman_Damaged_Return'].includes(r.transaction_type)?r.quantity:'—'}</td>
                        <td>{statusBadge(r.status)}</td>
                      </tr>
                    ))
                  }
                </tbody>
              </table>
            </div>
          )
        )}

        {activeTab === 'finLedger' && (
          fL ? <Spinner/> : (
            <table>
              <thead><tr><th>Date</th><th>Type</th><th>Reference</th><th>Debit</th><th>Credit</th><th>Balance</th><th>Status</th></tr></thead>
              <tbody>
                {paginatedFin.length===0 ? <Empty msg={isFiltered || query ? "No matching financial records found." : "No financial transactions yet."}/> :
                  paginatedFin.map((r,i) => (
                    <tr key={i}>
                      <td>{fmtDate(r.date)}</td>
                      <td>{r.type}</td>
                      <td style={{fontSize:11,color:'var(--text-dim)'}}>{r.ref}</td>
                      <td className="num-cell">{r.debit?`Rs. ${fmtNum(r.debit)}`:'—'}</td>
                      <td className="num-cell">{r.credit?`Rs. ${fmtNum(r.credit)}`:'—'}</td>
                      <td className="num-cell" style={{color:r.balance>0?'var(--red)':'var(--green)'}}>Rs. {fmtNum(Math.abs(r.balance))}</td>
                      <td>{statusBadge(r.status)}</td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
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
                        <td style={{fontSize:11,color:'var(--text-dim)'}}>{r.description||'—'}</td>
                        <td>{statusBadge(r.status)}</td>
                      </tr>
                    ))
                  }
                </tbody>
              </table>
            </div>
          )
        )}
      </div>
    </>
  );
}
function StockPage({ searchTerm = '' }) {
  const { data: salesmen }   = useAsync(fetchSalesmen);
  const { data: packagings } = useAsync(fetchPackagings);
  const { role, hasPermission } = useAuth();


  const [form, setForm] = useState({ salesmanId:'', packagingId:'', returnType:'Salesman_Good_Return', quantity:'', notes:'' });
  useEffect(() => {
    if (role === 'Salesman' && salesmen?.length) {
      const own = salesmen.find(s => s.profile_id === user?.id);
      if (own && !form.salesmanId) {
        setForm(f => ({ ...f, salesmanId: own.id }));
      }


function Pagination({ page, pageSize, total, onPageChange }) {
  if (total <= pageSize) return null;
  const totalPages = Math.ceil(total / pageSize);
  const start = (page - 1) * pageSize;
  const end = Math.min(start + pageSize, total);

  return (
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginTop:14,paddingTop:12,borderTop:'1px solid var(--line)',fontSize:12,color:'var(--text-dim)'}}>
      <div>Showing {start + 1}–{end} of {total} records</div>
      <div style={{display:'flex',gap:6,alignItems:'center'}}>
        <button className="btn" disabled={page <= 1} onClick={() => onPageChange(page - 1)} style={{padding:'4px 10px',fontSize:12}}>Previous</button>
        <span style={{fontSize:12,color:'var(--text)'}}>Page {page} of {totalPages}</span>
        <button className="btn" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)} style={{padding:'4px 10px',fontSize:12}}>Next</button>
      </div>
    </div>
  );
}

    }
  }, [role, salesmen, user]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.salesmanId || !form.packagingId || !form.quantity) { setMsg('err:Please fill all required fields.'); return; }
    setSaving(true); setMsg('');
    try {
      const pkg = (packagings||[]).find(p => p.id === form.packagingId);
      const unit_cost = pkg?.product_prices?.[0]?.unit_cost || 0;
      await submitStockReturn({ salesmanId:form.salesmanId, packagingId:form.packagingId, transaction_type:form.returnType, quantity:form.quantity, notes:form.notes, unit_cost });
      setMsg('ok:Return submitted for approval.');
      setForm({salesmanId:'',packagingId:'',returnType:'Salesman_Good_Return',quantity:'',notes:''});
      reload();
    } catch(e) { setMsg('err:'+e.message); } finally { setSaving(false); }
  };

  const handleApprove = async (id) => {
    try { await approveTransaction(id); reload(); } catch(e) { alert(e.message); }
  };

  const [localSearch, setLocalSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const returns = (txns||[]).filter(t => ['Salesman_Good_Return','Salesman_Damaged_Return','Customer_Good_Return','Customer_Damaged_Return'].includes(t.transaction_type));

  const query = (localSearch || searchTerm).trim().toLowerCase();

  const filteredReturns = returns.filter(r => {
    if (statusFilter !== 'All' && r.status !== statusFilter) return false;
    if (typeFilter === 'Good' && !['Salesman_Good_Return','Customer_Good_Return'].includes(r.transaction_type)) return false;
    if (typeFilter === 'Damaged' && !['Salesman_Damaged_Return','Customer_Damaged_Return'].includes(r.transaction_type)) return false;
    if (!query) return true;
    return (
      (r.reference_number || '').toLowerCase().includes(query) ||
      (r.salesmen?.profiles?.full_name || '').toLowerCase().includes(query) ||
      (r.transaction_type || '').toLowerCase().includes(query) ||
      (r.status || '').toLowerCase().includes(query) ||
      (r.notes || '').toLowerCase().includes(query) ||
      fmtDate(r.transaction_date).toLowerCase().includes(query)
    );
  });

  const paginatedReturns = filteredReturns.slice((page - 1) * pageSize, page * pageSize);
  const isFiltered = localSearch || statusFilter !== 'All' || typeFilter !== 'All';
  const resetFilters = () => { setLocalSearch(''); setStatusFilter('All'); setTypeFilter('All'); setPage(1); };

  const handleExportReturnsCsv = () => {
    const headers = ['Reference', 'Date', 'Salesman', 'Type', 'Quantity', 'Status', 'Notes'];
    const rows = filteredReturns.map(r => [
      r.reference_number,
      fmtDate(r.transaction_date),
      r.salesmen?.profiles?.full_name || '—',
      r.transaction_type,
      r.quantity,
      r.status,
      r.notes || ''
    ]);
    exportToCsv('Stock_Returns', headers, rows);
  };

  return (
    <>
      <div className="grid g2">
        <div className="panel">
          <div className="section-head"><h2>New stock return</h2></div>
          <Msg msg={msg} />
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="field">
                <label>Salesman *</label>
                <select value={form.salesmanId} onChange={e=>setForm(f=>({...f,salesmanId:e.target.value}))}>
                  <option value="">— Select —</option>
                  {filteredSalesmen.map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Product *</label>
                <select value={form.packagingId} onChange={e=>setForm(f=>({...f,packagingId:e.target.value}))}>
                  <option value="">— Select —</option>
                  {(packagings||[]).map(p=><option key={p.id} value={p.id}>{p.products?.name} — {p.name}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Return type</label>
                <select value={form.returnType} onChange={e=>setForm(f=>({...f,returnType:e.target.value}))}>
                  <option value="Salesman_Good_Return">Unsold Return (Good)</option>
                  <option value="Salesman_Damaged_Return">Damaged Return</option>
                  <option value="Customer_Good_Return">Customer Return (Good)</option>
                  <option value="Customer_Damaged_Return">Customer Return (Damaged)</option>
                </select>
              </div>
              <div className="field">
                <label>Quantity *</label>
                <input type="number" min="1" placeholder="e.g. 20" value={form.quantity} onChange={e=>setForm(f=>({...f,quantity:e.target.value}))}/>
              </div>
              <div className="field" style={{gridColumn:'1/-1'}}>
                <label>Notes</label>
                <textarea rows={2} placeholder="Optional notes" value={form.notes} onChange={e=>setForm(f=>({...f,notes:e.target.value}))}/>
              </div>
            </div>
            <div className="btn-row" style={{marginTop:16}}>
              <button type="submit" className="btn primary" disabled={saving}>{saving?'Submitting...':'Submit for approval'}</button>
            </div>
          </form>
        </div>

        <div className="panel">
          <div className="section-head"><h2>Stock movement summary</h2></div>
          <table>
            <tbody>
              <tr><td>Total returns submitted</td><td className="num-cell" style={{textAlign:'right'}}>{returns.length}</td></tr>
              <tr><td>Pending approval</td><td className="num-cell" style={{textAlign:'right'}}>{returns.filter(r=>r.status==='Pending').length}</td></tr>
              <tr><td>Approved</td><td className="num-cell" style={{textAlign:'right'}}>{returns.filter(r=>r.status==='Approved').length}</td></tr>
              <tr><td>Good condition returns</td><td className="num-cell" style={{textAlign:'right'}}>{returns.filter(r=>['Salesman_Good_Return','Customer_Good_Return'].includes(r.transaction_type)).length}</td></tr>
              <tr><td>Damaged returns</td><td className="num-cell" style={{textAlign:'right'}}>{returns.filter(r=>['Salesman_Damaged_Return','Customer_Damaged_Return'].includes(r.transaction_type)).length}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel" style={{marginTop:20}}>
        <div className="section-head"><h2>Return transactions</h2></div>
        {tl ? <Spinner/> : (
          <table>
            <thead><tr><th>Reference</th><th>Date</th><th>Salesman</th><th>Type</th><th>Qty</th><th>Status</th>{(hasPermission('inventory.approve'))&&<th></th>}</tr></thead>
            <tbody>
              {paginatedReturns.length===0 ? <Empty msg={isFiltered || query ? "No matching return transactions found." : "No return transactions yet."}/> :
                paginatedReturns.map(r=>(
                  <tr key={r.id}>
                    <td style={{fontSize:11}}>{r.reference_number}</td>
                    <td>{fmtDate(r.transaction_date)}</td>
                    <td>{r.salesmen?.profiles?.full_name||'—'}</td>
                    <td>{r.transaction_type?.replace(/_/g,' ')}</td>
                    <td className="num-cell">{r.quantity}</td>
                    <td>{statusBadge(r.status)}</td>
                    {(hasPermission('inventory.approve'))&&<td>{r.status==='Pending'&&<span className="link" onClick={()=>handleApprove(r.id)}>Approve</span>}</td>}
                  </tr>
                ))
              }
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function ExpensesPage({ searchTerm = '' }) {
  const { data: salesmen } = useAsync(fetchSalesmen);
  const { data: expenses, loading: el, reload } = useAsync(fetchExpenses);
  const { data: summary } = useAsync(fetchExpenseSummary);
  const { role, hasPermission } = useAuth();


  const [form, setForm] = useState({ salesmanId:'', category:'Fuel', amount:'', paid_by:'Salesman', payment_method:'Cash', description:'' });
  useEffect(() => {
    if (role === 'Salesman' && salesmen?.length) {
      const own = salesmen.find(s => s.profile_id === user?.id);
      if (own && !form.salesmanId) {
        setForm(f => ({ ...f, salesmanId: own.id }));
      }
    }
  }, [role, salesmen, user]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.salesmanId || !form.amount) { setMsg('err:Please fill all required fields.'); return; }
    setSaving(true); setMsg('');
    try {
      await submitExpense({ salesmanId:form.salesmanId, category:form.category, amount:form.amount, description:form.description, paid_by:form.paid_by, payment_method:form.payment_method });
      setMsg('ok:Expense submitted.');
      setForm({salesmanId:'',category:'Fuel',amount:'',paid_by:'Salesman',payment_method:'Cash',description:''});
      reload();
    } catch(e) { setMsg('err:'+e.message); } finally { setSaving(false); }
  };

  const handleStatus = async (id, status) => {
    try { await updateExpenseStatus(id, status); reload(); } catch(e) { alert(e.message); }
  };

  const sm = summary||{};
  const [localSearch, setLocalSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const query = (localSearch || searchTerm).trim().toLowerCase();

  const filteredExpenses = (expenses || []).filter(r => {
    if (statusFilter !== 'All' && r.status !== statusFilter) return false;
    if (categoryFilter !== 'All' && r.category !== categoryFilter) return false;
    if (!query) return true;
    return (
      (r.reference_number || '').toLowerCase().includes(query) ||
      (r.salesmen?.profiles?.full_name || '').toLowerCase().includes(query) ||
      (r.category || '').toLowerCase().includes(query) ||
      (r.description || '').toLowerCase().includes(query) ||
      (r.paid_by || '').toLowerCase().includes(query) ||
      (r.status || '').toLowerCase().includes(query) ||
      fmtDate(r.expense_date).toLowerCase().includes(query)
    );
  });

  const paginatedExpenses = filteredExpenses.slice((page - 1) * pageSize, page * pageSize);
  const isFiltered = localSearch || statusFilter !== 'All' || categoryFilter !== 'All';
  const resetFilters = () => { setLocalSearch(''); setStatusFilter('All'); setCategoryFilter('All'); setPage(1); };

  const handleExportExpensesCsv = () => {
    const headers = ['Reference', 'Date', 'Salesman', 'Category', 'Amount', 'Paid By', 'Status', 'Description'];
    const rows = filteredExpenses.map(r => [
      r.reference_number,
      fmtDate(r.expense_date),
      r.salesmen?.profiles?.full_name || '—',
      r.category,
      r.amount,
      r.paid_by || '—',
      r.status,
      r.description || ''
    ]);
    exportToCsv('Expenses_Ledger', headers, rows);
  };

  return (
    <>
      <div className="grid g2">
        <div className="panel">
          <div className="section-head"><h2>Submit expense</h2></div>
          <Msg msg={msg} />
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="field">
                <label>Salesman *</label>
                <select value={form.salesmanId} onChange={e=>setForm(f=>({...f,salesmanId:e.target.value}))}>
                  <option value="">— Select —</option>
                  {(salesmen||[]).map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Category</label>
                <select value={form.category} onChange={e=>setForm(f=>({...f,category:e.target.value}))}>
                  {['Fuel','Transport','Loading','Unloading','Food','Mobile/Communication','Repair','Other'].map(c=><option key={c}>{c}</option>)}
                </select>
              </div>
              <div className="field"><label>Amount (Rs.) *</label><input type="number" min="1" placeholder="500" value={form.amount} onChange={e=>setForm(f=>({...f,amount:e.target.value}))}/></div>
              <div className="field">
                <label>Paid by</label>
                <select value={form.paid_by} onChange={e=>setForm(f=>({...f,paid_by:e.target.value}))}>
                  <option>Salesman</option><option>Company</option>
                </select>
              </div>
              <div className="field">
                <label>Payment method</label>
                <select value={form.payment_method} onChange={e=>setForm(f=>({...f,payment_method:e.target.value}))}>
                  <option>Cash</option><option>Bank</option>
                </select>
              </div>
              <div className="field" style={{gridColumn:'1/-1'}}>
                <label>Description</label>
                <textarea rows={2} placeholder="Optional description" value={form.description} onChange={e=>setForm(f=>({...f,description:e.target.value}))}/>
              </div>
            </div>
            <div className="btn-row" style={{marginTop:16}}>
              <button type="submit" className="btn primary" disabled={saving}>{saving?'Submitting...':'Submit expense'}</button>
            </div>
          </form>
        </div>

        <div className="panel">
          <div className="section-head"><h2>Expense summary — this month</h2></div>
          <div className="grid g2" style={{marginBottom:16}}>
            <div className="tile amber"><div className="bar"/><div className="label">Total expenses</div><div className="num">Rs. {fmtNum(sm.total)}</div></div>
            <div className="tile red"><div className="bar"/><div className="label">Pending reimbursement</div><div className="num">Rs. {fmtNum(sm.pending)}</div></div>
          </div>
          <div style={{fontSize:12.5,color:'var(--text-dim)',marginBottom:6}}>Company-paid vs salesman-paid</div>
          <div className="progress" style={{marginBottom:6}}><div style={{width:`${sm.companyPct||0}%`}}/></div>
          <div style={{fontSize:11.5,color:'var(--text-dim)'}}>Company Rs. {fmtNum(sm.company)} ({sm.companyPct||0}%) · Salesman Rs. {fmtNum(sm.salesman)} ({100-(sm.companyPct||0)}%)</div>
        </div>
      </div>

      <div className="panel" style={{marginTop:20}}>
        <div className="section-head"><h2>Expense approvals</h2></div>
        {el ? <Spinner/> : (
          <table>
            <thead><tr><th>Reference</th><th>Date</th><th>Salesman</th><th>Category</th><th>Amount</th><th>Paid by</th><th>Status</th>{(hasPermission('expenses.approve'))&&<th></th>}</tr></thead>
            <tbody>
              {paginatedExpenses.length===0 ? <Empty msg={isFiltered || query ? "No matching expenses found." : "No expenses yet."}/> :
                paginatedExpenses.map(r=>(
                  <tr key={r.id}>
                    <td style={{fontSize:11}}>{r.reference_number}</td>
                    <td>{fmtDate(r.expense_date)}</td>
                    <td>{r.salesmen?.profiles?.full_name||'—'}</td>
                    <td>{r.category}</td>
                    <td className="num-cell">Rs. {fmtNum(r.amount)}</td>
                    <td>{r.paid_by||'—'}</td>
                    <td>{statusBadge(r.status)}</td>
                    {(hasPermission('expenses.approve'))&&<td>
                      {r.status==='Pending'&&<>
                        <span className="link" onClick={()=>handleStatus(r.id,'Approved')} style={{marginRight:8}}>Approve</span>
                        <span className="link" style={{color:'var(--red)'}} onClick={()=>handleStatus(r.id,'Cancelled')}>Reject</span>
                      </>}
                    </td>}
                  </tr>
                ))
              }
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
function CustomersPage({ searchTerm = '' }) {
  const { data: customers, loading: cl, reload } = useAsync(fetchCustomers);
  const { data: salesmen } = useAsync(fetchSalesmen);
  const { data: cReturns, loading: rl } = useAsync(fetchCustomerReturns);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ code:'', name:'', phone:'', address:'', default_salesman_id:'' });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

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

  return (
    <>
      <div className="panel">
        <div className="section-head">
          <h2>Customer directory</h2>
          <span className="link" onClick={()=>setShowAdd(s=>!s)}>{showAdd?'Cancel':'Add customer'}</span>
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
                  <option value="">— None —</option>
                  {(salesmen||[]).map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
                </select>
              </div>
              <div className="field" style={{gridColumn:'1/-1'}}><label>Address</label><input placeholder="Area / locality" value={form.address} onChange={e=>setForm(f=>({...f,address:e.target.value}))}/></div>
            </div>
            <button type="submit" className="btn primary" style={{marginTop:12}} disabled={saving}>{saving?'Saving...':'Add Customer'}</button>
          </form>
        )}

        {cl ? <Spinner/> : (
          <table>
            <thead><tr><th>Customer</th><th>Area</th><th>Salesman</th><th>Outstanding</th></tr></thead>
            <tbody>
              {paginatedCustomers.length===0 ? <Empty msg={isCustFiltered || query ? "No customers found matching search criteria." : "No customers yet."}/> :
                paginatedCustomers.map(c=>(
                  <tr key={c.id}>
                    <td>
    <div style={{fontWeight:600}}>{c.name}</div>
    <div style={{fontSize:11,color:'var(--text-dim)',display:'flex',alignItems:'center',gap:6}}>
      <span>{c.code}</span>
      {c.phone && (
        <span 
          className="link" 
          onClick={() => shareOnWhatsApp({
            title: 'Customer Balance Notice',
            lines: [`*Customer:* ${c.name} (${c.code})`, `*Area:* ${c.address || '—'}`, `*Outstanding Balance:* Rs. ${fmtNum(c.outstanding)}`],
            phone: c.phone
          })}
          style={{color:'var(--teal)',fontWeight:500}}
        >
          WhatsApp
        </span>
      )}
    </div>
  </td>
                    <td>{c.address||'—'}</td>
                    <td>{c.salesmen?.profiles?.full_name||'—'}</td>
                    <td className="num-cell" style={{color:c.outstanding>0?'var(--red)':'inherit'}}>Rs. {fmtNum(c.outstanding)}</td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        )}
      </div>

      <div className="panel" style={{marginTop:20}}>
        <div className="section-head"><h2>Customer returns</h2></div>
        {rl ? <Spinner/> : (
          <table>
            <thead><tr><th>Reference</th><th>Date</th><th>Customer</th><th>Salesman</th><th>Type</th><th>Qty</th><th>Status</th></tr></thead>
            <tbody>
              {paginatedReturns.length===0 ? <Empty msg={retQuery ? "No matching customer returns found." : "No customer returns yet."}/> :
                paginatedReturns.map(r=>(
                  <tr key={r.id}>
                    <td style={{fontSize:11}}>{r.reference_number}</td>
                    <td>{fmtDate(r.transaction_date)}</td>
                    <td>{r.customers?.name||'—'}</td>
                    <td>{r.salesmen?.profiles?.full_name||'—'}</td>
                    <td>{r.transaction_type?.replace(/_/g,' ')}</td>
                    <td className="num-cell">{r.quantity}</td>
                    <td>{statusBadge(r.status)}</td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function ProductPage({ searchTerm = '' }) {
  const { data: products, loading: pl } = useAsync(fetchProducts);
  const { data: movement, loading: ml } = useAsync(fetchProductMovement);
  const mv = movement||{};
  const [localSearch, setLocalSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const query = (localSearch || searchTerm).trim().toLowerCase();

  const allPriceRows = (products || []).flatMap(p =>
    (p.product_packaging || []).map(pkg => {
      const price = pkg.product_prices?.[0];
      return {
        id: pkg.id,
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

  const handleExportProductsCsv = () => {
    const headers = ['Product Name', 'Packaging', 'Unit Cost (PKR)', 'Sales Price (PKR)'];
    const rows = filteredPrices.map(r => [
      r.productName,
      r.packagingName,
      r.unitCost || 0,
      r.salesPrice || 0
    ]);
    exportToCsv('Products_and_Pricing', headers, rows);
  };

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
        <div className="section-head"><h2>Products &amp; pricing</h2></div>
        {pl ? <Spinner/> : (
          <table>
            <thead><tr><th>Product</th><th>Packaging</th><th>Cost price</th><th>Sales price</th></tr></thead>
            <tbody>
              {paginatedPrices.length===0 ? <Empty msg={isFiltered || query ? "No products found matching search criteria." : "No products found."}/> :
                (products||[]).flatMap(p=>
                  (p.product_packaging||[]).map(pkg=>{
                    const price = pkg.product_prices?.[0];
                    return (
                      <tr key={pkg.id}>
                        <td>{p.name}</td>
                        <td>{pkg.name}</td>
                        <td className="num-cell">Rs. {fmtNum(price?.unit_cost)}</td>
                        <td className="num-cell">Rs. {fmtNum(price?.sales_price)}</td>
                      </tr>
                    );
                  })
                )
              }
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function SettlementPage({ searchTerm = '' }) {
  const { data: salesmen } = useAsync(fetchSalesmen);
  const [selectedId, setSelectedId] = useState('');
  const { data: settlement, loading: sl } = useAsync(() => selectedId ? fetchSalesmanSettlement(selectedId) : Promise.resolve(null), [selectedId]);
  const query = (searchTerm || '').trim().toLowerCase();
  const filteredSalesmen = (salesmen || []).filter(s => !query || (s.profiles?.full_name || '').toLowerCase().includes(query) || (s.code || '').toLowerCase().includes(query));
  const selected = (salesmen||[]).find(s=>s.id===selectedId);
  const sv = settlement||{};

  return (
    <div className="panel">
      <div className="section-head"><h2>Salesman settlement</h2></div>
      <div className="field" style={{marginBottom:20,maxWidth:300}}>
        <label>Select Salesman</label>
        <select value={selectedId} onChange={e=>setSelectedId(e.target.value)}>
          <option value="">— Select salesman —</option>
          {(salesmen||[]).map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
        </select>
      </div>

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
                  {sv.net>0?`Rs. ${fmtNum(sv.net)} payable by ${selected?.profiles?.full_name||'salesman'}`:`Rs. ${fmtNum(Math.abs(sv.net))} payable to ${selected?.profiles?.full_name||'salesman'}`}
                </strong>
              </td></tr>
            </tbody>
          </table>
          <div className="btn-row" style={{marginTop:16}}>
            <button className="btn primary">Approve settlement</button>
          </div>
        </>
      ))}

      {!selectedId && <div style={{padding:24,textAlign:'center',color:'var(--text-dim)',fontSize:13}}>Select a salesman above to view their settlement.</div>}
    </div>
  );
}

function ReportsPage() {
  return (
    <>
      <div className="grid g3">
        <div className="panel-flat"><h3 style={{fontSize:14,marginBottom:6}}>Daily closing report</h3><p style={{fontSize:12.5,color:'var(--text-dim)',marginBottom:14}}>Stock + cash + expense reconciliation for all salesmen, per day.</p><button className="btn">Open</button></div>
        <div className="panel-flat"><h3 style={{fontSize:14,marginBottom:6}}>Product movement report</h3><p style={{fontSize:12.5,color:'var(--text-dim)',marginBottom:14}}>Opening, production, sales, returns, damages, closing — by product.</p><button className="btn">Open</button></div>
        <div className="panel-flat"><h3 style={{fontSize:14,marginBottom:6}}>Expense report</h3><p style={{fontSize:12.5,color:'var(--text-dim)',marginBottom:14}}>Filter by salesman, category, paid-by and status.</p><button className="btn">Open</button></div>
        <div className="panel-flat"><h3 style={{fontSize:14,marginBottom:6}}>Salesman statement (PDF)</h3><p style={{fontSize:12.5,color:'var(--text-dim)',marginBottom:14}}>Stock, sales, recovery, returns, damages, expenses.</p><button className="btn">Generate</button></div>
        <div className="panel-flat"><h3 style={{fontSize:14,marginBottom:6}}>Profitability report</h3><p style={{fontSize:12.5,color:'var(--text-dim)',marginBottom:14}}>Revenue, COGS, gross profit, expenses, net profit.</p><button className="btn">Open</button></div>
        <div className="panel-flat"><h3 style={{fontSize:14,marginBottom:6}}>Variance report</h3><p style={{fontSize:12.5,color:'var(--text-dim)',marginBottom:14}}>All stock/cash shortages &amp; excesses.</p><button className="btn">Open</button></div>
      </div>
    </>
  );
}

function AuditPage({ searchTerm = '' }) {
  const { data: logs, loading: ll } = useAsync(fetchAuditLogs);
  return (
    <div className="panel">
      <div className="section-head"><h2>Audit trail</h2></div>
      {ll ? <Spinner/> : (
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
      )}
    </div>
  );
}

createRoot(document.getElementById('root')).render(<Root/>);


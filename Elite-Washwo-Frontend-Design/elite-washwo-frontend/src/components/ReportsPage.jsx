import React, { useState, useEffect } from 'react';
import { fetchReportsMetrics } from '../lib/db';

const fmtNum = (n) => Number(n || 0).toLocaleString();
const fmtDate = (d) => {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' });
};
const fmtDateTime = (d) => {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};

export default function ReportsPage() {
  const todayStr = new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState(todayStr);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Table search states
  const [bookingSearch, setBookingSearch] = useState('');
  const [recoverySearch, setRecoverySearch] = useState('');
  const [expenseSearch, setExpenseSearch] = useState('');
  const [returnSearch, setReturnSearch] = useState('');

  const loadData = async (dateStr) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReportsMetrics(dateStr);
      setMetrics(data);
    } catch (e) {
      console.error(e);
      setError('Unable to load reports. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(selectedDate);
  }, [selectedDate]);

  const handlePrint = () => {
    window.print();
  };

  const handleWhatsApp = () => {
    if (!metrics) return;
    
    // Sum specific returns
    const goodRtn = metrics.returns.records.filter(r => r.transaction_type === 'Salesman_Good_Return').reduce((a, r) => a + Number(r.quantity), 0);
    const dmgRtn = metrics.returns.records.filter(r => r.transaction_type === 'Salesman_Damaged_Return').reduce((a, r) => a + Number(r.quantity), 0);
    
    // Sum total expenses
    const expAmount = metrics.expense.records.reduce((a, e) => a + Number(e.amount), 0);
    const recAmount = metrics.recovery.records.reduce((a, r) => a + Number(r.amount), 0);
    const bkgAmount = metrics.booking.records.reduce((a, b) => a + Number(b.total_amount), 0);
    
    const msg = `*EliteWash ERP - Financial Report*\n` +
      `Date: ${fmtDate(selectedDate)}\n\n` +
      `*Daily Activity*\n` +
      `Sales: PKR ${fmtNum(metrics.sales.amount)} (${fmtNum(metrics.sales.packets)} pkts)\n` +
      `Bookings: PKR ${fmtNum(bkgAmount)} (${fmtNum(metrics.booking.records.reduce((a, b) => a + b.packets, 0))} pkts)\n` +
      `Recovery: PKR ${fmtNum(recAmount)}\n` +
      `Expenses: PKR ${fmtNum(expAmount)}\n\n` +
      `*Financial Accounts*\n` +
      `Distributor Commission Balance: PKR ${fmtNum(metrics.distributorCommission.balance)}\n` +
      `Advertisement Account Balance: PKR ${fmtNum(metrics.advertisement.balance)}\n` +
      `Welfare Account Balance: PKR ${fmtNum(metrics.welfare.balance)}\n\n` +
      `*Returns*\n` +
      `Distributor Return Stock: ${fmtNum(goodRtn)} pkts\n` +
      `Damage Return Stock: ${fmtNum(dmgRtn)} pkts`;
      
    const encoded = encodeURIComponent(msg);
    window.open(`https://wa.me/923240106056?text=${encoded}`, '_blank');
  };

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="panel" style={{ textAlign: 'center', padding: 40, color: 'var(--red)', background: 'var(--red-soft)', border: '1px solid #f0c8c4' }}>
          <p style={{ marginBottom: 14 }}>{error}</p>
          <button className="btn primary" onClick={() => loadData(selectedDate)}>Retry</button>
        </div>
      </div>
    );
  }

  // Derived calculations
  let bkgAmount = 0, bkgPackets = 0, recAmount = 0, expAmount = 0;
  let expDist = 0, expComp = 0, expOff = 0, expOth = 0;
  let goodReturnQty = 0, dmgReturnQty = 0;

  if (metrics) {
    bkgAmount = metrics.booking.records.reduce((a, b) => a + Number(b.total_amount || 0), 0);
    bkgPackets = metrics.booking.records.reduce((a, b) => a + b.packets, 0);
    recAmount = metrics.recovery.records.reduce((a, r) => a + Number(r.amount || 0), 0);
    
    metrics.expense.records.forEach(e => {
      const a = Number(e.amount || 0);
      expAmount += a;
      if (e.category === 'Distributor') expDist += a;
      else if (e.category === 'Company') expComp += a;
      else if (e.category === 'Office') expOff += a;
      else if (e.category === 'Others') expOth += a;
    });
    
    metrics.returns.records.forEach(r => {
      if (r.transaction_type === 'Salesman_Good_Return') goodReturnQty += Number(r.quantity || 0);
      if (r.transaction_type === 'Salesman_Damaged_Return') dmgReturnQty += Number(r.quantity || 0);
    });
  }

  const expPct = (val) => expAmount > 0 ? Math.round((val / expAmount) * 100) : 0;

  // Filtered lists
  const filterList = (list, search, fields) => {
    if (!search) return list;
    const q = search.toLowerCase();
    return list.filter(item => fields.some(f => {
      const val = f.split('.').reduce((obj, key) => obj && obj[key], item);
      return val && String(val).toLowerCase().includes(q);
    }));
  };

  const filteredBookings = metrics ? filterList(metrics.booking.records, bookingSearch, ['reference_number', 'distributors.code', 'distributors.name']) : [];
  const filteredRecoveries = metrics ? filterList(metrics.recovery.records, recoverySearch, ['distributors.code', 'distributors.name', 'notes']) : [];
  const filteredExpenses = metrics ? filterList(metrics.expense.records, expenseSearch, ['reference_number', 'distributors.code', 'distributors.name', 'head', 'description']) : [];
  const filteredReturns = metrics ? filterList(metrics.returns.records, returnSearch, ['reference_number', 'distributors.code', 'distributors.name', 'notes']) : [];

  return (
    <div className="dashboard-container reports-print-wrapper">
      
      {/* HEADER */}
      <div className="dash-header no-print">
        <div>
          <h1>Reports</h1>
          <p>Business reports and financial summaries</p>
        </div>
        <div className="dash-date-control" style={{ display: 'flex', gap: 10 }}>
          <button className="btn ghost" onClick={handlePrint}>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: 6 }}><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            Print Report
          </button>
          <button className="btn" style={{ background: '#25D366', color: '#fff', borderColor: '#25D366' }} onClick={handleWhatsApp}>
            WhatsApp Report
          </button>
          <div style={{ width: 1, background: 'var(--line)', margin: '0 4px' }}></div>
          <input 
            type="date" 
            value={selectedDate} 
            onChange={(e) => setSelectedDate(e.target.value || todayStr)}
          />
          <button className="btn-today" onClick={() => setSelectedDate(todayStr)}>Today</button>
        </div>
      </div>

      <div className="print-only-header" style={{ display: 'none', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24 }}>EliteWash Financial Report</h1>
        <p style={{ margin: '4px 0 0 0', color: '#555' }}>Report Date: {fmtDate(selectedDate)}</p>
      </div>

      {!loading && metrics && (
        <div style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 16 }} className="no-print">
          Report Date: <strong style={{ color: 'var(--ink)' }}>{fmtDate(selectedDate)}</strong>
        </div>
      )}

      {loading ? (
        <div className="panel" style={{ padding: 60, textAlign: 'center', color: 'var(--text-dim)', border: 'none', background: 'transparent' }}>
          <div className="splash-loader" style={{ minHeight: 'auto', padding: 0, background: 'transparent' }}>
            <div className="brand-mark" style={{ width: 44, height: 44, fontSize: 16 }}>EW</div>
            <p>Loading financial data...</p>
          </div>
        </div>
      ) : metrics && (
        <>
          {/* SUMMARY KPI CARDS */}
          <div className="grid g4" style={{ marginBottom: 20 }}>
            <div className="tile teal">
              <div className="label">Total Sales</div>
              <div className="num">PKR {fmtNum(metrics.sales.amount)}</div>
              <div className="delta up">{fmtNum(metrics.sales.packets)} pkts</div>
            </div>
            <div className="tile amber">
              <div className="label">Total Bookings</div>
              <div className="num">PKR {fmtNum(bkgAmount)}</div>
              <div className="delta down">{fmtNum(bkgPackets)} pkts</div>
            </div>
            <div className="tile green">
              <div className="label">Recovery Amount</div>
              <div className="num">PKR {fmtNum(recAmount)}</div>
              <div className="delta up">Valid recoveries</div>
            </div>
            <div className="tile red">
              <div className="label">Total Expenses</div>
              <div className="num">PKR {fmtNum(expAmount)}</div>
              <div className="delta down">Approved expenses</div>
            </div>
          </div>

          <div className="grid g2" style={{ alignItems: 'start', marginBottom: 20 }}>
            {/* FINANCIAL ACCOUNTS */}
            <div className="panel">
              <div className="section-head" style={{ marginBottom: 12 }}>
                <h2>Financial Accounts</h2>
                <span className="badge gray">Balance as of selected date</span>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ background: '#F9F8F6', padding: 14, borderRadius: 8, border: '1px solid var(--line)' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--teal)' }}>Distributor Commission</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Commission (Selected Date)</span>
                    <span>PKR {fmtNum(metrics.distributorCommission.allocation)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Distributor Expenses (Selected Date)</span>
                    <span style={{ color: 'var(--red)' }}>− PKR {fmtNum(metrics.distributorCommission.expenses)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13.5, fontWeight: 600, borderTop: '1px solid var(--line)', paddingTop: 8 }}>
                    <span>Balance</span>
                    <span>PKR {fmtNum(metrics.distributorCommission.balance)}</span>
                  </div>
                </div>

                <div style={{ background: '#F9F8F6', padding: 14, borderRadius: 8, border: '1px solid var(--line)' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--teal)' }}>Advertisement Account Balance</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Opening Balance</span>
                    <span>PKR {fmtNum(metrics.advertisement.opening)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Sales Allocation</span>
                    <span style={{ color: 'var(--green)' }}>+ PKR {fmtNum(metrics.advertisement.allocation)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Company Expenses</span>
                    <span style={{ color: 'var(--red)' }}>− PKR {fmtNum(expComp)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Office Expenses</span>
                    <span style={{ color: 'var(--red)' }}>− PKR {fmtNum(expOff)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13.5, fontWeight: 600, borderTop: '1px solid var(--line)', paddingTop: 8 }}>
                    <span>Current Balance</span>
                    <span>PKR {fmtNum(metrics.advertisement.balance)}</span>
                  </div>
                </div>

                <div style={{ background: '#F9F8F6', padding: 14, borderRadius: 8, border: '1px solid var(--line)' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--teal)' }}>Welfare Account Balance</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Opening Balance</span>
                    <span>PKR {fmtNum(metrics.welfare.opening)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Sales Allocation</span>
                    <span style={{ color: 'var(--green)' }}>+ PKR {fmtNum(metrics.welfare.allocation)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Others Expenses</span>
                    <span style={{ color: 'var(--red)' }}>− PKR {fmtNum(expOth)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13.5, fontWeight: 600, borderTop: '1px solid var(--line)', paddingTop: 8 }}>
                    <span>Current Balance</span>
                    <span>PKR {fmtNum(metrics.welfare.balance)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* EXPENSE BREAKDOWN */}
              <div className="panel">
                <div className="section-head" style={{ marginBottom: 12 }}>
                  <h2>Expense Breakdown</h2>
                  <span className="badge gray">Activity for selected date</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--teal)' }}></div>
                      <span>Distributor</span>
                    </div>
                    <div><span style={{ fontWeight: 600, marginRight: 10 }}>PKR {fmtNum(expDist)}</span> <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>{expPct(expDist)}%</span></div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)' }}></div>
                      <span>Company</span>
                    </div>
                    <div><span style={{ fontWeight: 600, marginRight: 10 }}>PKR {fmtNum(expComp)}</span> <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>{expPct(expComp)}%</span></div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--amber)' }}></div>
                      <span>Office</span>
                    </div>
                    <div><span style={{ fontWeight: 600, marginRight: 10 }}>PKR {fmtNum(expOff)}</span> <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>{expPct(expOff)}%</span></div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--red)' }}></div>
                      <span>Others</span>
                    </div>
                    <div><span style={{ fontWeight: 600, marginRight: 10 }}>PKR {fmtNum(expOth)}</span> <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>{expPct(expOth)}%</span></div>
                  </div>
                </div>
              </div>

              {/* RETURNS */}
              <div className="panel">
                <div className="section-head" style={{ marginBottom: 12 }}>
                  <h2>Returns</h2>
                  <span className="badge gray">Activity for selected date</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span>Distributor Return Stock</span>
                    <span style={{ fontWeight: 600 }}>{fmtNum(goodReturnQty)} pkts</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span>Damage Return Stock</span>
                    <span style={{ fontWeight: 600, color: 'var(--red)' }}>{fmtNum(dmgReturnQty)} pkts</span>
                  </div>
                </div>
              </div>

              {/* STOCK POSITION */}
              <div className="panel">
                <div className="section-head" style={{ marginBottom: 12 }}>
                  <h2>Stock Position</h2>
                  <span className="badge gray">Stock as of selected date</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span>Company Saleable Stock</span>
                    <span style={{ fontWeight: 600, color: 'var(--teal)' }}>{fmtNum(metrics.stock.sellable)} pkts</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span>Company Damaged Stock</span>
                    <span style={{ fontWeight: 600, color: 'var(--red)' }}>{fmtNum(metrics.stock.damaged)} pkts</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* TABLES */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            
            {/* BOOKINGS TABLE */}
            <div className="panel" style={{ overflowX: 'auto' }}>
              <div className="section-head" style={{ marginBottom: 16 }}>
                <h2>Booking Report</h2>
                <div className="search-box no-print">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
                  <input type="text" placeholder="Search bookings..." value={bookingSearch} onChange={e => setBookingSearch(e.target.value)} style={{ border: 'none', background: 'transparent', outline: 'none', width: 140 }} />
                </div>
              </div>
              <table style={{ minWidth: 600 }}>
                <thead><tr><th>Date</th><th>Reference</th><th>Distributor</th><th className="num-cell">Packets</th><th className="num-cell">Amount</th><th>Status</th></tr></thead>
                <tbody>
                  {filteredBookings.length === 0 ? (
                    <tr><td colSpan="10" style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>No bookings found for this date.</td></tr>
                  ) : (
                    filteredBookings.map(b => (
                      <tr key={b.id}>
                        <td>{fmtDateTime(b.sale_date)}</td>
                        <td style={{ fontFamily: 'monospace' }}>{b.reference_number}</td>
                        <td>{b.distributors ? `${b.distributors.code} - ${b.distributors.name}` : '—'}</td>
                        <td className="num-cell" style={{ fontWeight: 600 }}>{fmtNum(b.packets)}</td>
                        <td className="num-cell">PKR {fmtNum(b.total_amount)}</td>
                        <td><span className="badge amber">{b.status}</span></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* RECOVERIES TABLE */}
            <div className="panel" style={{ overflowX: 'auto' }}>
              <div className="section-head" style={{ marginBottom: 16 }}>
                <h2>Recovery Report</h2>
                <div className="search-box no-print">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
                  <input type="text" placeholder="Search recoveries..." value={recoverySearch} onChange={e => setRecoverySearch(e.target.value)} style={{ border: 'none', background: 'transparent', outline: 'none', width: 140 }} />
                </div>
              </div>
              <table style={{ minWidth: 700 }}>
                <thead><tr><th>Date</th><th>Reference</th><th>Distributor</th><th className="num-cell">Amount</th><th>Account Detail</th><th>TID</th><th>Notes</th><th>Status</th></tr></thead>
                <tbody>
                  {filteredRecoveries.length === 0 ? (
                    <tr><td colSpan="10" style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>No recoveries found for this date.</td></tr>
                  ) : (
                    filteredRecoveries.map((r, i) => (
                      <tr key={i}>
                        <td>{fmtDateTime(r.recovery_date)}</td>
                        <td style={{ fontFamily: 'monospace' }}>{r.reference_number || '—'}</td>
                        <td>{r.distributors ? `${r.distributors.code} - ${r.distributors.name}` : '—'}</td>
                        <td className="num-cell" style={{ fontWeight: 600 }}>PKR {fmtNum(r.amount)}</td>
                        <td>{r.account_detail || '—'}</td>
                        <td>{r.tid || '—'}</td>
                        <td>{r.notes || '—'}</td>
                        <td><span className="badge green">{r.status || 'Approved'}</span></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* EXPENSES TABLE */}
            <div className="panel" style={{ overflowX: 'auto' }}>
              <div className="section-head" style={{ marginBottom: 16 }}>
                <h2>Expense Report</h2>
                <div className="search-box no-print">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
                  <input type="text" placeholder="Search expenses..." value={expenseSearch} onChange={e => setExpenseSearch(e.target.value)} style={{ border: 'none', background: 'transparent', outline: 'none', width: 140 }} />
                </div>
              </div>
              <table style={{ minWidth: 800 }}>
                <thead><tr><th>Date</th><th>Reference</th><th>Type</th><th>Distributor</th><th>Head</th><th className="num-cell">Amount</th><th>Account Detail</th><th>TID</th><th>Notes</th><th>Status</th></tr></thead>
                <tbody>
                  {filteredExpenses.length === 0 ? (
                    <tr><td colSpan="10" style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>No expenses found for this date.</td></tr>
                  ) : (
                    filteredExpenses.map((e, i) => (
                      <tr key={i}>
                        <td>{fmtDateTime(e.expense_date)}</td>
                        <td style={{ fontFamily: 'monospace' }}>{e.reference_number || '—'}</td>
                        <td>{e.category}</td>
                        <td>{e.category === 'Distributor' && e.distributors ? `${e.distributors.code} - ${e.distributors.name}` : '—'}</td>
                        <td>{e.head || '—'}</td>
                        <td className="num-cell" style={{ fontWeight: 600 }}>PKR {fmtNum(e.amount)}</td>
                        <td>{e.account_detail || '—'}</td>
                        <td>{e.tid || '—'}</td>
                        <td>{e.description || '—'}</td>
                        <td><span className="badge green">{e.status || 'Approved'}</span></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* RETURNS TABLE */}
            <div className="panel" style={{ overflowX: 'auto' }}>
              <div className="section-head" style={{ marginBottom: 16 }}>
                <h2>Return Report</h2>
                <div className="search-box no-print">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
                  <input type="text" placeholder="Search returns..." value={returnSearch} onChange={e => setReturnSearch(e.target.value)} style={{ border: 'none', background: 'transparent', outline: 'none', width: 140 }} />
                </div>
              </div>
              <table style={{ minWidth: 700 }}>
                <thead><tr><th>Date</th><th>Reference</th><th>Distributor</th><th>Return Type</th><th className="num-cell">Quantity</th><th>Notes</th><th>Status</th></tr></thead>
                <tbody>
                  {filteredReturns.length === 0 ? (
                    <tr><td colSpan="7" style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>No returns found for this date.</td></tr>
                  ) : (
                    filteredReturns.map((r, i) => (
                      <tr key={i}>
                        <td>{fmtDateTime(r.transaction_date)}</td>
                        <td style={{ fontFamily: 'monospace' }}>{r.reference_number}</td>
                        <td>{r.distributors ? `${r.distributors.code} - ${r.distributors.name}` : '—'}</td>
                        <td>{r.transaction_type === 'Salesman_Good_Return' ? 'Good Return' : r.transaction_type === 'Salesman_Damaged_Return' ? 'Damaged Return' : r.transaction_type}</td>
                        <td className="num-cell" style={{ fontWeight: 600 }}>{fmtNum(r.quantity)}</td>
                        <td>{r.notes || '—'}</td>
                        <td><span className="badge green">{r.status || 'Approved'}</span></td>
                        <td><span className="badge green">{r.status}</span></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

          </div>
        </>
      )}
    </div>
  );
}

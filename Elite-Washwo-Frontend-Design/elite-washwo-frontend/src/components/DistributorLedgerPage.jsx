import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchDistributors,
  fetchDistributorOutstanding,
  fetchDistributorTodayRecovery,
  fetchDistributorStockStats,
  fetchDistributorStockLedger,
  fetchDistributorFinLedger,
  fetchDistributorCommissionLedger,
  addDistributorRecovery
} from '../lib/db';

const fmtNum = (n) => Number(n || 0).toLocaleString('en-PK');
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

function statusBadge(s) {
  const map = {
    Approved: 'green',
    Posted: 'green',
    Pending: 'amber',
    Submitted: 'amber',
    Cancelled: 'gray',
    Rejected: 'red'
  };
  return <span className={`badge ${map[s] || 'gray'}`}>{s || 'Pending'}</span>;
}

export default function DistributorLedgerPage({ searchTerm = '' }) {
  const { role } = useAuth();
  const [distributors, setDistributors] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [loadingDist, setLoadingDist] = useState(true);
  const [loadingData, setLoadingData] = useState(false);

  // Active Tab: finLedger, stockLedger, commLedger, statement
  const [activeTab, setActiveTab] = useState('finLedger');

  // Stats & Ledger state
  const [stats, setStats] = useState({
    stock: 0,
    issued: 0,
    goodReturns: 0,
    damagedReturns: 0,
    pendingReturns: 0,
    totalSales: 0,
    totalRecoveries: 0,
    totalPackets: 0,
    netBalance: 0,
    outstanding: 0,
    advanceBalance: 0,
    accruedCommission: 0,
    settledCommission: 0,
    commissionPayable: 0,
    todayRecovery: 0
  });

  const [finLedger, setFinLedger] = useState([]);
  const [stockLedger, setStockLedger] = useState([]);
  const [commLedger, setCommLedger] = useState([]);

  // Direct Recovery recording state
  const [showRecModal, setShowRecModal] = useState(false);
  const [recAmount, setRecAmount] = useState('');
  const [recMethod, setRecMethod] = useState('Cash');
  const [recNotes, setRecNotes] = useState('');
  const [recDate, setRecDate] = useState(new Date().toISOString().split('T')[0]);
  const [recSaving, setRecSaving] = useState(false);
  const [recMsg, setRecMsg] = useState('');

  // Filters & Pagination
  const [localSearch, setLocalSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [distSearch, setDistSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Load distributors list
  const loadDistributorsList = useCallback(async () => {
    setLoadingDist(true);
    try {
      const data = await fetchDistributors();
      const list = data || [];
      setDistributors(list);
      if (list.length > 0 && !selectedId) {
        setSelectedId(list[0].id);
      }
    } catch (err) {
      console.error('Error loading distributors:', err);
    } finally {
      setLoadingDist(false);
    }
  }, [selectedId]);

  useEffect(() => {
    loadDistributorsList();
  }, [loadDistributorsList]);

  // Load distributor-specific data
  const loadDistributorData = useCallback(async (distId) => {
    if (!distId) return;
    setLoadingData(true);
    try {
      const [outRes, recRes, stockStatsRes, finRes, stockRes, commRes] = await Promise.all([
        fetchDistributorOutstanding(distId),
        fetchDistributorTodayRecovery(distId),
        fetchDistributorStockStats(distId),
        fetchDistributorFinLedger(distId),
        fetchDistributorStockLedger(distId),
        fetchDistributorCommissionLedger(distId)
      ]);

      setStats({
        ...outRes,
        ...stockStatsRes,
        todayRecovery: recRes || 0
      });

      setFinLedger(finRes || []);
      setStockLedger(stockRes || []);
      setCommLedger(commRes || []);
    } catch (err) {
      console.error('Error loading distributor data:', err);
    } finally {
      setLoadingData(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId) {
      loadDistributorData(selectedId);
      setPage(1);
    }
  }, [selectedId, loadDistributorData]);

  // Reset page on tab or filter change
  useEffect(() => {
    setPage(1);
  }, [activeTab, statusFilter, localSearch, searchTerm]);

  // Selected distributor entity
  const selectedDist = useMemo(() => {
    return distributors.find(d => d.id === selectedId) || null;
  }, [distributors, selectedId]);

  // Filtered distributors for selector
  const filteredDistributors = useMemo(() => {
    const q = (distSearch || '').trim().toLowerCase();
    if (!q) return distributors;
    return distributors.filter(d =>
      (d.name || '').toLowerCase().includes(q) ||
      (d.code || '').toLowerCase().includes(q) ||
      (d.phone || '').toLowerCase().includes(q)
    );
  }, [distributors, distSearch]);

  const query = (localSearch || searchTerm).trim().toLowerCase();

  // Filtered Financial Ledger entries
  const filteredFin = useMemo(() => {
    return finLedger.filter(r => {
      if (statusFilter !== 'All' && r.status !== statusFilter) return false;
      if (!query) return true;
      return (
        (r.ref || '').toLowerCase().includes(query) ||
        (r.type || '').toLowerCase().includes(query) ||
        (r.description || '').toLowerCase().includes(query) ||
        fmtDate(r.date).toLowerCase().includes(query)
      );
    });
  }, [finLedger, statusFilter, query]);

  // Filtered Stock Ledger entries
  const filteredStock = useMemo(() => {
    return stockLedger.filter(r => {
      if (statusFilter !== 'All' && r.status !== statusFilter) return false;
      if (!query) return true;
      const pkgName = r.product_packaging?.name || '';
      const prodName = r.product_packaging?.products?.name || '';
      return (
        (r.reference_number || '').toLowerCase().includes(query) ||
        (r.transaction_type || '').toLowerCase().includes(query) ||
        pkgName.toLowerCase().includes(query) ||
        prodName.toLowerCase().includes(query) ||
        fmtDate(r.transaction_date).toLowerCase().includes(query)
      );
    });
  }, [stockLedger, statusFilter, query]);

  // Filtered Commission Ledger entries
  const filteredComm = useMemo(() => {
    return commLedger.filter(r => {
      if (statusFilter !== 'All' && r.status !== statusFilter) return false;
      if (!query) return true;
      return (
        (r.ref || '').toLowerCase().includes(query) ||
        (r.type || '').toLowerCase().includes(query) ||
        (r.notes || '').toLowerCase().includes(query) ||
        fmtDate(r.date).toLowerCase().includes(query)
      );
    });
  }, [commLedger, statusFilter, query]);

  // Pagination slicing
  const paginatedFin = filteredFin.slice((page - 1) * pageSize, page * pageSize);
  const paginatedStock = filteredStock.slice((page - 1) * pageSize, page * pageSize);
  const paginatedComm = filteredComm.slice((page - 1) * pageSize, page * pageSize);

  const totalPages = Math.ceil(
    (activeTab === 'finLedger' ? filteredFin.length : activeTab === 'stockLedger' ? filteredStock.length : filteredComm.length) / pageSize
  ) || 1;

  const isFiltered = Boolean(localSearch || statusFilter !== 'All');
  const resetFilters = () => {
    setLocalSearch('');
    setStatusFilter('All');
    setPage(1);
  };

  const handlePrintStatement = () => {
    window.print();
  };

  const handleSaveRecovery = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!selectedId) return;
    const amt = Number(recAmount);
    if (!amt || amt <= 0) {
      setRecMsg('err:Enter a valid recovery amount.');
      return;
    }
    setRecSaving(true);
    setRecMsg('');
    try {
      await addDistributorRecovery({
        distributorId: selectedId,
        amount: amt,
        paymentMethod: recMethod,
        recoveryDate: recDate,
        notes: recNotes
      });
      setRecMsg('ok:Recovery recorded successfully.');
      await loadDistributorData(selectedId);
      setTimeout(() => {
        setShowRecModal(false);
        setRecMsg('');
      }, 1200);
    } catch (err) {
      setRecMsg('err:' + (err.message || 'Failed to record recovery.'));
    } finally {
      setRecSaving(false);
    }
  };

  if (loadingDist) {
    return (
      <div className="panel" style={{ textAlign: 'center', padding: 40, color: 'var(--text-dim)' }}>
        Loading distributors...
      </div>
    );
  }

  return (
    <>
      {/* ── DISTRIBUTOR SELECTION & PROFILE BAR ── */}
      <div className="panel no-print" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          {/* Left: Selected Distributor Meta */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div className="avatar" style={{ width: 54, height: 54, fontSize: 18, background: 'var(--teal)', color: '#fff', fontWeight: 700 }}>
              {selectedDist?.name ? selectedDist.name.substring(0, 2).toUpperCase() : 'DST'}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 17, fontWeight: 700, color: 'var(--ink)' }}>
                  {selectedDist?.name || 'Select Distributor'}
                </span>
                <span className="badge gray" style={{ fontSize: 11 }}>
                  #{selectedDist?.code || '—'}
                </span>
                {selectedDist?.is_active ? (
                  <span className="badge green">Active</span>
                ) : (
                  <span className="badge gray">Inactive</span>
                )}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 3 }}>
                Phone: <strong style={{ color: 'var(--ink)' }}>{selectedDist?.phone || '—'}</strong>
                {selectedDist?.cnic ? ` · CNIC: ${selectedDist.cnic}` : ''}
                {selectedDist?.commission !== undefined ? ` · Commission: Rs. ${selectedDist.commission}/pkt` : ''}
              </div>
            </div>
          </div>

          {/* Right: Quick Search + Distributor Chips / Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="Search distributor..."
              value={distSearch}
              onChange={e => setDistSearch(e.target.value)}
              style={{
                padding: '6px 12px',
                fontSize: 12,
                border: '1px solid var(--line)',
                borderRadius: 6,
                background: 'var(--panel)',
                color: 'var(--text)',
                width: 170
              }}
            />
            <div className="chip-list" style={{ maxWidth: 420, overflowX: 'auto', paddingBottom: 2 }}>
              {filteredDistributors.map(d => (
                <div
                  key={d.id}
                  className={`chip${d.id === selectedId ? ' active' : ''}`}
                  onClick={() => setSelectedId(d.id)}
                  style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}
                  title={`${d.name} (${d.code})`}
                >
                  {d.name || d.code}
                </div>
              ))}
              {filteredDistributors.length === 0 && (
                <span style={{ fontSize: 12, color: 'var(--text-dim)', padding: '4px 8px' }}>No matches</span>
              )}
            </div>
            <button
              className="btn primary"
              style={{ fontSize: 12, padding: '6px 12px', whiteSpace: 'nowrap' }}
              onClick={() => {
                setRecAmount('');
                setRecMethod('Cash');
                setRecNotes('');
                setRecDate(new Date().toISOString().split('T')[0]);
                setRecMsg('');
                setShowRecModal(true);
              }}
              disabled={!selectedId}
            >
              + Record Recovery
            </button>
          </div>
        </div>
      </div>

      {/* ── KPI METRIC CARDS ── */}
      <div className="grid g4" style={{ marginBottom: 20 }}>
        {/* Tile 1: Stock */}
        <div className="tile teal">
          <div className="bar" />
          <div className="label">Distributor Physical Stock</div>
          <div className="num">{fmtNum(stats.stock)} pkts</div>
          <div className="delta" style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
            {stats.issued > 0 
              ? `${fmtNum(stats.issued)} issued · ${fmtNum(stats.goodReturns + stats.damagedReturns)} returned`
              : `0 warehouse issues · ${fmtNum(stats.totalPackets)} commercial pkts sold`
            }
          </div>
        </div>

        {/* Tile 2: Approved Sales */}
        <div className="tile green">
          <div className="bar" />
          <div className="label">Total Approved Sales</div>
          <div className="num">Rs. {fmtNum(stats.totalSales)}</div>
          <div className="delta up" style={{ fontSize: 11 }}>
            {fmtNum(stats.totalPackets)} packets delivered (SAL-)
          </div>
          {stats.pendingBookingsCount > 0 && (
            <div style={{ fontSize: 10.5, color: 'var(--amber)', marginTop: 3 }}>
              Pending bookings: {stats.pendingBookingsCount} ({fmtNum(stats.pendingBookingsPackets)} pkts · Rs. {fmtNum(stats.pendingBookingsAmount)}) excluded
            </div>
          )}
        </div>

        {/* Tile 3: Total Recoveries */}
        <div className="tile amber">
          <div className="bar" />
          <div className="label">Total Recoveries</div>
          <div className="num">Rs. {fmtNum(stats.totalRecoveries)}</div>
          <div className="delta" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
            Today: Rs. {fmtNum(stats.todayRecovery)}
            {stats.totalSettlementAdjustments > 0 && ` · Incl. Rs. ${fmtNum(stats.totalSettlementAdjustments)} commission adjusted`}
          </div>
        </div>

        {/* Tile 4: Outstanding Balance or Advance Credit Held */}
        <div className={`tile ${stats.advanceBalance > 0 ? 'teal' : stats.outstanding > 0 ? 'red' : 'green'}`}>
          <div className="bar" />
          <div className="label">{stats.advanceBalance > 0 ? 'Advance Credit Held' : 'Outstanding Balance'}</div>
          <div className="num" style={{ color: stats.advanceBalance > 0 ? 'var(--teal)' : stats.outstanding > 0 ? 'var(--red)' : 'var(--green)' }}>
            Rs. {fmtNum(stats.advanceBalance > 0 ? stats.advanceBalance : stats.outstanding)}
          </div>
          <div className="delta" style={{ fontSize: 11, color: stats.advanceBalance > 0 ? 'var(--teal)' : stats.outstanding > 0 ? 'var(--red)' : 'var(--green)' }}>
            {stats.advanceBalance > 0 
              ? 'Distributor in Credit (Prepaid/Advance)' 
              : stats.outstanding > 0 
                ? 'Approved Sales − Recoveries' 
                : 'Fully settled'}
          </div>
        </div>
      </div>

      {/* Commission Strip Banner */}
      <div className="panel" style={{ marginBottom: 20, padding: '12px 18px', background: 'rgba(14,124,134,0.04)', borderColor: 'rgba(14,124,134,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <strong style={{ fontSize: 13, color: 'var(--ink)' }}>Distributor Commission Position</strong>
                {stats.hasUnreconciledRates && (
                  <span className="badge amber" style={{ fontSize: 10.5 }} title="Historical sales orders in database lack commission_rate_snapshot values">
                    Snapshot Missing in DB ({stats.unreconciledPackets} pkts)
                  </span>
                )}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 2 }}>
                Verified Snapshot Accrued: <strong style={{ color: 'var(--ink)' }}>Rs. {fmtNum(stats.accruedCommission)}</strong>
                {' · '}Settled/Paid: <strong style={{ color: 'var(--green)' }}>Rs. {fmtNum(stats.settledCommission)}</strong>
                {stats.hasUnreconciledRates && (
                  <span style={{ color: 'var(--text-dim)', marginLeft: 6 }}>
                    · Registered rate: Rs. {selectedDist?.commission || 0}/pkt (Requires DB snapshot reconciliation)
                  </span>
                )}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Commission Payable</span>
              <div style={{ fontSize: 18, fontWeight: 700, color: stats.commissionPayable > 0 ? 'var(--teal)' : 'var(--text-dim)' }}>
                Rs. {fmtNum(stats.commissionPayable)}
              </div>
            </div>
            <button
              className="btn no-print"
              onClick={handlePrintStatement}
              style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="6 9 6 2 18 2 18 9" />
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
                <rect x="6" y="14" width="12" height="8" />
              </svg>
              Print Statement
            </button>
          </div>
        </div>
      </div>

      {/* ── LEDGER TABS & TABLE PANEL ── */}
      <div className="panel">
        {/* Tab Selector & Filter Bar */}
        <div
          className="no-print"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 12,
            borderBottom: '1px solid var(--line)',
            paddingBottom: 12,
            marginBottom: 16
          }}
        >
          {/* Tabs */}
          <div className="tabs" style={{ margin: 0, border: 0 }}>
            {[
              ['finLedger', 'Financial Ledger'],
              ['stockLedger', 'Stock Ledger'],
              ['commLedger', 'Commission Ledger'],
              ['statement', 'Account Statement']
            ].map(([k, label]) => (
              <div
                key={k}
                className={`tab${activeTab === k ? ' active' : ''}`}
                onClick={() => setActiveTab(k)}
              >
                {label}
              </div>
            ))}
          </div>

          {/* Search & Status Filters */}
          {activeTab !== 'statement' && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="text"
                placeholder="Filter by ref, type, date..."
                value={localSearch}
                onChange={e => setLocalSearch(e.target.value)}
                style={{
                  padding: '5px 10px',
                  fontSize: 12,
                  border: '1px solid var(--line)',
                  borderRadius: 6,
                  background: 'var(--panel)',
                  color: 'var(--text)',
                  width: 200
                }}
              />
              <div className="chip-list" style={{ gap: 4 }}>
                {['All', 'Approved', 'Pending'].map(st => (
                  <div
                    key={st}
                    className={`chip${statusFilter === st ? ' active' : ''}`}
                    onClick={() => setStatusFilter(st)}
                    style={{ padding: '4px 10px', fontSize: 11 }}
                  >
                    {st}
                  </div>
                ))}
              </div>
              {isFiltered && (
                <span className="link" onClick={resetFilters} style={{ color: 'var(--red)', fontSize: 12, cursor: 'pointer' }}>
                  Reset
                </span>
              )}
            </div>
          )}
        </div>

        {/* Loading Indicator */}
        {loadingData ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-dim)', fontSize: 13 }}>
            Loading ledger records...
          </div>
        ) : (
          <>
            {/* ── TAB 1: FINANCIAL LEDGER ── */}
            {activeTab === 'finLedger' && (
              <div>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Type</th>
                      <th>Reference</th>
                      <th>Description</th>
                      <th style={{ textAlign: 'right' }}>Debit (Sales)</th>
                      <th style={{ textAlign: 'right' }}>Credit (Recovery)</th>
                      <th style={{ textAlign: 'right' }}>Running Balance</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedFin.length === 0 ? (
                      <tr>
                        <td colSpan={8} style={{ textAlign: 'center', padding: 30, color: 'var(--text-dim)' }}>
                          {isFiltered || query ? 'No matching financial transactions found.' : 'No financial transactions recorded for this distributor.'}
                        </td>
                      </tr>
                    ) : (
                      paginatedFin.map(r => (
                        <tr key={r.id || r.ref} style={{ background: r.isBooking ? 'rgba(224,147,46,0.02)' : 'transparent' }}>
                          <td>{fmtDate(r.date)}</td>
                          <td>
                            <strong>{r.type}</strong>
                            {r.isBooking && (
                              <span className="badge amber" style={{ marginLeft: 6, fontSize: 10 }}>Demand Note</span>
                            )}
                          </td>
                          <td style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'monospace' }}>
                            {r.ref || '—'}
                          </td>
                          <td style={{ fontSize: 12 }}>{r.description}</td>
                          <td className="num-cell" style={{ textAlign: 'right', fontWeight: (!r.isBooking && r.debit) ? 600 : 400 }}>
                            {!r.isBooking && r.debit ? `Rs. ${fmtNum(r.debit)}` : '—'}
                          </td>
                          <td className="num-cell" style={{ textAlign: 'right', color: (!r.isBooking && r.credit) ? 'var(--green)' : 'inherit', fontWeight: (!r.isBooking && r.credit) ? 600 : 400 }}>
                            {!r.isBooking && r.credit ? `Rs. ${fmtNum(r.credit)}` : '—'}
                          </td>
                          <td
                            className="num-cell"
                            style={{
                              textAlign: 'right',
                              fontWeight: r.isPosted ? 700 : 400,
                              color: r.isPosted 
                                ? (r.balance > 0 ? 'var(--red)' : r.balance < 0 ? 'var(--green)' : 'var(--ink)')
                                : 'var(--text-dim)'
                            }}
                          >
                            {r.isPosted && r.balance !== null && r.balance !== undefined ? (
                              `Rs. ${fmtNum(Math.abs(r.balance))} ${r.balance > 0 ? 'Dr' : r.balance < 0 ? 'Cr' : ''}`
                            ) : (
                              <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>—</span>
                            )}
                          </td>
                          <td>{statusBadge(r.status)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>

                {/* Pagination */}
                {filteredFin.length > pageSize && (
                  <div className="no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
                    <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                      Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, filteredFin.length)} of {filteredFin.length} entries
                    </span>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn" disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))}>
                        Previous
                      </button>
                      <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── TAB 2: STOCK LEDGER ── */}
            {activeTab === 'stockLedger' && (
              <div>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Transaction Type</th>
                      <th>Reference</th>
                      <th>Product / Packaging</th>
                      <th style={{ textAlign: 'right' }}>In (Issued)</th>
                      <th style={{ textAlign: 'right' }}>Out (Returned)</th>
                      <th>Condition</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedStock.length === 0 ? (
                      <tr>
                        <td colSpan={8} style={{ textAlign: 'center', padding: 30, color: 'var(--text-dim)' }}>
                          {isFiltered || query ? 'No matching stock transactions found.' : 'No stock transactions recorded for this distributor.'}
                        </td>
                      </tr>
                    ) : (
                      paginatedStock.map(r => {
                        const isIssue = ['Distributor_Issue', 'Salesman_Issue'].includes(r.transaction_type);
                        const isReturn = ['Distributor_Good_Return', 'Distributor_Damaged_Return', 'Salesman_Good_Return', 'Salesman_Damaged_Return'].includes(r.transaction_type);
                        const isDamaged = r.transaction_type.includes('Damaged') || r.category === 'Damaged Stock';
                        return (
                          <tr key={r.id}>
                            <td>{fmtDate(r.transaction_date)}</td>
                            <td>{r.transaction_type?.replace(/_/g, ' ')}</td>
                            <td style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'monospace' }}>
                              {r.reference_number || '—'}
                            </td>
                            <td>
                              {r.product_packaging?.products?.name || 'Surf'} — {r.product_packaging?.name || 'Packet'}
                            </td>
                            <td className="num-cell" style={{ textAlign: 'right', fontWeight: isIssue ? 600 : 400 }}>
                              {isIssue ? `${fmtNum(r.quantity)} pkts` : '—'}
                            </td>
                            <td className="num-cell" style={{ textAlign: 'right', fontWeight: isReturn ? 600 : 400, color: isDamaged ? 'var(--red)' : 'inherit' }}>
                              {isReturn ? `${fmtNum(r.quantity)} pkts` : '—'}
                            </td>
                            <td>
                              {isDamaged ? (
                                <span className="badge red">Damaged</span>
                              ) : (
                                <span className="badge green">Good</span>
                              )}
                            </td>
                            <td>{statusBadge(r.status)}</td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>

                {/* Pagination */}
                {filteredStock.length > pageSize && (
                  <div className="no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
                    <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                      Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, filteredStock.length)} of {filteredStock.length} entries
                    </span>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn" disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))}>
                        Previous
                      </button>
                      <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── TAB 3: COMMISSION LEDGER ── */}
            {activeTab === 'commLedger' && (
              <div>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Type</th>
                      <th>Reference</th>
                      <th>Notes / Breakdown</th>
                      <th style={{ textAlign: 'right' }}>Packets</th>
                      <th style={{ textAlign: 'right' }}>Rate (PKR)</th>
                      <th style={{ textAlign: 'right' }}>Earned</th>
                      <th style={{ textAlign: 'right' }}>Paid</th>
                      <th style={{ textAlign: 'right' }}>Running Balance</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedComm.length === 0 ? (
                      <tr>
                        <td colSpan={10} style={{ textAlign: 'center', padding: 30, color: 'var(--text-dim)' }}>
                          {isFiltered || query ? 'No matching commission records found.' : 'No commission records found for this distributor.'}
                        </td>
                      </tr>
                    ) : (
                      paginatedComm.map(r => (
                        <tr key={r.id}>
                          <td>{fmtDate(r.date)}</td>
                          <td>
                            <strong>{r.type}</strong>
                            {r.isMissingSnapshot && (
                              <span className="badge amber" style={{ marginLeft: 6, fontSize: 10 }}>Snapshot Missing</span>
                            )}
                          </td>
                          <td style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'monospace' }}>
                            {r.ref || '—'}
                          </td>
                          <td style={{ fontSize: 12 }}>
                            {r.isMissingSnapshot ? (
                              <span style={{ color: 'var(--amber)' }}>
                                {r.notes}
                              </span>
                            ) : r.notes}
                          </td>
                          <td className="num-cell" style={{ textAlign: 'right' }}>
                            {r.packets ? fmtNum(r.packets) : '—'}
                          </td>
                          <td className="num-cell" style={{ textAlign: 'right' }}>
                            {r.isMissingSnapshot ? (
                              <span style={{ color: 'var(--amber)', fontSize: 11 }}>Missing in DB</span>
                            ) : (r.rate !== null && r.rate !== undefined ? `Rs. ${r.rate}` : '—')}
                          </td>
                          <td className="num-cell" style={{ textAlign: 'right', color: r.earned ? 'var(--teal)' : 'inherit', fontWeight: r.earned ? 600 : 400 }}>
                            {r.isMissingSnapshot ? (
                              <span style={{ color: 'var(--text-dim)' }}>—</span>
                            ) : (r.earned ? `Rs. ${fmtNum(r.earned)}` : '—')}
                          </td>
                          <td className="num-cell" style={{ textAlign: 'right', color: r.paid ? 'var(--green)' : 'inherit', fontWeight: r.paid ? 600 : 400 }}>
                            {r.paid ? `Rs. ${fmtNum(r.paid)}` : '—'}
                          </td>
                          <td className="num-cell" style={{ textAlign: 'right', fontWeight: 700, color: 'var(--teal)' }}>
                            {r.isMissingSnapshot && (!r.balance || r.balance === 0) ? (
                              <span style={{ color: 'var(--text-dim)' }}>—</span>
                            ) : (
                              `Rs. ${fmtNum(r.balance)}`
                            )}
                          </td>
                          <td>
                            {r.isMissingSnapshot ? (
                              <span className="badge amber">Unreconciled</span>
                            ) : statusBadge(r.status)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>

                {/* Pagination */}
                {filteredComm.length > pageSize && (
                  <div className="no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
                    <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                      Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, filteredComm.length)} of {filteredComm.length} entries
                    </span>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn" disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))}>
                        Previous
                      </button>
                      <button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── TAB 4: ACCOUNT STATEMENT (PRINTABLE) ── */}
            {activeTab === 'statement' && (
              <div style={{ padding: '16px 8px' }}>
                <div style={{ border: '1px solid var(--line)', borderRadius: 8, padding: 24, background: '#fff' }}>
                  {/* Statement Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '2px solid var(--ink)', paddingBottom: 16, marginBottom: 20 }}>
                    <div>
                      <h2 style={{ margin: '0 0 4px', fontSize: 20, fontFamily: "'Space Grotesk', sans-serif" }}>
                        ELITE WASH DETERGENT
                      </h2>
                      <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                        Distributor Account &amp; Financial Ledger Statement
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 14, fontWeight: 700 }}>
                        {selectedDist?.name} (#{selectedDist?.code})
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                        Phone: {selectedDist?.phone || '—'} · Date: {fmtDate(new Date())}
                      </div>
                    </div>
                  </div>

                  {/* Summary Balance Table */}
                  <div className="grid g3" style={{ marginBottom: 24 }}>
                    <div className="panel-flat" style={{ border: '1px solid var(--line)', borderRadius: 6, padding: 14 }}>
                      <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 600 }}>
                        Gross Approved Sales
                      </div>
                      <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4 }}>
                        Rs. {fmtNum(stats.totalSales)}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                        {fmtNum(stats.totalPackets)} Packets Delivered
                      </div>
                    </div>

                    <div className="panel-flat" style={{ border: '1px solid var(--line)', borderRadius: 6, padding: 14 }}>
                      <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 600 }}>
                        Total Recoveries Received
                      </div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--green)', marginTop: 4 }}>
                        Rs. {fmtNum(stats.totalRecoveries)}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                        {stats.advanceBalance > 0 ? 'Includes booking advances' : 'Direct & linked recoveries'}
                      </div>
                    </div>

                    <div className="panel-flat" style={{ border: '1px solid var(--line)', borderRadius: 6, padding: 14 }}>
                      <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 600 }}>
                        {stats.advanceBalance > 0 ? 'Advance Credit Held' : 'Net Outstanding Balance'}
                      </div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: stats.advanceBalance > 0 ? 'var(--teal)' : stats.outstanding > 0 ? 'var(--red)' : 'var(--green)', marginTop: 4 }}>
                        Rs. {fmtNum(stats.advanceBalance > 0 ? stats.advanceBalance : stats.outstanding)} {stats.advanceBalance > 0 ? '(Cr)' : stats.outstanding > 0 ? '(Dr)' : ''}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                        {stats.advanceBalance > 0 ? 'Prepaid / Advance deposit balance' : stats.outstanding > 0 ? 'Payable by Distributor' : 'Fully Cleared'}
                      </div>
                    </div>
                  </div>

                  {/* Stock Position Summary */}
                  <div style={{ marginBottom: 20 }}>
                    <h3 style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)', marginBottom: 8 }}>
                      Stock Reconciliation Summary
                    </h3>
                    <table style={{ width: '100%' }}>
                      <tbody>
                        <tr>
                          <td>Physical Warehouse Stock Issued to Distributor:</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtNum(stats.issued)} pkts</td>
                        </tr>
                        <tr>
                          <td>Commercial Sales Invoiced / Delivered:</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtNum(stats.totalPackets)} pkts</td>
                        </tr>
                        <tr>
                          <td>Good Condition Packets Returned:</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>− {fmtNum(stats.goodReturns)} pkts</td>
                        </tr>
                        <tr>
                          <td>Damaged Condition Packets Returned:</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>− {fmtNum(stats.damagedReturns)} pkts</td>
                        </tr>
                        <tr style={{ borderTop: '1px solid var(--line)', fontWeight: 700 }}>
                          <td>Distributor Warehouse Stock Balance:</td>
                          <td style={{ textAlign: 'right', color: 'var(--teal)' }}>{fmtNum(stats.stock)} pkts</td>
                        </tr>
                      </tbody>
                    </table>
                    {stats.issued === 0 && stats.totalPackets > 0 && (
                      <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 6, fontStyle: 'italic' }}>
                        * Note: Commercial sales ({fmtNum(stats.totalPackets)} pkts) were invoiced directly. No physical warehouse dispatch movements (Distributor_Issue) have been recorded in inventory transactions.
                      </div>
                    )}
                  </div>

                  {/* Commission Summary */}
                  <div style={{ marginBottom: 24 }}>
                    <h3 style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)', marginBottom: 8 }}>
                      Commission Position
                    </h3>
                    <table style={{ width: '100%' }}>
                      <tbody>
                        <tr>
                          <td>Verified Snapshot Accrued Commission:</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>Rs. {fmtNum(stats.accruedCommission)}</td>
                        </tr>
                        {stats.hasUnreconciledRates && (
                          <tr style={{ color: 'var(--amber)' }}>
                            <td>
                              Unreconciled Historical Sales ({stats.unreconciledPackets} pkts):
                              <span style={{ fontSize: 11, display: 'block', color: 'var(--text-dim)' }}>
                                Rate snapshot missing in DB. Registered rate: Rs. {selectedDist?.commission || 0}/pkt (Est. Rs. {fmtNum(stats.estimatedUnreconciledCommission)} pending DB snapshot reconciliation)
                              </span>
                            </td>
                            <td style={{ textAlign: 'right', fontWeight: 600 }}>Snapshot Missing</td>
                          </tr>
                        )}
                        <tr>
                          <td>Commission Paid Out (Settlements):</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>− Rs. {fmtNum(stats.settledCommission)}</td>
                        </tr>
                        <tr style={{ borderTop: '1px solid var(--line)', fontWeight: 700 }}>
                          <td>Net Verified Commission Payable:</td>
                          <td style={{ textAlign: 'right', color: 'var(--green)' }}>Rs. {fmtNum(stats.commissionPayable)}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* Statement Footer */}
                  <div style={{ borderTop: '1px dashed var(--line)', paddingTop: 16, marginTop: 24, display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-dim)' }}>
                    <div>All calculations derived directly from verified transactions. No manual overwrites permitted.</div>
                    <div>Elite Wash ERP · Official Ledger Statement</div>
                  </div>
                </div>

                <div className="btn-row no-print" style={{ marginTop: 16, justifyContent: 'center' }}>
                  <button className="btn primary" onClick={handlePrintStatement} style={{ padding: '8px 24px', fontSize: 13 }}>
                    Print Official Statement
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* ── DIRECT RECOVERY MODAL ────────────────────────────────────────── */}
      {showRecModal && selectedDist && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="panel" style={{ width: 440, maxWidth: '92%', padding: 24, boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, borderBottom: '1px solid var(--line)', paddingBottom: 10 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 16 }}>Record Recovery — {selectedDist.name}</h3>
                <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                  Distributor Code: #{selectedDist.code} · Current Outstanding: Rs. {fmtNum(stats.outstanding)} {stats.advanceBalance > 0 ? `(Advance Held: Rs. ${fmtNum(stats.advanceBalance)})` : ''}
                </div>
              </div>
              <button className="btn ghost" style={{ padding: '4px 8px' }} onClick={() => setShowRecModal(false)}>✕</button>
            </div>

            {recMsg && (
              <div style={{
                padding: '8px 12px',
                marginBottom: 12,
                borderRadius: 4,
                fontSize: 12,
                background: recMsg.startsWith('err:') ? 'var(--red-soft)' : 'var(--green-soft)',
                color: recMsg.startsWith('err:') ? 'var(--red)' : 'var(--green)'
              }}>
                {recMsg.replace(/^(ok|err):/, '')}
              </div>
            )}

            <form onSubmit={handleSaveRecovery} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="field">
                <label>Recovery Date *</label>
                <input
                  type="date"
                  value={recDate}
                  onChange={e => setRecDate(e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label>Amount (Rs.) *</label>
                <input
                  type="number"
                  min="1"
                  step="any"
                  placeholder="e.g. 50000"
                  value={recAmount}
                  onChange={e => setRecAmount(e.target.value)}
                  required
                  style={{ fontSize: 15, fontWeight: 700 }}
                />
              </div>

              <div className="field">
                <label>Payment Method *</label>
                <select value={recMethod} onChange={e => setRecMethod(e.target.value)}>
                  <option value="Cash">Cash</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                  <option value="Cheque">Cheque</option>
                </select>
              </div>

              <div className="field">
                <label>Notes / Cheque / Bank Details (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. HBL deposit, Cheque #123456"
                  value={recNotes}
                  onChange={e => setRecNotes(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
                <button type="button" className="btn ghost" onClick={() => setShowRecModal(false)}>Cancel</button>
                <button type="submit" className="btn primary" disabled={recSaving}>
                  {recSaving ? 'Saving...' : 'Save Recovery'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

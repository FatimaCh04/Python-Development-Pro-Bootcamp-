import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchReportsMetrics,
  fetchSalesReport,
  fetchBookingReport,
  fetchDistributorLedgerReport,
  fetchRecoveryReport,
  fetchStockMovementReport,
  fetchReturnsReport,
  fetchExpenseReport,
  fetchPersonPaymentReport,
  fetchCommissionSettlementReport,
  fetchAdvWelfareReport,
  fetchProfitabilityReport,
  fetchDailyClosingReport,
  reconcileDailyClosing,
  approveDailyClosing,
  closeTodayLedger,
  fetchAuditLogs,
  fetchDistributors,
  fetchPersons
} from '../lib/db';
import { exportToCsv, printReport } from '../lib/exportUtils';

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
  const { role } = useAuth();
  const canApprove = role === 'Super_Admin' || role === 'Manager';

  const todayStr = new Date().toISOString().split('T')[0];
  const [activeTab, setActiveTab] = useState('summary');
  
  // Date filters
  const [startDate, setStartDate] = useState(todayStr);
  const [endDate, setEndDate] = useState(todayStr);
  const [distributorId, setDistributorId] = useState('');
  const [personId, setPersonId] = useState('');
  const [search, setSearch] = useState('');

  // Dropdown data
  const [distributors, setDistributors] = useState([]);
  const [persons, setPersons] = useState([]);

  // Data states for reports
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [msg, setMsg] = useState('');

  // Active dataset
  const [summaryMetrics, setSummaryMetrics] = useState(null);
  const [reportData, setReportData] = useState([]);
  const [profitData, setProfitData] = useState(null);
  const [advWelfData, setAdvWelfData] = useState(null);
  const [ledgerData, setLedgerData] = useState(null);

  // Daily Closing Reconcile Modal
  const [reconcileModal, setReconcileModal] = useState(null);
  const [submittedCash, setSubmittedCash] = useState('');
  const [submittedStock, setSubmittedStock] = useState('');
  const [reconcileNotes, setReconcileNotes] = useState('');
  const [submittingReconcile, setSubmittingReconcile] = useState(false);

  // Load dropdown lists on mount
  useEffect(() => {
    async function loadDropdowns() {
      try {
        const [dList, pList] = await Promise.all([
          fetchDistributors(),
          fetchPersons()
        ]);
        setDistributors(dList || []);
        setPersons(pList || []);
      } catch (e) {
        console.warn('Error loading dropdowns:', e);
      }
    }
    loadDropdowns();
  }, []);

  // Fetch report data on filter or tab change
  const loadActiveReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    setMsg('');

    try {
      const filters = {
        startDate,
        endDate,
        distributorId: distributorId || null,
        personId: personId || null
      };

      switch (activeTab) {
        case 'summary': {
          const data = await fetchReportsMetrics(startDate);
          setSummaryMetrics(data);
          break;
        }
        case 'sales': {
          const data = await fetchSalesReport(filters);
          setReportData(data || []);
          break;
        }
        case 'booking': {
          const data = await fetchBookingReport(filters);
          setReportData(data || []);
          break;
        }
        case 'ledger': {
          if (!distributorId) {
            setLedgerData(null);
          } else {
            const data = await fetchDistributorLedgerReport(distributorId, startDate, endDate);
            setLedgerData(data);
          }
          break;
        }
        case 'recovery': {
          const data = await fetchRecoveryReport(filters);
          setReportData(data || []);
          break;
        }
        case 'stock': {
          const data = await fetchStockMovementReport(filters);
          setReportData(data || []);
          break;
        }
        case 'returns': {
          const data = await fetchReturnsReport(filters);
          setReportData(data || []);
          break;
        }
        case 'expense': {
          const data = await fetchExpenseReport(filters);
          setReportData(data || []);
          break;
        }
        case 'person_payments': {
          const data = await fetchPersonPaymentReport(filters);
          setReportData(data || []);
          break;
        }
        case 'commission_settlements': {
          const data = await fetchCommissionSettlementReport(filters);
          setReportData(data || []);
          break;
        }
        case 'adv_welfare': {
          const data = await fetchAdvWelfareReport(filters);
          setAdvWelfData(data);
          break;
        }
        case 'pnl': {
          const data = await fetchProfitabilityReport(filters);
          setProfitData(data);
          break;
        }
        case 'daily_closing': {
          const data = await fetchDailyClosingReport(filters);
          setReportData(data || []);
          break;
        }
        case 'audit': {
          const data = await fetchAuditLogs(150);
          setReportData(data || []);
          break;
        }
        default:
          break;
      }
    } catch (err) {
      console.error(err);
      setError('Failed to load report data: ' + (err.message || 'Error occurred'));
    } finally {
      setLoading(false);
    }
  }, [activeTab, startDate, endDate, distributorId, personId]);

  useEffect(() => {
    loadActiveReport();
  }, [loadActiveReport]);

  // Daily Closing Actions
  const handleGenerateDailyTally = async () => {
    if (!window.confirm(`Generate daily closing drafts for ${fmtDate(startDate)}? This calculates expected figures and marks them as Pending for reconciliation.`)) return;
    setLoading(true);
    try {
      await closeTodayLedger({ closingDate: startDate });
      setMsg('ok:Daily closing drafts generated successfully. Please review and reconcile below.');
      await loadActiveReport();
    } catch (e) {
      setMsg('err:' + e.message);
      setLoading(false);
    }
  };

  const handleOpenReconcileModal = (closing) => {
    setReconcileModal(closing);
    setSubmittedCash(closing.submitted_cash !== null ? String(closing.submitted_cash) : '');
    const expStock = typeof closing.expected_stock === 'object' && closing.expected_stock !== null
      ? closing.expected_stock.packets
      : closing.expected_stock;
    const subStock = typeof closing.submitted_stock === 'object' && closing.submitted_stock !== null
      ? closing.submitted_stock.packets
      : closing.submitted_stock;
    setSubmittedStock(subStock !== null && subStock !== undefined ? String(subStock) : (expStock !== null ? String(expStock) : ''));
    setReconcileNotes(closing.notes || '');
  };

  const handleSaveReconciliation = async () => {
    if (!reconcileModal) return;
    setSubmittingReconcile(true);
    try {
      await reconcileDailyClosing({
        closingId: reconcileModal.id,
        submittedCash: Number(submittedCash),
        submittedStockPackets: Number(submittedStock),
        notes: reconcileNotes
      });
      setReconcileModal(null);
      setMsg('ok:Daily closing reconciled successfully.');
      await loadActiveReport();
    } catch (e) {
      alert('Error during reconciliation: ' + e.message);
    } finally {
      setSubmittingReconcile(false);
    }
  };

  const handleApproveClosing = async (closingId) => {
    if (!window.confirm('Approve this daily closing? This marks the reconciliation finalized.')) return;
    setLoading(true);
    try {
      await approveDailyClosing(closingId);
      setMsg('ok:Daily closing approved successfully.');
      await loadActiveReport();
    } catch (e) {
      setMsg('err:' + e.message);
      setLoading(false);
    }
  };

  // WhatsApp share for Summary
  const handleWhatsAppSummary = () => {
    if (!summaryMetrics) return;
    const goodRtn = (summaryMetrics.returns?.records || []).filter(r => r.transaction_type?.includes('Good_Return')).reduce((a, r) => a + Number(r.quantity), 0);
    const dmgRtn = (summaryMetrics.returns?.records || []).filter(r => r.transaction_type?.includes('Damaged_Return')).reduce((a, r) => a + Number(r.quantity), 0);
    const expAmount = (summaryMetrics.expense?.records || []).reduce((a, e) => a + Number(e.amount), 0);
    const recAmount = (summaryMetrics.recovery?.records || []).reduce((a, r) => a + Number(r.amount), 0);
    const bkgAmount = (summaryMetrics.booking?.records || []).reduce((a, b) => a + Number(b.total_amount), 0);

    const msgText = `*EliteWash ERP - Financial Report*\n` +
      `Date: ${fmtDate(startDate)}\n\n` +
      `*Daily Activity*\n` +
      `Sales: PKR ${fmtNum(summaryMetrics.sales.amount)} (${fmtNum(summaryMetrics.sales.packets)} pkts)\n` +
      `Bookings: PKR ${fmtNum(bkgAmount)}\n` +
      `Recovery: PKR ${fmtNum(recAmount)}\n` +
      `Expenses: PKR ${fmtNum(expAmount)}\n\n` +
      `*Fund Accounts*\n` +
      `Distributor Commission Balance: PKR ${fmtNum(summaryMetrics.distributorCommission.balance)}\n` +
      `Advertisement Balance: PKR ${fmtNum(summaryMetrics.advertisement.balance)}\n` +
      `Welfare Balance: PKR ${fmtNum(summaryMetrics.welfare.balance)}\n\n` +
      `*Returns*\n` +
      `Good Return: ${fmtNum(goodRtn)} pkts\n` +
      `Damaged Return: ${fmtNum(dmgRtn)} pkts`;

    const encoded = encodeURIComponent(msgText);
    window.open(`https://wa.me/?text=${encoded}`, '_blank');
  };

  // Export to CSV
  const handleExportCsv = () => {
    const filename = `EliteWash_${activeTab}_${startDate}_to_${endDate}.csv`;
    let headers = [];
    let rows = [];

    switch (activeTab) {
      case 'sales':
        headers = ['Date', 'Reference', 'Distributor', 'Packets', 'Total Amount', 'Commission Rate', 'Adv Rate', 'Welf Rate', 'Total Commission', 'Status'];
        rows = reportData.map(s => [
          fmtDateTime(s.sale_date),
          s.reference_number,
          s.distributors ? `${s.distributors.name} (${s.distributors.code})` : '—',
          s.totalPackets,
          s.total_amount,
          s.commRate ?? 'No Snapshot',
          s.advRate ?? '—',
          s.welfRate ?? '—',
          s.totalCommission ?? '—',
          s.status
        ]);
        break;
      case 'booking':
        headers = ['Date', 'Reference', 'Distributor', 'Packets', 'Total Amount', 'Status'];
        rows = reportData.map(b => [
          fmtDateTime(b.sale_date),
          b.reference_number,
          b.distributors ? `${b.distributors.name} (${b.distributors.code})` : '—',
          b.totalPackets,
          b.total_amount,
          b.status
        ]);
        break;
      case 'ledger':
        if (!ledgerData) return alert('Select a distributor to export ledger.');
        headers = ['Date', 'Reference', 'Description', 'Debit (Sales)', 'Credit (Recovery)', 'Balance', 'Status'];
        rows = (ledgerData.entries || []).map(e => [
          fmtDateTime(e.date),
          e.ref,
          e.description,
          e.debit,
          e.credit,
          e.balance,
          e.status
        ]);
        break;
      case 'recovery':
        headers = ['Date', 'Reference', 'Distributor', 'Amount', 'Payment Method', 'Account Detail', 'TID', 'Status', 'Notes'];
        rows = reportData.map(r => [
          fmtDateTime(r.recovery_date),
          r.reference_number,
          r.distributors ? `${r.distributors.name} (${r.distributors.code})` : '—',
          r.amount,
          r.payment_method,
          r.account_detail || '—',
          r.tid || '—',
          r.status,
          r.notes || '—'
        ]);
        break;
      case 'stock':
        headers = ['Date', 'Reference', 'Transaction Type', 'Product', 'Party', 'Quantity', 'Status'];
        rows = reportData.map(r => [
          fmtDateTime(r.transaction_date),
          r.reference_number,
          r.transaction_type,
          r.product_packaging?.products?.name ? `${r.product_packaging.products.name} (${r.product_packaging.name})` : 'Surf',
          r.distributors?.name || r.salesmen?.profiles?.full_name || 'Company',
          r.quantity,
          r.status
        ]);
        break;
      case 'returns':
        headers = ['Date', 'Reference', 'Distributor', 'Return Type', 'Quantity', 'Status', 'Notes'];
        rows = reportData.map(r => [
          fmtDateTime(r.transaction_date),
          r.reference_number,
          r.distributors ? `${r.distributors.name} (${r.distributors.code})` : '—',
          r.transaction_type,
          r.quantity,
          r.status,
          r.notes || '—'
        ]);
        break;
      case 'expense':
        headers = ['Date', 'Reference', 'Category', 'Head', 'Amount', 'Payment Method', 'Account Detail', 'TID', 'Description', 'Status'];
        rows = reportData.map(e => [
          fmtDateTime(e.expense_date),
          e.reference_number,
          e.category,
          e.head || '—',
          e.amount,
          e.payment_method || '—',
          e.account_detail || '—',
          e.tid || '—',
          e.description || '—',
          e.status
        ]);
        break;
      case 'person_payments':
        headers = ['Date', 'Reference', 'Person', 'Category', 'Entry Type', 'Direction', 'Quantity', 'Rate', 'Amount', 'Status'];
        rows = reportData.map(p => [
          fmtDateTime(p.entry_date),
          p.reference_number,
          p.persons?.name || '—',
          p.persons?.category || '—',
          p.entry_type,
          p.direction,
          p.quantity || 0,
          p.rate || 0,
          p.amount,
          p.status
        ]);
        break;
      case 'commission_settlements':
        headers = ['Date', 'Reference', 'Distributor', 'Settlement Type', 'Amount', 'Payment Method', 'Status', 'Notes'];
        rows = reportData.map(s => [
          fmtDateTime(s.settlement_date),
          s.reference_number,
          s.distributors ? `${s.distributors.name} (${s.distributors.code})` : '—',
          s.settlement_type,
          s.amount,
          s.payment_method,
          s.status,
          s.notes || '—'
        ]);
        break;
      case 'daily_closing':
        headers = ['Date', 'Distributor', 'Expected Cash', 'Submitted Cash', 'Cash Variance', 'Expected Stock', 'Submitted Stock', 'Status'];
        rows = reportData.map(c => {
          const expStock = typeof c.expected_stock === 'object' && c.expected_stock !== null ? c.expected_stock.packets : c.expected_stock;
          const subStock = typeof c.submitted_stock === 'object' && c.submitted_stock !== null ? c.submitted_stock.packets : c.submitted_stock;
          const cashVar = (c.submitted_cash !== null && c.submitted_cash !== undefined) ? (Number(c.submitted_cash) - Number(c.expected_cash || 0)) : 'Unreconciled';
          return [
            fmtDate(c.closing_date),
            c.distributors?.name || c.salesmen?.profiles?.full_name || '—',
            c.expected_cash,
            c.submitted_cash ?? '—',
            cashVar,
            expStock ?? 0,
            subStock ?? '—',
            c.status
          ];
        });
        break;
      default:
        return alert('Export not supported for this tab.');
    }

    exportToCsv(filename, headers, rows);
  };

  // Print Report
  const handlePrintReport = () => {
    let title = 'Financial Report';
    let subtitle = `Period: ${fmtDate(startDate)} to ${fmtDate(endDate)}`;
    let headers = [];
    let rows = [];
    let summaryBoxes = [];

    if (activeTab === 'summary') {
      window.print();
      return;
    }

    if (activeTab === 'sales') {
      title = 'Sales Report';
      headers = ['Date', 'Ref', 'Distributor', 'Packets', 'Total Amount', 'Commission Snapshot', 'Status'];
      const totalAmount = reportData.reduce((a, s) => a + Number(s.total_amount || 0), 0);
      const totalPackets = reportData.reduce((a, s) => a + Number(s.totalPackets || 0), 0);
      summaryBoxes = [
        { label: 'Total Sales', value: `PKR ${fmtNum(totalAmount)}` },
        { label: 'Total Packets', value: `${fmtNum(totalPackets)} pkts` },
        { label: 'Order Count', value: reportData.length }
      ];
      rows = reportData.map(s => [
        fmtDateTime(s.sale_date),
        s.reference_number,
        s.distributors?.name || '—',
        s.totalPackets,
        `PKR ${fmtNum(s.total_amount)}`,
        s.commRate !== null ? `Rs. ${s.commRate}/pkt` : 'No Snapshot',
        s.status
      ]);
    } else if (activeTab === 'ledger' && ledgerData) {
      title = `Distributor Ledger — ${ledgerData.distributor?.name} (${ledgerData.distributor?.code})`;
      summaryBoxes = [
        { label: 'Opening Balance', value: `PKR ${fmtNum(ledgerData.openingBalance)}` },
        { label: 'Period Sales', value: `PKR ${fmtNum(ledgerData.totalSales)}` },
        { label: 'Period Recoveries', value: `PKR ${fmtNum(ledgerData.totalRecoveries)}` },
        { label: 'Closing Outstanding', value: `PKR ${fmtNum(ledgerData.closingBalance)}` }
      ];
      headers = ['Date', 'Ref', 'Description', 'Debit', 'Credit', 'Running Balance'];
      rows = (ledgerData.entries || []).map(e => [
        fmtDate(e.date),
        e.ref,
        e.description,
        e.debit ? `PKR ${fmtNum(e.debit)}` : '—',
        e.credit ? `PKR ${fmtNum(e.credit)}` : '—',
        `PKR ${fmtNum(e.balance)}`
      ]);
    } else if (activeTab === 'daily_closing') {
      title = 'Daily Closing Reconciliation Report';
      headers = ['Closing Date', 'Party', 'Expected Cash', 'Submitted Cash', 'Cash Variance', 'Expected Stock', 'Submitted Stock', 'Status'];
      rows = reportData.map(c => {
        const expStock = typeof c.expected_stock === 'object' && c.expected_stock !== null ? c.expected_stock.packets : c.expected_stock;
        const subStock = typeof c.submitted_stock === 'object' && c.submitted_stock !== null ? c.submitted_stock.packets : c.submitted_stock;
        const cashVar = (c.submitted_cash !== null && c.submitted_cash !== undefined) ? (Number(c.submitted_cash) - Number(c.expected_cash || 0)) : null;
        return [
          fmtDate(c.closing_date),
          c.distributors?.name || c.salesmen?.profiles?.full_name || '—',
          `PKR ${fmtNum(c.expected_cash)}`,
          c.submitted_cash !== null ? `PKR ${fmtNum(c.submitted_cash)}` : '—',
          cashVar !== null ? `PKR ${fmtNum(cashVar)}` : 'Unreconciled',
          `${fmtNum(expStock)} pkts`,
          subStock !== null ? `${fmtNum(subStock)} pkts` : '—',
          c.status
        ];
      });
    } else {
      window.print();
      return;
    }

    printReport({ title, subtitle, dateRange: `${startDate} to ${endDate}`, headers, rows, summaryBoxes });
  };

  return (
    <div className="dashboard-container reports-print-wrapper">
      {/* HEADER */}
      <div className="dash-header no-print">
        <div>
          <h1>Financial &amp; Operational Reports</h1>
          <p>Strictly verified transaction figures · Full audit reconciliation</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <button className="btn" onClick={handleExportCsv}>
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: 5 }}><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Export CSV
          </button>
          <button className="btn ghost" onClick={handlePrintReport}>
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: 5 }}><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            Print
          </button>
          {activeTab === 'summary' && (
            <button className="btn" style={{ background: '#25D366', color: '#fff', borderColor: '#25D366' }} onClick={handleWhatsAppSummary}>
              WhatsApp
            </button>
          )}
        </div>
      </div>

      {/* TABS SELECTOR */}
      <div className="no-print" style={{ marginBottom: 16 }}>
        <div className="chip-list" style={{ gap: 6 }}>
          {[
            { key: 'summary', label: '📊 Summary Dashboard' },
            { key: 'sales', label: '💰 Daily Sales' },
            { key: 'booking', label: '📝 Bookings' },
            { key: 'ledger', label: '📑 Distributor Ledger' },
            { key: 'recovery', label: '💵 Recoveries' },
            { key: 'stock', label: '📦 Stock Movements' },
            { key: 'returns', label: '🔄 Returns' },
            { key: 'expense', label: '🧾 Expenses' },
            { key: 'person_payments', label: '👷 Person Payments' },
            { key: 'commission_settlements', label: '🤝 Commission Settlements' },
            { key: 'adv_welfare', label: '🎯 Adv & Welfare Funds' },
            { key: 'pnl', label: '📈 Profit & Loss' },
            { key: 'daily_closing', label: '🔒 Daily Closing' },
            { key: 'audit', label: '🛡️ Audit Trail' },
          ].map(tab => (
            <div
              key={tab.key}
              className={`chip${activeTab === tab.key ? ' active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </div>
          ))}
        </div>
      </div>

      {/* FILTER CONTROLS */}
      <div className="panel-flat no-print" style={{ padding: '12px 16px', marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <div className="field" style={{ margin: 0, minWidth: 140 }}>
            <label style={{ fontSize: 11, marginBottom: 2 }}>Start Date</label>
            <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
          </div>

          <div className="field" style={{ margin: 0, minWidth: 140 }}>
            <label style={{ fontSize: 11, marginBottom: 2 }}>End Date</label>
            <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
          </div>

          {(activeTab === 'ledger' || activeTab === 'sales' || activeTab === 'booking' || activeTab === 'recovery' || activeTab === 'commission_settlements' || activeTab === 'daily_closing') && (
            <div className="field" style={{ margin: 0, minWidth: 200 }}>
              <label style={{ fontSize: 11, marginBottom: 2 }}>Distributor Filter</label>
              <select value={distributorId} onChange={e => setDistributorId(e.target.value)}>
                <option value="">-- All Distributors --</option>
                {distributors.map(d => (
                  <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
                ))}
              </select>
            </div>
          )}

          {activeTab === 'person_payments' && (
            <div className="field" style={{ margin: 0, minWidth: 200 }}>
              <label style={{ fontSize: 11, marginBottom: 2 }}>Person Filter</label>
              <select value={personId} onChange={e => setPersonId(e.target.value)}>
                <option value="">-- All Persons --</option>
                {persons.map(p => (
                  <option key={p.id} value={p.id}>{p.name} ({p.category})</option>
                ))}
              </select>
            </div>
          )}

          <div className="field" style={{ margin: 0, flex: 1, minWidth: 160 }}>
            <label style={{ fontSize: 11, marginBottom: 2 }}>Search Text</label>
            <input
              type="text"
              placeholder="Search reference, party, notes..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          <div style={{ alignSelf: 'flex-end' }}>
            <button className="btn primary" onClick={loadActiveReport} style={{ padding: '7px 16px' }}>
              Apply Filter
            </button>
          </div>
        </div>
      </div>

      {msg && (
        <div style={{
          padding: '10px 14px',
          marginBottom: 16,
          borderRadius: 6,
          fontSize: 12.5,
          background: msg.startsWith('err') ? 'var(--red-soft)' : 'var(--green-soft)',
          color: msg.startsWith('err') ? 'var(--red)' : 'var(--green)'
        }}>
          {msg.replace(/^(ok|err):/, '')}
        </div>
      )}

      {error && (
        <div style={{ padding: 16, marginBottom: 16, borderRadius: 6, background: 'var(--red-soft)', color: 'var(--red)' }}>
          {error}
        </div>
      )}

      {/* TAB CONTENT */}
      {loading ? (
        <div className="panel" style={{ padding: 60, textAlign: 'center', color: 'var(--text-dim)' }}>
          <div className="splash-loader" style={{ minHeight: 'auto', background: 'transparent' }}>
            <div className="brand-mark">EW</div>
            <p>Loading report data...</p>
          </div>
        </div>
      ) : (
        <>
          {/* 1. SUMMARY DASHBOARD TAB */}
          {activeTab === 'summary' && summaryMetrics && (
            <>
              <div className="grid g4" style={{ marginBottom: 20 }}>
                <div className="tile teal">
                  <div className="label">Total Sales</div>
                  <div className="num">PKR {fmtNum(summaryMetrics.sales.amount)}</div>
                  <div className="delta up">{fmtNum(summaryMetrics.sales.packets)} pkts</div>
                </div>
                <div className="tile amber">
                  <div className="label">Total Bookings</div>
                  <div className="num">PKR {fmtNum((summaryMetrics.booking?.records || []).reduce((a, b) => a + Number(b.total_amount || 0), 0))}</div>
                  <div className="delta down">{(summaryMetrics.booking?.records || []).reduce((a, b) => a + b.packets, 0)} pkts (Pending)</div>
                </div>
                <div className="tile green">
                  <div className="label">Recovery Amount</div>
                  <div className="num">PKR {fmtNum((summaryMetrics.recovery?.records || []).reduce((a, r) => a + Number(r.amount || 0), 0))}</div>
                  <div className="delta up">Approved recoveries</div>
                </div>
                <div className="tile red">
                  <div className="label">Total Expenses</div>
                  <div className="num">PKR {fmtNum((summaryMetrics.expense?.records || []).reduce((a, e) => a + Number(e.amount || 0), 0))}</div>
                  <div className="delta down">Approved expenses</div>
                </div>
              </div>

              <div className="grid g2" style={{ alignItems: 'start', marginBottom: 20 }}>
                <div className="panel">
                  <div className="section-head" style={{ marginBottom: 12 }}>
                    <h2>Financial Accounts &amp; Fund Balances</h2>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ background: '#F9F8F6', padding: 14, borderRadius: 8, border: '1px solid var(--line)' }}>
                      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--teal)' }}>Distributor Commission Fund</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Accrued from Verified Snapshots</span>
                        <span>PKR {fmtNum(summaryMetrics.distributorCommission.allocation)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Distributor Specific Expenses</span>
                        <span style={{ color: 'var(--red)' }}>− PKR {fmtNum(summaryMetrics.distributorCommission.expenses)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13.5, fontWeight: 700, borderTop: '1px solid var(--line)', paddingTop: 8 }}>
                        <span>Net Commission Position</span>
                        <span>PKR {fmtNum(summaryMetrics.distributorCommission.balance)}</span>
                      </div>
                    </div>

                    <div style={{ background: '#F9F8F6', padding: 14, borderRadius: 8, border: '1px solid var(--line)' }}>
                      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--teal)' }}>Advertisement Fund</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Opening Fund Balance</span>
                        <span>PKR {fmtNum(summaryMetrics.advertisement.opening)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Cumulative Snapshot Allocation</span>
                        <span style={{ color: 'var(--green)' }}>+ PKR {fmtNum(summaryMetrics.advertisement.allocation)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Approved Advertisement Expenses</span>
                        <span style={{ color: 'var(--red)' }}>− PKR {fmtNum(summaryMetrics.advertisement.expenses)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13.5, fontWeight: 700, borderTop: '1px solid var(--line)', paddingTop: 8 }}>
                        <span>Current Fund Balance</span>
                        <span>PKR {fmtNum(summaryMetrics.advertisement.balance)}</span>
                      </div>
                    </div>

                    <div style={{ background: '#F9F8F6', padding: 14, borderRadius: 8, border: '1px solid var(--line)' }}>
                      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--teal)' }}>Welfare Fund</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Opening Fund Balance</span>
                        <span>PKR {fmtNum(summaryMetrics.welfare.opening)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Cumulative Snapshot Allocation</span>
                        <span style={{ color: 'var(--green)' }}>+ PKR {fmtNum(summaryMetrics.welfare.allocation)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Approved Welfare Expenses</span>
                        <span style={{ color: 'var(--red)' }}>− PKR {fmtNum(summaryMetrics.welfare.expenses)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13.5, fontWeight: 700, borderTop: '1px solid var(--line)', paddingTop: 8 }}>
                        <span>Current Fund Balance</span>
                        <span>PKR {fmtNum(summaryMetrics.welfare.balance)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="panel">
                  <div className="section-head" style={{ marginBottom: 12 }}>
                    <h2>Stock &amp; Operational Position</h2>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ background: '#F9F8F6', padding: 14, borderRadius: 8, border: '1px solid var(--line)' }}>
                      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--teal)' }}>Company Physical Stock</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Saleable Available Stock</span>
                        <span style={{ fontWeight: 600 }}>{fmtNum(summaryMetrics.stock.sellable)} pkts</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Damaged Stock (Strictly Isolated)</span>
                        <span style={{ fontWeight: 600, color: 'var(--red)' }}>{fmtNum(summaryMetrics.stock.damaged)} pkts</span>
                      </div>
                    </div>

                    <div style={{ background: '#F9F8F6', padding: 14, borderRadius: 8, border: '1px solid var(--line)' }}>
                      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--teal)' }}>Returns Summary</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Good Returns (Returned to Saleable)</span>
                        <span style={{ fontWeight: 600 }}>
                          {fmtNum((summaryMetrics.returns?.records || []).filter(r => r.transaction_type?.includes('Good_Return')).reduce((a, r) => a + Number(r.quantity), 0))} pkts
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                        <span style={{ color: 'var(--text-dim)' }}>Damaged Returns</span>
                        <span style={{ fontWeight: 600, color: 'var(--red)' }}>
                          {fmtNum((summaryMetrics.returns?.records || []).filter(r => r.transaction_type?.includes('Damaged_Return')).reduce((a, r) => a + Number(r.quantity), 0))} pkts
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* 2. DAILY SALES REPORT */}
          {activeTab === 'sales' && (
            <div className="panel">
              <div className="section-head">
                <h2>Daily Sales Report</h2>
                <span className="badge green">{reportData.length} Orders</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Reference</th>
                      <th>Distributor</th>
                      <th style={{ textAlign: 'right' }}>Packets</th>
                      <th style={{ textAlign: 'right' }}>Gross Amount</th>
                      <th style={{ textAlign: 'right' }}>Comm Rate</th>
                      <th style={{ textAlign: 'right' }}>Adv Rate</th>
                      <th style={{ textAlign: 'right' }}>Welf Rate</th>
                      <th style={{ textAlign: 'right' }}>Accrued Comm</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="10" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No sales orders matching filters.</td></tr>
                    ) : (
                      reportData.map(s => (
                        <tr key={s.id}>
                          <td>{fmtDateTime(s.sale_date)}</td>
                          <td style={{ fontFamily: 'monospace' }}>{s.reference_number}</td>
                          <td>{s.distributors ? `${s.distributors.name} (${s.distributors.code})` : '—'}</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtNum(s.totalPackets)}</td>
                          <td style={{ textAlign: 'right', color: 'var(--teal)', fontWeight: 600 }}>PKR {fmtNum(s.total_amount)}</td>
                          <td style={{ textAlign: 'right' }}>
                            {s.commRate !== null ? `Rs. ${s.commRate}` : <span className="badge amber">No Snapshot</span>}
                          </td>
                          <td style={{ textAlign: 'right' }}>{s.advRate !== null ? `Rs. ${s.advRate}` : '—'}</td>
                          <td style={{ textAlign: 'right' }}>{s.welfRate !== null ? `Rs. ${s.welfRate}` : '—'}</td>
                          <td style={{ textAlign: 'right' }}>{s.totalCommission !== null ? `PKR ${fmtNum(s.totalCommission)}` : '—'}</td>
                          <td><span className="badge green">{s.status}</span></td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 3. BOOKINGS REPORT */}
          {activeTab === 'booking' && (
            <div className="panel">
              <div className="section-head">
                <h2>Booking Ledger Report</h2>
                <span className="badge amber">{reportData.length} Bookings</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Reference</th>
                      <th>Distributor</th>
                      <th style={{ textAlign: 'right' }}>Packets</th>
                      <th style={{ textAlign: 'right' }}>Total Amount</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="6" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No booking orders found.</td></tr>
                    ) : (
                      reportData.map(b => (
                        <tr key={b.id}>
                          <td>{fmtDateTime(b.sale_date)}</td>
                          <td style={{ fontFamily: 'monospace' }}>{b.reference_number}</td>
                          <td>{b.distributors ? `${b.distributors.name} (${b.distributors.code})` : '—'}</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtNum(b.totalPackets)}</td>
                          <td style={{ textAlign: 'right' }}>PKR {fmtNum(b.total_amount)}</td>
                          <td><span className="badge amber">{b.status}</span></td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 4. DISTRIBUTOR LEDGER */}
          {activeTab === 'ledger' && (
            <div className="panel">
              <div className="section-head">
                <h2>Distributor Statement &amp; Running Ledger</h2>
                {ledgerData?.distributor && (
                  <span className="badge teal">{ledgerData.distributor.name} ({ledgerData.distributor.code})</span>
                )}
              </div>
              {!distributorId ? (
                <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)' }}>
                  Please select a distributor in the filter bar above to view their running ledger.
                </div>
              ) : ledgerData ? (
                <>
                  <div className="grid g4" style={{ marginBottom: 18 }}>
                    <div className="panel-flat">
                      <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Opening Outstanding</div>
                      <div style={{ fontSize: 18, fontWeight: 700 }}>PKR {fmtNum(ledgerData.openingBalance)}</div>
                    </div>
                    <div className="panel-flat">
                      <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Period Sales (Debit)</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--teal)' }}>PKR {fmtNum(ledgerData.totalSales)}</div>
                    </div>
                    <div className="panel-flat">
                      <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Period Recoveries (Credit)</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--green)' }}>PKR {fmtNum(ledgerData.totalRecoveries)}</div>
                    </div>
                    <div className="panel-flat">
                      <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Closing Outstanding</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: ledgerData.closingBalance > 0 ? 'var(--red)' : 'var(--green)' }}>
                        PKR {fmtNum(ledgerData.closingBalance)}
                      </div>
                    </div>
                  </div>

                  <div style={{ overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Reference</th>
                          <th>Type &amp; Description</th>
                          <th style={{ textAlign: 'right' }}>Debit (Sales)</th>
                          <th style={{ textAlign: 'right' }}>Credit (Recovery)</th>
                          <th style={{ textAlign: 'right' }}>Running Outstanding</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ledgerData.entries.length === 0 ? (
                          <tr><td colSpan="6" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No ledger entries in this period.</td></tr>
                        ) : (
                          ledgerData.entries.map((e, idx) => (
                            <tr key={idx}>
                              <td>{fmtDate(e.date)}</td>
                              <td style={{ fontFamily: 'monospace' }}>{e.ref}</td>
                              <td>{e.description}</td>
                              <td style={{ textAlign: 'right', color: e.debit ? 'var(--teal)' : 'inherit' }}>
                                {e.debit ? `PKR ${fmtNum(e.debit)}` : '—'}
                              </td>
                              <td style={{ textAlign: 'right', color: e.credit ? 'var(--green)' : 'inherit' }}>
                                {e.credit ? `PKR ${fmtNum(e.credit)}` : '—'}
                              </td>
                              <td style={{ textAlign: 'right', fontWeight: 700, color: e.balance > 0 ? 'var(--red)' : 'var(--green)' }}>
                                PKR {fmtNum(e.balance)}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : null}
            </div>
          )}

          {/* 5. RECOVERIES REPORT */}
          {activeTab === 'recovery' && (
            <div className="panel">
              <div className="section-head">
                <h2>Recovery Report</h2>
                <span className="badge green">{reportData.length} Recoveries</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Reference</th>
                      <th>Distributor</th>
                      <th style={{ textAlign: 'right' }}>Amount</th>
                      <th>Method</th>
                      <th>Account Detail</th>
                      <th>TID</th>
                      <th>Status</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="9" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No recoveries found.</td></tr>
                    ) : (
                      reportData.map(r => (
                        <tr key={r.id}>
                          <td>{fmtDateTime(r.recovery_date)}</td>
                          <td style={{ fontFamily: 'monospace' }}>{r.reference_number || '—'}</td>
                          <td>{r.distributors ? `${r.distributors.name} (${r.distributors.code})` : '—'}</td>
                          <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--green)' }}>PKR {fmtNum(r.amount)}</td>
                          <td><span className="badge teal">{r.payment_method || 'Cash'}</span></td>
                          <td>{r.account_detail || '—'}</td>
                          <td>{r.tid || '—'}</td>
                          <td><span className="badge green">{r.status}</span></td>
                          <td style={{ color: 'var(--text-dim)' }}>{r.notes || '—'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 6. STOCK MOVEMENTS REPORT */}
          {activeTab === 'stock' && (
            <div className="panel">
              <div className="section-head">
                <h2>Stock Movement Report</h2>
                <span className="badge teal">{reportData.length} Movements</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Reference</th>
                      <th>Movement Type</th>
                      <th>Product</th>
                      <th>Party</th>
                      <th style={{ textAlign: 'right' }}>Quantity</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="7" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No inventory movements found.</td></tr>
                    ) : (
                      reportData.map(r => (
                        <tr key={r.id}>
                          <td>{fmtDateTime(r.transaction_date)}</td>
                          <td style={{ fontFamily: 'monospace' }}>{r.reference_number}</td>
                          <td>
                            <span className={`badge ${
                              r.transaction_type.includes('Good_Return') || r.transaction_type === 'Production' || r.transaction_type === 'Purchase'
                                ? 'green'
                                : r.transaction_type.includes('Damaged')
                                ? 'red'
                                : 'teal'
                            }`}>
                              {r.transaction_type.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td>{r.product_packaging?.products?.name ? `${r.product_packaging.products.name} (${r.product_packaging.name})` : 'Surf'}</td>
                          <td>{r.distributors?.name || r.salesmen?.profiles?.full_name || 'Company Internal'}</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtNum(r.quantity)} pkts</td>
                          <td><span className="badge green">{r.status}</span></td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 7. RETURNS REPORT */}
          {activeTab === 'returns' && (
            <div className="panel">
              <div className="section-head">
                <h2>Returns Report (Good vs Damaged)</h2>
                <span className="badge amber">{reportData.length} Returns</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Reference</th>
                      <th>Distributor</th>
                      <th>Condition / Category</th>
                      <th style={{ textAlign: 'right' }}>Quantity</th>
                      <th>Effect on Saleable Stock</th>
                      <th>Status</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="8" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No returns found.</td></tr>
                    ) : (
                      reportData.map(r => {
                        const isGood = r.transaction_type.includes('Good_Return');
                        return (
                          <tr key={r.id}>
                            <td>{fmtDateTime(r.transaction_date)}</td>
                            <td style={{ fontFamily: 'monospace' }}>{r.reference_number}</td>
                            <td>{r.distributors ? `${r.distributors.name} (${r.distributors.code})` : '—'}</td>
                            <td>
                              <span className={`badge ${isGood ? 'green' : 'red'}`}>
                                {isGood ? 'Good Return' : 'Damaged Return'}
                              </span>
                            </td>
                            <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtNum(r.quantity)} pkts</td>
                            <td style={{ fontSize: 12, color: isGood ? 'var(--green)' : 'var(--red)' }}>
                              {isGood ? 'Increases Saleable Stock' : 'Isolated in Damaged Stock'}
                            </td>
                            <td><span className="badge green">{r.status}</span></td>
                            <td style={{ color: 'var(--text-dim)' }}>{r.notes || '—'}</td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 8. EXPENSES REPORT */}
          {activeTab === 'expense' && (
            <div className="panel">
              <div className="section-head">
                <h2>Expense Report</h2>
                <span className="badge red">{reportData.length} Expenses</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Reference</th>
                      <th>Category</th>
                      <th>Head</th>
                      <th>Party</th>
                      <th style={{ textAlign: 'right' }}>Amount</th>
                      <th>Method</th>
                      <th>TID</th>
                      <th>Description</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="10" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No expenses found.</td></tr>
                    ) : (
                      reportData.map(e => (
                        <tr key={e.id}>
                          <td>{fmtDateTime(e.expense_date)}</td>
                          <td style={{ fontFamily: 'monospace' }}>{e.reference_number}</td>
                          <td><span className="badge gray">{e.category}</span></td>
                          <td>{e.head || '—'}</td>
                          <td>{e.distributors?.name || e.persons?.name || '—'}</td>
                          <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--red)' }}>PKR {fmtNum(e.amount)}</td>
                          <td>{e.payment_method || 'Cash'}</td>
                          <td>{e.tid || '—'}</td>
                          <td>{e.description}</td>
                          <td><span className="badge green">{e.status}</span></td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 9. PERSON PAYMENTS REPORT */}
          {activeTab === 'person_payments' && (
            <div className="panel">
              <div className="section-head">
                <h2>Person Payment &amp; Work Earnings Report</h2>
                <span className="badge teal">{reportData.length} Entries</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Reference</th>
                      <th>Person</th>
                      <th>Role</th>
                      <th>Entry Type</th>
                      <th>Direction</th>
                      <th style={{ textAlign: 'right' }}>Qty</th>
                      <th style={{ textAlign: 'right' }}>Rate</th>
                      <th style={{ textAlign: 'right' }}>Amount</th>
                      <th>Linked Expense</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="11" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No person payment entries found.</td></tr>
                    ) : (
                      reportData.map(p => (
                        <tr key={p.id}>
                          <td>{fmtDateTime(p.entry_date)}</td>
                          <td style={{ fontFamily: 'monospace' }}>{p.reference_number}</td>
                          <td><strong>{p.persons?.name || '—'}</strong></td>
                          <td><span className="badge gray">{p.persons?.category || '—'}</span></td>
                          <td>{p.entry_type.replace(/_/g, ' ')}</td>
                          <td><span className={`badge ${p.direction === 'Payable' ? 'amber' : 'green'}`}>{p.direction}</span></td>
                          <td style={{ textAlign: 'right' }}>{p.quantity ? fmtNum(p.quantity) : '—'}</td>
                          <td style={{ textAlign: 'right' }}>{p.rate ? `Rs. ${p.rate}` : '—'}</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>PKR {fmtNum(p.amount)}</td>
                          <td>{p.expenses?.reference_number ? <span className="badge gray">{p.expenses.reference_number}</span> : '—'}</td>
                          <td><span className={`badge ${p.status === 'Approved' ? 'green' : 'amber'}`}>{p.status}</span></td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 10. COMMISSION SETTLEMENTS REPORT */}
          {activeTab === 'commission_settlements' && (
            <div className="panel">
              <div className="section-head">
                <h2>Distributor Commission Settlement Report</h2>
                <span className="badge teal">{reportData.length} Settlements</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Reference</th>
                      <th>Distributor</th>
                      <th>Settlement Mode</th>
                      <th style={{ textAlign: 'right' }}>Amount</th>
                      <th>Payment Method</th>
                      <th>Linked Recovery</th>
                      <th>Status</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="9" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No settlements found.</td></tr>
                    ) : (
                      reportData.map(s => (
                        <tr key={s.id}>
                          <td>{fmtDateTime(s.settlement_date)}</td>
                          <td style={{ fontFamily: 'monospace' }}>{s.reference_number}</td>
                          <td>{s.distributors ? `${s.distributors.name} (${s.distributors.code})` : '—'}</td>
                          <td>
                            <span className={`badge ${s.settlement_type === 'Commission_Against_Outstanding' ? 'teal' : 'gray'}`}>
                              {s.settlement_type.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--teal)' }}>PKR {fmtNum(s.amount)}</td>
                          <td>{s.payment_method}</td>
                          <td>{s.recoveries?.reference_number ? <span className="badge green">{s.recoveries.reference_number}</span> : '—'}</td>
                          <td><span className={`badge ${s.status === 'Approved' ? 'green' : s.status === 'Pending' ? 'amber' : 'red'}`}>{s.status}</span></td>
                          <td style={{ color: 'var(--text-dim)' }}>{s.notes || '—'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 11. ADV & WELFARE FUNDS REPORT */}
          {activeTab === 'adv_welfare' && advWelfData && (
            <div className="panel">
              <div className="section-head">
                <h2>Advertisement &amp; Welfare Fund Reconciliation</h2>
              </div>
              <div className="grid g2" style={{ marginBottom: 20 }}>
                <div className="panel-flat">
                  <h3 style={{ fontSize: 14, color: 'var(--teal)', marginBottom: 12 }}>🎯 Advertisement Fund</h3>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Opening Fund Balance</span>
                    <span>PKR {fmtNum(advWelfData.advertisement.opening)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Allocated from Sales Snapshots</span>
                    <span style={{ color: 'var(--green)' }}>+ PKR {fmtNum(advWelfData.advertisement.allocated)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10, fontSize: 13 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Approved Expenses Deducted</span>
                    <span style={{ color: 'var(--red)' }}>− PKR {fmtNum(advWelfData.advertisement.spent)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 15, fontWeight: 700, borderTop: '1px solid var(--line)', paddingTop: 10 }}>
                    <span>Net Fund Balance</span>
                    <span style={{ color: 'var(--teal)' }}>PKR {fmtNum(advWelfData.advertisement.balance)}</span>
                  </div>
                </div>

                <div className="panel-flat">
                  <h3 style={{ fontSize: 14, color: 'var(--green)', marginBottom: 12 }}>🤝 Welfare Fund</h3>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Opening Fund Balance</span>
                    <span>PKR {fmtNum(advWelfData.welfare.opening)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Allocated from Sales Snapshots</span>
                    <span style={{ color: 'var(--green)' }}>+ PKR {fmtNum(advWelfData.welfare.allocated)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10, fontSize: 13 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Approved Expenses Deducted</span>
                    <span style={{ color: 'var(--red)' }}>− PKR {fmtNum(advWelfData.welfare.spent)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 15, fontWeight: 700, borderTop: '1px solid var(--line)', paddingTop: 10 }}>
                    <span>Net Fund Balance</span>
                    <span style={{ color: 'var(--green)' }}>PKR {fmtNum(advWelfData.welfare.balance)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 12. PROFIT & LOSS REPORT */}
          {activeTab === 'pnl' && profitData && (
            <div className="panel">
              <div className="section-head">
                <h2>Profit &amp; Loss Statement</h2>
                <span className="badge teal">{fmtDate(startDate)} to {fmtDate(endDate)}</span>
              </div>
              <div className="grid g3" style={{ marginBottom: 20 }}>
                <div className="panel-flat">
                  <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Total Revenue</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--teal)' }}>PKR {fmtNum(profitData.revenue)}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>{profitData.salesCount} approved orders</div>
                </div>
                <div className="panel-flat">
                  <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Cost of Goods Sold (COGS)</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--amber)' }}>PKR {fmtNum(profitData.cogs)}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Unit production &amp; packaging cost</div>
                </div>
                <div className="panel-flat">
                  <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Net Profit (Estimated)</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: profitData.netProfit >= 0 ? 'var(--green)' : 'var(--red)' }}>
                    PKR {fmtNum(profitData.netProfit)}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Margin: {profitData.marginPct}%</div>
                </div>
              </div>

              <table>
                <tbody>
                  <tr>
                    <td><strong>Gross Revenue (Sales)</strong></td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>PKR {fmtNum(profitData.revenue)}</td>
                  </tr>
                  <tr>
                    <td style={{ paddingLeft: 24, color: 'var(--text-dim)' }}>Less: Cost of Goods Sold (COGS)</td>
                    <td style={{ textAlign: 'right', color: 'var(--red)' }}>− PKR {fmtNum(profitData.cogs)}</td>
                  </tr>
                  <tr style={{ background: '#FAF9F6' }}>
                    <td><strong>Gross Profit</strong></td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--teal)' }}>PKR {fmtNum(profitData.grossProfit)}</td>
                  </tr>
                  <tr>
                    <td style={{ paddingLeft: 24, color: 'var(--text-dim)' }}>Less: Approved Operating Expenses</td>
                    <td style={{ textAlign: 'right', color: 'var(--red)' }}>− PKR {fmtNum(profitData.expenses)}</td>
                  </tr>
                  <tr style={{ borderTop: '2px solid var(--line)', background: '#F5F9F6' }}>
                    <td><strong style={{ fontSize: 14 }}>Net Operating Profit / (Loss)</strong></td>
                    <td style={{ textAlign: 'right', fontSize: 15, fontWeight: 800, color: profitData.netProfit >= 0 ? 'var(--green)' : 'var(--red)' }}>
                      PKR {fmtNum(profitData.netProfit)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* 13. DAILY CLOSING REPORT */}
          {activeTab === 'daily_closing' && (
            <div className="panel">
              <div className="section-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2>Daily Closing &amp; Cash Reconciliation</h2>
                  <p style={{ margin: 0, fontSize: 12, color: 'var(--text-dim)' }}>
                    Strict verification required. Variances are highlighted and require explanation.
                  </p>
                </div>
                <button className="btn primary" onClick={handleGenerateDailyTally}>
                  + Generate Daily Tally for {fmtDate(startDate)}
                </button>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Closing Date</th>
                      <th>Party</th>
                      <th style={{ textAlign: 'right' }}>Expected Cash</th>
                      <th style={{ textAlign: 'right' }}>Submitted Cash</th>
                      <th style={{ textAlign: 'right' }}>Cash Variance</th>
                      <th style={{ textAlign: 'right' }}>Expected Stock</th>
                      <th style={{ textAlign: 'right' }}>Submitted Stock</th>
                      <th>Status</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="9" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No daily closing records found for selected period. Click "+ Generate Daily Tally" above.</td></tr>
                    ) : (
                      reportData.map(c => {
                        const expStock = typeof c.expected_stock === 'object' && c.expected_stock !== null ? c.expected_stock.packets : c.expected_stock;
                        const subStock = typeof c.submitted_stock === 'object' && c.submitted_stock !== null ? c.submitted_stock.packets : c.submitted_stock;
                        const hasSubmitted = c.submitted_cash !== null && c.submitted_cash !== undefined;
                        const cashVariance = hasSubmitted ? (Number(c.submitted_cash) - Number(c.expected_cash || 0)) : null;

                        return (
                          <tr key={c.id}>
                            <td>{fmtDate(c.closing_date)}</td>
                            <td>{c.distributors?.name || c.salesmen?.profiles?.full_name || '—'}</td>
                            <td style={{ textAlign: 'right' }}>PKR {fmtNum(c.expected_cash)}</td>
                            <td style={{ textAlign: 'right' }}>
                              {hasSubmitted ? `PKR ${fmtNum(c.submitted_cash)}` : <span style={{ color: 'var(--text-dim)' }}>Uncounted</span>}
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              {cashVariance !== null ? (
                                <span style={{ fontWeight: 700, color: cashVariance === 0 ? 'var(--green)' : 'var(--red)' }}>
                                  {cashVariance === 0 ? 'Reconciled (0)' : `PKR ${fmtNum(cashVariance)}`}
                                </span>
                              ) : (
                                <span className="badge amber">Pending Count</span>
                              )}
                            </td>
                            <td style={{ textAlign: 'right' }}>{fmtNum(expStock)} pkts</td>
                            <td style={{ textAlign: 'right' }}>{subStock !== null && subStock !== undefined ? `${fmtNum(subStock)} pkts` : '—'}</td>
                            <td>
                              <span className={`badge ${c.status === 'Approved' ? 'green' : c.status === 'Variance_Flagged' ? 'red' : 'amber'}`}>
                                {c.status}
                              </span>
                            </td>
                            <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                              {c.status !== 'Approved' && (
                                <button
                                  className="btn"
                                  style={{ padding: '2px 8px', fontSize: 11, marginRight: 4 }}
                                  onClick={() => handleOpenReconcileModal(c)}
                                >
                                  Reconcile
                                </button>
                              )}
                              {c.status !== 'Approved' && canApprove && (
                                <button
                                  className="btn"
                                  style={{ padding: '2px 8px', fontSize: 11, background: 'var(--green-soft)', color: 'var(--green)', borderColor: 'var(--green)' }}
                                  onClick={() => handleApproveClosing(c.id)}
                                >
                                  Approve
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 14. AUDIT TRAIL REPORT */}
          {activeTab === 'audit' && (
            <div className="panel">
              <div className="section-head">
                <h2>Immutable Audit Log</h2>
                <span className="badge teal">{reportData.length} Recent Logs</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Performed By</th>
                      <th>Module / Table</th>
                      <th>Action</th>
                      <th>Record ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.length === 0 ? (
                      <tr><td colSpan="5" style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>No audit logs recorded yet.</td></tr>
                    ) : (
                      reportData.map(l => (
                        <tr key={l.id}>
                          <td style={{ fontSize: 11 }}>{fmtDateTime(l.created_at)}</td>
                          <td><strong>{l.profiles?.full_name || 'System'}</strong></td>
                          <td style={{ fontFamily: 'monospace', fontSize: 11 }}>{l.table_name}</td>
                          <td>
                            <span className={`badge ${l.action === 'INSERT' ? 'green' : l.action === 'UPDATE' ? 'amber' : 'red'}`}>
                              {l.action}
                            </span>
                          </td>
                          <td style={{ fontSize: 11, color: 'var(--text-dim)' }}>{l.record_id || '—'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* RECONCILE MODAL */}
      {reconcileModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: 20
        }}>
          <div className="panel" style={{ width: '100%', maxWidth: 500, boxShadow: '0 20px 50px rgba(0,0,0,0.2)' }}>
            <div className="section-head" style={{ marginBottom: 16 }}>
              <h2>Physical Daily Reconciliation</h2>
              <span className="badge amber">{fmtDate(reconcileModal.closing_date)}</span>
            </div>
            
            <div style={{ marginBottom: 16, fontSize: 13 }}>
              Party: <strong>{reconcileModal.distributors?.name || reconcileModal.salesmen?.profiles?.full_name || '—'}</strong>
            </div>

            <div className="grid g2" style={{ marginBottom: 16 }}>
              <div className="panel-flat">
                <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>System Expected Cash</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--teal)' }}>
                  PKR {fmtNum(reconcileModal.expected_cash)}
                </div>
              </div>
              <div className="panel-flat">
                <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>System Expected Stock</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--teal)' }}>
                  {fmtNum(reconcileModal.expected_stock?.packets ?? reconcileModal.expected_stock)} pkts
                </div>
              </div>
            </div>

            <div className="form-grid" style={{ marginBottom: 16 }}>
              <div className="field">
                <label>Actual Cash Counted (PKR)</label>
                <input
                  type="number"
                  value={submittedCash}
                  onChange={e => setSubmittedCash(e.target.value)}
                  placeholder="e.g. 15000"
                />
              </div>

              <div className="field">
                <label>Actual Stock Counted (Packets)</label>
                <input
                  type="number"
                  value={submittedStock}
                  onChange={e => setSubmittedStock(e.target.value)}
                  placeholder="e.g. 100"
                />
              </div>

              <div className="field" style={{ gridColumn: '1/-1' }}>
                <label>Reconciliation Notes / Variance Reason</label>
                <textarea
                  rows={2}
                  value={reconcileNotes}
                  onChange={e => setReconcileNotes(e.target.value)}
                  placeholder="Enter explanation if variance exists"
                />
              </div>
            </div>

            {/* LIVE VARIANCE PREVIEW */}
            {submittedCash !== '' && (
              <div style={{
                padding: '10px 14px',
                borderRadius: 6,
                marginBottom: 16,
                fontSize: 12.5,
                background: (Number(submittedCash) - Number(reconcileModal.expected_cash || 0)) === 0 ? 'var(--green-soft)' : 'var(--red-soft)',
                color: (Number(submittedCash) - Number(reconcileModal.expected_cash || 0)) === 0 ? 'var(--green)' : 'var(--red)'
              }}>
                Cash Variance: PKR {fmtNum(Number(submittedCash) - Number(reconcileModal.expected_cash || 0))}
                {(Number(submittedCash) - Number(reconcileModal.expected_cash || 0)) === 0 ? ' (Exact match)' : ' (Discrepancy will be flagged)'}
              </div>
            )}

            <div className="btn-row" style={{ justifyContent: 'flex-end' }}>
              <button className="btn ghost" onClick={() => setReconcileModal(null)} disabled={submittingReconcile}>
                Cancel
              </button>
              <button className="btn primary" onClick={handleSaveReconciliation} disabled={submittingReconcile || submittedCash === ''}>
                {submittingReconcile ? 'Saving...' : 'Submit Reconciliation'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

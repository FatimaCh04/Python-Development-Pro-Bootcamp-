import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchDashboardMetrics } from '../lib/db';

const fmtNum = (n) => Number(n || 0).toLocaleString();
const fmtDate = (d) => {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' });
};

// SVG Icons
const IconBox = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>;
const IconMoney = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/></svg>;
const IconTrend = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>;
const IconRotate = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/></svg>;
const IconAlert = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>;
const IconAccount = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>;
const IconPercent = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>;

function KPICard({ title, value, unit, context, icon, color = 'teal', accent = false, onClick = null }) {
  return (
    <div 
      className={`kpi-card ${accent ? `accent-${color}` : ''}`} 
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div className="kpi-label">{title}</div>
          <div className={`kpi-icon ${color}`}>
            {icon}
          </div>
        </div>
        <div className="kpi-value-row">
          <div className="kpi-value">{value}</div>
          <div className="kpi-unit">{unit}</div>
        </div>
      </div>
      <div className="kpi-context">{context}</div>
    </div>
  );
}

export default function OverviewPage({ navigate = () => {} }) {
  const { user, role } = useAuth();
  
  // Date selector (default to today)
  const todayStr = new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState(todayStr);
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const metrics = await fetchDashboardMetrics(selectedDate);
        if (mounted) setData(metrics);
      } catch (err) {
        console.error(err);
        if (mounted) setError('Failed to load dashboard data. Please try again.');
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, [selectedDate]);

  return (
    <div className="dashboard-container">
      {/* HEADER */}
      <div className="dash-header">
        <div>
          <h1>Dashboard</h1>
          <p>Real-time transaction-derived overview · Selected Date: <strong>{fmtDate(selectedDate)}</strong></p>
        </div>
        <div className="dash-date-control">
          <input 
            type="date" 
            value={selectedDate} 
            onChange={(e) => setSelectedDate(e.target.value || todayStr)}
          />
          <button 
            className="btn-today" 
            onClick={() => setSelectedDate(todayStr)}
          >
            Today
          </button>
        </div>
      </div>

      {loading ? (
        <div className="panel" style={{ padding: 60, textAlign: 'center', color: 'var(--text-dim)', border: 'none', background: 'transparent' }}>
          <div className="splash-loader" style={{ minHeight: 'auto', padding: 0, background: 'transparent' }}>
            <div className="brand-mark" style={{ width: 44, height: 44, fontSize: 16 }}>EW</div>
            <p>Loading business metrics...</p>
          </div>
        </div>
      ) : error ? (
        <div className="panel" style={{ padding: 20, color: 'var(--red)', background: 'var(--red-soft)', border: '1px solid #f0c8c4' }}>
          {error}
        </div>
      ) : data ? (
        <>
          {/* NINE BUSINESS METRICS GRID */}
          <div className="dash-section" style={{ marginTop: 0 }}>
            <div className="dash-section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2>Core Business Metrics</h2>
                <p>Derived strictly from approved transactions · Distinct daily and cumulative balances</p>
              </div>
              <button className="btn ghost" style={{ fontSize: 12 }} onClick={() => navigate('reports')}>
                View Detailed Reports →
              </button>
            </div>

            <div className="grid g3">
              {/* 1. Company Saleable Stock (Packets) */}
              <KPICard 
                title="1. Company Saleable Stock" 
                value={fmtNum(data.companyStock)} 
                unit="pkts" 
                context="Cumulative physical stock available for issue" 
                icon={<IconBox/>} 
                color="teal" 
                accent={true} 
                onClick={() => navigate('stock')}
              />

              {/* 2. Sales (PKR) */}
              <KPICard 
                title="2. Sales" 
                value={fmtNum(data.salesAmount)} 
                unit="PKR" 
                context={`Daily: ${fmtNum(data.salesSelectedDatePackets || 0)} pkts · Cumulative: PKR ${fmtNum(data.salesCumulativeAmount || 0)}`} 
                icon={<IconMoney/>} 
                color="green" 
                accent={true} 
                onClick={() => navigate('sales')}
              />

              {/* 3. Distributors Outstanding (PKR) */}
              <KPICard 
                title="3. Distributors Outstanding" 
                value={fmtNum(data.distributorsOutstanding)} 
                unit="PKR" 
                context={`Cumulative unrecovered balance (Total Sales − Recoveries)`} 
                icon={<IconTrend/>} 
                color="amber" 
                accent={true} 
                onClick={() => navigate('distributors')}
              />

              {/* 4. Expenses (PKR) */}
              <KPICard 
                title="4. Expenses" 
                value={fmtNum(data.expensesAmount)} 
                unit="PKR" 
                context={`Daily approved on ${fmtDate(selectedDate)} · Cumulative: PKR ${fmtNum(data.expensesCumulativeAmount || 0)}`} 
                icon={<IconMoney/>} 
                color="red" 
                accent={false} 
                onClick={() => navigate('expenses')}
              />

              {/* 5. Advertisement Balance (PKR) */}
              <KPICard 
                title="5. Advertisement Balance" 
                value={fmtNum(data.advertisementBalance)} 
                unit="PKR" 
                context={`Cumulative fund balance (Opening + Allocations − Expenses)`} 
                icon={<IconAccount/>} 
                color="teal" 
                accent={false} 
                onClick={() => navigate('reports')}
              />

              {/* 6. Welfare Balance (PKR) */}
              <KPICard 
                title="6. Welfare Balance" 
                value={fmtNum(data.welfareBalance)} 
                unit="PKR" 
                context={`Cumulative fund balance (Opening + Allocations − Expenses)`} 
                icon={<IconAccount/>} 
                color="green" 
                accent={false} 
                onClick={() => navigate('reports')}
              />

              {/* 7. Distributors Commission (PKR) */}
              <KPICard 
                title="7. Distributors Commission" 
                value={fmtNum(data.commissionAmount)} 
                unit="PKR" 
                context={`Earned on ${fmtDate(selectedDate)} · Outstanding Payable: PKR ${fmtNum(data.commissionPayable)}`} 
                icon={<IconPercent/>} 
                color="teal" 
                accent={false} 
                onClick={() => navigate('settlement')}
              />

              {/* 8. Distributors Return Stock (Packets) */}
              <KPICard 
                title="8. Distributors Return Stock" 
                value={fmtNum(data.distReturnStock)} 
                unit="pkts" 
                context={`Cumulative approved returns · Daily: ${fmtNum(data.distReturnSelectedDate || 0)} pkts`} 
                icon={<IconRotate/>} 
                color="amber" 
                accent={false} 
                onClick={() => navigate('stock')}
              />

              {/* 9. Damage Return Stock (Packets) */}
              <KPICard 
                title="9. Damage Return Stock" 
                value={fmtNum(data.damageReturnStock)} 
                unit="pkts" 
                context={`Cumulative damaged returns (isolated from saleable stock)`} 
                icon={<IconAlert/>} 
                color="red" 
                accent={false} 
                onClick={() => navigate('stock')}
              />
            </div>
          </div>

          {/* QUICK AUDIT & LEDGER SUMMARY NOTE */}
          <div className="panel" style={{ marginTop: 24, padding: '16px 20px', background: '#FAF9F5', border: '1px solid var(--line)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
              <div style={{ fontSize: 12.5, color: 'var(--text-dim)' }}>
                🔒 <strong>Strict Reconciliation Notice:</strong> All metrics are computed strictly from verified database records.
                Rates for Commission, Advertisement, and Welfare use frozen transaction snapshots.
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn" style={{ fontSize: 12, padding: '5px 12px' }} onClick={() => navigate('reports')}>
                  Financial Reports
                </button>
                <button className="btn primary" style={{ fontSize: 12, padding: '5px 12px' }} onClick={() => navigate('audit')}>
                  Audit Trail
                </button>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

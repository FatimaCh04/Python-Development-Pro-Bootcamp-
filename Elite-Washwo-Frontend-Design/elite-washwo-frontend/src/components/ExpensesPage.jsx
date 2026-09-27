import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchExpenses, submitExpense, updateExpenseStatus, fetchExpenseSummary, fetchDistributors } from '../lib/db';

const fmtNum = (n) => Number(n || 0).toLocaleString();
const fmtDate = (d) => {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};

// Simple UI wrapper for inline messages
const Msg = ({ msg }) => {
  if (!msg) return null;
  const isErr = msg.startsWith('err:');
  const text = msg.replace(/^(err:|ok:)/, '');
  return (
    <div className={`perm-message ${isErr ? 'err' : 'ok'}`} style={{ marginBottom: 14 }}>
      {text}
    </div>
  );
};

export default function ExpensesPage() {
  const { role, hasPermission } = useAuth();
  
  const [distributors, setDistributors] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState({});
  const [loadingList, setLoadingList] = useState(true);
  
  const [msg, setMsg] = useState('');
  const [saving, setSaving] = useState(false);

  // Form State
  const [form, setForm] = useState({
    expenseType: 'Distributor',
    distributorId: '',
    amount: '',
    accountDetail: '',
    tid: '',
    notes: '',
    head: ''
  });

  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');

  const loadData = async () => {
    setLoadingList(true);
    try {
      const [distRes, expRes, sumRes] = await Promise.all([
        fetchDistributors(),
        fetchExpenses({ type: typeFilter, status: statusFilter }),
        fetchExpenseSummary()
      ]);
      setDistributors(distRes);
      setExpenses(expRes);
      setSummary(sumRes);
    } catch(e) {
      console.error(e);
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [typeFilter, statusFilter]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (role === 'Manager' && !hasPermission('expenses.create')) {
      setMsg("err:Permission denied: You do not have 'expenses.create' permission.");
      return;
    }
    if (!form.expenseType || !form.amount) { 
      setMsg('err:Please fill all required fields.'); 
      return; 
    }
    if (form.expenseType === 'Distributor' && !form.distributorId) {
      setMsg('err:Please select a Distributor.');
      return;
    }
    if (Number(form.amount) <= 0) {
      setMsg('err:Amount must be greater than 0.');
      return;
    }

    setSaving(true); 
    setMsg('');
    try {
      await submitExpense({ ...form });
      setMsg('ok:Expense submitted successfully.');
      setForm({
        expenseType: 'Distributor',
        distributorId: '',
        amount: '',
        accountDetail: '',
        tid: '',
        notes: '',
        head: ''
      });
      loadData();
    } catch(e) { 
      setMsg('err:'+e.message); 
    } finally { 
      setSaving(false); 
    }
  };

  const handleStatus = async (id, status) => {
    if (status === 'Approved' && !hasPermission('expenses.approve')) {
      alert("Permission denied: You do not have 'expenses.approve' permission.");
      return;
    }
    try { 
      await updateExpenseStatus(id, status); 
      loadData(); 
    } catch(e) { 
      alert(e.message); 
    }
  };

  const selectedDist = form.distributorId ? distributors.find(d => d.id === form.distributorId) : null;

  // Client-side search filtering
  const query = searchTerm.trim().toLowerCase();
  const displayExpenses = expenses.filter(r => {
    if (!query) return true;
    return (
      (r.reference_number || '').toLowerCase().includes(query) ||
      (r.head || '').toLowerCase().includes(query) ||
      (r.distributors?.name || '').toLowerCase().includes(query) ||
      (r.distributors?.code || '').toLowerCase().includes(query) ||
      (r.salesmen?.profiles?.full_name || '').toLowerCase().includes(query) || // Historical search
      (r.category || '').toLowerCase().includes(query)
    );
  });

  return (
    <div className="dashboard-container">
      {/* SUMMARY */}
      <div className="grid g4" style={{ marginBottom: 20 }}>
        <div className="tile teal">
          <div className="bar"></div>
          <div className="label">Total Expenses This Month</div>
          <div className="num">PKR {fmtNum(summary.total)}</div>
        </div>
        <div className="tile amber">
          <div className="bar"></div>
          <div className="label">Distributor Expenses</div>
          <div className="num">PKR {fmtNum(summary.distributor)}</div>
        </div>
        <div className="tile green">
          <div className="bar"></div>
          <div className="label">Company Expenses</div>
          <div className="num">PKR {fmtNum(summary.company)}</div>
        </div>
        <div className="tile red">
          <div className="bar"></div>
          <div className="label">Office & Others</div>
          <div className="num">PKR {fmtNum(summary.office + summary.others)}</div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        
        {/* FORM */}
        <div className="panel">
          <div className="section-head">
            <h2>Record Expense</h2>
          </div>
          <Msg msg={msg} />
          
          <form onSubmit={handleSubmit} className="form-grid">
            
            <div className="field">
              <label>Expense Type <span style={{color:'var(--red)'}}>*</span></label>
              <select 
                value={form.expenseType} 
                onChange={e => setForm({...form, expenseType: e.target.value, distributorId: ''})} 
                required
              >
                <option value="Distributor">Distributor</option>
                <option value="Company">Company</option>
                <option value="Office">Office</option>
                <option value="Others">Others</option>
              </select>
            </div>

            {form.expenseType === 'Distributor' && (
              <div className="field" style={{ background: '#F5F3ED', padding: 12, borderRadius: 8, border: '1px solid var(--line)' }}>
                <label>Select Distributor <span style={{color:'var(--red)'}}>*</span></label>
                <select 
                  value={form.distributorId} 
                  onChange={e => setForm({...form, distributorId: e.target.value})}
                  required
                >
                  <option value="">-- Choose --</option>
                  {distributors.map(d => (
                    <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
                  ))}
                </select>
                
                {selectedDist && (
                  <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-dim)' }}>
                    <div><strong>Code:</strong> {selectedDist.code}</div>
                    <div><strong>Name:</strong> {selectedDist.name}</div>
                    {selectedDist.id_card && <div><strong>ID Card:</strong> {selectedDist.id_card}</div>}
                    {selectedDist.phone && <div><strong>Phone No:</strong> {selectedDist.phone}</div>}
                  </div>
                )}
              </div>
            )}

            <div className="field">
              <label>Amount (PKR) <span style={{color:'var(--red)'}}>*</span></label>
              <input 
                type="number" 
                value={form.amount} 
                onChange={e => setForm({...form, amount: e.target.value})} 
                placeholder="0.00" 
                required 
              />
            </div>

            <div className="field">
              <label>Cash / Account Detail</label>
              <input 
                type="text" 
                value={form.accountDetail} 
                onChange={e => setForm({...form, accountDetail: e.target.value})} 
                placeholder="e.g., Cash, Meezan Bank..." 
              />
            </div>

            <div className="field">
              <label>TID (Transaction ID)</label>
              <input 
                type="text" 
                value={form.tid} 
                onChange={e => setForm({...form, tid: e.target.value})} 
                placeholder="Optional for cash" 
              />
            </div>

            <div className="field">
              <label>Head</label>
              <input 
                type="text" 
                value={form.head} 
                onChange={e => setForm({...form, head: e.target.value})} 
                placeholder="e.g., Advertisement, Welfare, Fuel..." 
              />
            </div>

            <div className="field" style={{ gridColumn: '1/-1' }}>
              <label>Notes</label>
              <textarea 
                value={form.notes} 
                onChange={e => setForm({...form, notes: e.target.value})} 
                placeholder="Additional details..." 
                rows="3"
                style={{ resize: 'vertical', width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--line)', fontFamily: 'inherit' }}
              />
            </div>

            <div style={{ gridColumn: '1/-1', marginTop: 16 }}><button type="submit" className="btn" disabled={saving}>
              {saving ? 'Submitting...' : 'Submit Expense'}
            </button></div>
          </form>
        </div>

        {/* LIST */}
        <div className="panel" style={{ overflowX: 'auto' }}>
          <div className="section-head" style={{ marginBottom: 16 }}>
            <h2>Expense Ledger</h2>
            
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <div className="search-box">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
                <input 
                  type="text" 
                  placeholder="Search reference, head..." 
                  value={searchTerm} 
                  onChange={e => setSearchTerm(e.target.value)} 
                  style={{ border: 'none', background: 'transparent', outline: 'none', width: 160 }}
                />
              </div>
              <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--line)', fontSize: 13 }}>
                <option value="All">All Types</option>
                <option value="Distributor">Distributor</option>
                <option value="Company">Company</option>
                <option value="Office">Office</option>
                <option value="Others">Others</option>
              </select>
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--line)', fontSize: 13 }}>
                <option value="All">All Status</option>
                <option value="Pending">Pending</option>
                <option value="Approved">Approved</option>
                <option value="Rejected">Rejected</option>
              </select>
            </div>
          </div>

          <table style={{ minWidth: 700 }}>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Date</th>
                <th>Type / Cat</th>
                <th>Distributor / SM</th>
                <th>Head</th>
                <th className="num-cell">Amount</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loadingList ? (
                <tr><td colSpan="8" style={{ textAlign: 'center', padding: 20 }}>Loading...</td></tr>
              ) : displayExpenses.length === 0 ? (
                <tr><td colSpan="8" style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>No expenses found.</td></tr>
              ) : (
                displayExpenses.map(r => {
                  const distName = r.distributors ? `${r.distributors.code} - ${r.distributors.name}` : null;
                  const smName = r.salesmen?.profiles?.full_name; // Legacy
                  
                  return (
                    <tr key={r.id}>
                      <td style={{ fontSize: 12, fontFamily: 'monospace' }}>{r.reference_number}</td>
                      <td>{fmtDate(r.expense_date)}</td>
                      <td>{r.category || '—'}</td>
                      <td>
                        {distName ? <span style={{ fontWeight: 600 }}>{distName}</span> : 
                         smName ? <span style={{ color: 'var(--text-dim)' }}>{smName} (Legacy)</span> : '—'}
                      </td>
                      <td>{r.head || '—'}</td>
                      <td className="num-cell" style={{ fontWeight: 600 }}>{fmtNum(r.amount)}</td>
                      <td>
                        <span className={`badge ${r.status === 'Approved' ? 'green' : r.status === 'Rejected' ? 'red' : 'amber'}`}>
                          {r.status}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {r.status === 'Pending' && role !== 'Salesman' && (
                          <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                            <button className="btn" style={{ padding: '4px 8px', fontSize: 11 }} onClick={() => handleStatus(r.id, 'Approved')}>Approve</button>
                            <button className="btn ghost" style={{ padding: '4px 8px', fontSize: 11, color: 'var(--red)' }} onClick={() => handleStatus(r.id, 'Rejected')}>Reject</button>
                          </div>
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
    </div>
  );
}

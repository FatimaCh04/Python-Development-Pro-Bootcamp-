import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchExpenses, submitExpense, updateExpenseStatus, fetchExpenseSummary, fetchDistributors, fetchPersons } from '../lib/db';

const fmtNum = (n) => Number(n || 0).toLocaleString();
const fmtDate = (d) => {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};
const todayISO = () => new Date().toISOString().split('T')[0];

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

const COMMON_HEADS = [
  'Advertisement — Billboards & Banners',
  'Advertisement — Social Media & Digital',
  'Advertisement — Promotional Samples',
  'Welfare — Worker Aid & Support',
  'Welfare — Medical / Emergency',
  'Distributor — Fuel & Transport Subsidy',
  'Distributor — Delivery Route Allowance',
  'Company — Factory Electricity / Fuel',
  'Company — Machinery Maintenance',
  'Company — Warehouse / Factory Rent',
  'Office — Stationery & Supplies',
  'Office — Tea & Refreshments',
  'Office — Internet & Communication'
];

export default function ExpensesPage({ searchTerm = '' }) {
  const { role, hasPermission } = useAuth();
  
  const [distributors, setDistributors] = useState([]);
  const [persons, setPersons] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState({
    total: 0,
    approvedTotal: 0,
    pendingTotal: 0,
    distributor: 0,
    company: 0,
    office: 0,
    advertisement: 0,
    welfare: 0,
    others: 0
  });
  const [loadingList, setLoadingList] = useState(true);
  
  const [msg, setMsg] = useState('');
  const [saving, setSaving] = useState(false);

  // Form State
  const [form, setForm] = useState({
    expenseType: 'Distributor',
    distributorId: '',
    personId: '',
    expenseDate: todayISO(),
    amount: '',
    paymentMethod: 'Cash',
    accountDetail: '',
    tid: '',
    head: '',
    notes: ''
  });

  // Search & Filter State
  const [localSearch, setLocalSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');

  const loadData = async () => {
    setLoadingList(true);
    try {
      const [distRes, expRes, sumRes, persRes] = await Promise.all([
        fetchDistributors(),
        fetchExpenses({ type: typeFilter, status: statusFilter }),
        fetchExpenseSummary(),
        fetchPersons ? fetchPersons().catch(() => []) : Promise.resolve([])
      ]);
      setDistributors(distRes || []);
      setExpenses(expRes || []);
      setSummary(sumRes || {});
      setPersons(persRes || []);
    } catch(e) {
      console.error(e);
      setMsg('err:Failed to load expenses data.');
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
      setMsg('ok:Expense recorded successfully in Pending status.');
      setForm({
        expenseType: 'Distributor',
        distributorId: '',
        personId: '',
        expenseDate: todayISO(),
        amount: '',
        paymentMethod: 'Cash',
        accountDetail: '',
        tid: '',
        head: '',
        notes: ''
      });
      await loadData();
    } catch(e) { 
      setMsg('err:' + e.message); 
    } finally { 
      setSaving(false); 
    }
  };

  const handleStatus = async (id, status) => {
    if (status === 'Approved' && role === 'Manager' && !hasPermission('expenses.approve')) {
      alert("Permission denied: You do not have 'expenses.approve' permission.");
      return;
    }
    try { 
      await updateExpenseStatus(id, status); 
      setMsg(`ok:Expense marked as ${status}.`);
      await loadData(); 
    } catch(e) { 
      alert(e.message); 
    }
  };

  const selectedDist = form.distributorId ? distributors.find(d => d.id === form.distributorId) : null;

  // Client-side search filtering
  const query = (localSearch || searchTerm).trim().toLowerCase();
  const displayExpenses = expenses.filter(r => {
    if (!query) return true;
    return (
      (r.reference_number || '').toLowerCase().includes(query) ||
      (r.head || '').toLowerCase().includes(query) ||
      (r.category || '').toLowerCase().includes(query) ||
      (r.distributors?.name || '').toLowerCase().includes(query) ||
      (r.distributors?.code || '').toLowerCase().includes(query) ||
      (r.persons?.name || '').toLowerCase().includes(query) ||
      (r.salesmen?.profiles?.full_name || '').toLowerCase().includes(query) ||
      (r.account_detail || '').toLowerCase().includes(query) ||
      (r.tid || '').toLowerCase().includes(query) ||
      (r.description || '').toLowerCase().includes(query)
    );
  });

  return (
    <div className="dashboard-container">
      {/* SUMMARY TILES */}
      <div className="grid g4" style={{ marginBottom: 20 }}>
        <div className="tile teal">
          <div className="bar"></div>
          <div className="label">Approved Expenses This Month</div>
          <div className="num">PKR {fmtNum(summary.total)}</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
            Pending: PKR {fmtNum(summary.pendingTotal || 0)}
          </div>
        </div>
        <div className="tile amber">
          <div className="bar"></div>
          <div className="label">Distributor Expenses</div>
          <div className="num">PKR {fmtNum(summary.distributor)}</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Approved total</div>
        </div>
        <div className="tile green">
          <div className="bar"></div>
          <div className="label">Company & Office</div>
          <div className="num">PKR {fmtNum((summary.company || 0) + (summary.office || 0))}</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Operational costs</div>
        </div>
        <div className="tile red">
          <div className="bar"></div>
          <div className="label">Advertisement & Welfare</div>
          <div className="num">PKR {fmtNum((summary.advertisement || 0) + (summary.welfare || 0))}</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Program accounts</div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        
        {/* RECORD EXPENSE FORM */}
        <div className="panel">
          <div className="section-head">
            <h2>Record Expense</h2>
            <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
              Note: Only approved expenses impact Profit &amp; Loss totals.
            </span>
          </div>
          <Msg msg={msg} />
          
          <form onSubmit={handleSubmit} className="form-grid">
            
            <div className="field">
              <label>Expense Category <span style={{color:'var(--red)'}}>*</span></label>
              <select 
                value={form.expenseType} 
                onChange={e => setForm({...form, expenseType: e.target.value, distributorId: '', personId: ''})} 
                required
              >
                <option value="Distributor">Distributor</option>
                <option value="Company">Company</option>
                <option value="Office">Office</option>
                <option value="Advertisement">Advertisement</option>
                <option value="Welfare">Welfare</option>
                <option value="Others">Others</option>
              </select>
            </div>

            <div className="field">
              <label>Expense Date <span style={{color:'var(--red)'}}>*</span></label>
              <input 
                type="date" 
                value={form.expenseDate} 
                onChange={e => setForm({...form, expenseDate: e.target.value})} 
                required 
              />
            </div>

            {form.expenseType === 'Distributor' && (
              <div className="field" style={{ gridColumn: '1 / -1', background: '#F5F3ED', padding: 12, borderRadius: 8, border: '1px solid var(--line)' }}>
                <label>Select Distributor <span style={{color:'var(--red)'}}>*</span></label>
                <select 
                  value={form.distributorId} 
                  onChange={e => setForm({...form, distributorId: e.target.value})}
                  required
                >
                  <option value="">-- Choose Distributor --</option>
                  {distributors.filter(d => d.is_active).map(d => (
                    <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
                  ))}
                </select>
                
                {selectedDist && (
                  <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-dim)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                    <div><strong>Code:</strong> {selectedDist.code}</div>
                    <div><strong>Name:</strong> {selectedDist.name}</div>
                    {selectedDist.id_card && <div><strong>CNIC:</strong> {selectedDist.id_card}</div>}
                    {selectedDist.phone && <div><strong>Phone:</strong> {selectedDist.phone}</div>}
                  </div>
                )}
              </div>
            )}

            <div className="field">
              <label>Amount (PKR) <span style={{color:'var(--red)'}}>*</span></label>
              <input 
                type="number" 
                min="1"
                step="0.01"
                value={form.amount} 
                onChange={e => setForm({...form, amount: e.target.value})} 
                placeholder="0.00" 
                required 
              />
            </div>

            <div className="field">
              <label>Payment Method</label>
              <select 
                value={form.paymentMethod} 
                onChange={e => setForm({...form, paymentMethod: e.target.value})}
              >
                <option value="Cash">Cash</option>
                <option value="Bank Transfer">Bank Transfer</option>
                <option value="Cheque">Cheque</option>
                <option value="Online">Online / Wallet</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="field">
              <label>Account / Cash Detail</label>
              <input 
                type="text" 
                value={form.accountDetail} 
                onChange={e => setForm({...form, accountDetail: e.target.value})} 
                placeholder="e.g., Petty Cash, Meezan Bank..." 
              />
            </div>

            <div className="field">
              <label>TID / Cheque #</label>
              <input 
                type="text" 
                value={form.tid} 
                onChange={e => setForm({...form, tid: e.target.value})} 
                placeholder="Transaction reference / cheque no." 
              />
            </div>

            <div className="field" style={{ gridColumn: '1 / -1' }}>
              <label>Expense Head / Sub-Category</label>
              <input 
                type="text" 
                list="head-suggestions"
                value={form.head} 
                onChange={e => setForm({...form, head: e.target.value})} 
                placeholder="e.g., Promotional Samples, Fuel, Rent, Stationery..." 
              />
              <datalist id="head-suggestions">
                {COMMON_HEADS.map(h => <option key={h} value={h} />)}
              </datalist>
            </div>

            <div className="field" style={{ gridColumn: '1 / -1' }}>
              <label>Description / Notes</label>
              <textarea 
                value={form.notes} 
                onChange={e => setForm({...form, notes: e.target.value})} 
                placeholder="Explanation of expense and verification details..." 
                rows="2"
                style={{ resize: 'vertical', width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--line)', fontFamily: 'inherit' }}
              />
            </div>

            <div style={{ gridColumn: '1 / -1', marginTop: 10 }}>
              <button type="submit" className="btn primary" disabled={saving}>
                {saving ? 'Submitting...' : 'Submit Expense for Approval'}
              </button>
            </div>
          </form>
        </div>

        {/* EXPENSE LEDGER */}
        <div className="panel" style={{ overflowX: 'auto' }}>
          <div className="section-head" style={{ marginBottom: 16 }}>
            <h2>Expense Ledger</h2>
            
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
              <div className="search-box">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
                <input 
                  type="text" 
                  placeholder="Search reference, head, payee..." 
                  value={localSearch} 
                  onChange={e => setLocalSearch(e.target.value)} 
                  style={{ border: 'none', background: 'transparent', outline: 'none', width: 170 }}
                />
              </div>
              <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--line)', fontSize: 13 }}>
                <option value="All">All Categories</option>
                <option value="Distributor">Distributor</option>
                <option value="Company">Company</option>
                <option value="Office">Office</option>
                <option value="Advertisement">Advertisement</option>
                <option value="Welfare">Welfare</option>
                <option value="Others">Others</option>
              </select>
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--line)', fontSize: 13 }}>
                <option value="All">All Status</option>
                <option value="Pending">Pending</option>
                <option value="Approved">Approved</option>
                <option value="Cancelled">Cancelled</option>
                <option value="Rejected">Rejected</option>
              </select>
            </div>
          </div>

          <table style={{ minWidth: 850 }}>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Date</th>
                <th>Category</th>
                <th>Entity / Payee</th>
                <th>Head / Description</th>
                <th>Payment Detail</th>
                <th className="num-cell">Amount</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loadingList ? (
                <tr><td colSpan="9" style={{ textAlign: 'center', padding: 20 }}>Loading expenses...</td></tr>
              ) : displayExpenses.length === 0 ? (
                <tr><td colSpan="9" style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>No expenses found.</td></tr>
              ) : (
                displayExpenses.map(r => {
                  const distName = r.distributors ? `${r.distributors.code} — ${r.distributors.name}` : null;
                  const personName = r.persons?.name ? `${r.persons.name} (${r.persons.category || r.persons.code || 'Person'})` : null;
                  const smName = r.salesmen?.profiles?.full_name;
                  const isPersonLinked = !!r.originating_ledger_entry_id;
                  
                  return (
                    <tr key={r.id}>
                      <td style={{ fontSize: 12, fontFamily: 'monospace', fontWeight: 600 }}>{r.reference_number}</td>
                      <td>{fmtDate(r.expense_date)}</td>
                      <td>
                        <span className="badge" style={{ fontSize: 11 }}>{r.category || 'General'}</span>
                      </td>
                      <td>
                        {distName ? <span style={{ fontWeight: 600, color: 'var(--teal)' }}>{distName}</span> : 
                         personName ? <span>{personName}</span> :
                         smName ? <span style={{ color: 'var(--text-dim)' }}>{smName} (Legacy)</span> : '—'}
                        {isPersonLinked && (
                          <div style={{ marginTop: 2 }}>
                            <span className="badge teal" style={{ fontSize: 9, padding: '2px 4px' }}>Person Payment</span>
                          </div>
                        )}
                      </td>
                      <td>
                        <div style={{ fontWeight: 500 }}>{r.head || '—'}</div>
                        {r.description && <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{r.description}</div>}
                      </td>
                      <td style={{ fontSize: 12 }}>
                        <div>{r.payment_method || 'Cash'}</div>
                        {(r.account_detail || r.tid) && (
                          <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                            {r.account_detail} {r.tid ? `(TID: ${r.tid})` : ''}
                          </div>
                        )}
                      </td>
                      <td className="num-cell" style={{ fontWeight: 700, fontSize: 13 }}>
                        PKR {fmtNum(r.amount)}
                      </td>
                      <td>
                        <span className={`badge ${r.status === 'Approved' ? 'green' : r.status === 'Cancelled' ? 'gray' : r.status === 'Rejected' ? 'red' : 'amber'}`}>
                          {r.status}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {isPersonLinked ? (
                          <span style={{ fontSize: 11, color: 'var(--text-dim)', fontStyle: 'italic' }}>
                            Linked Payment
                          </span>
                        ) : (
                          <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                            {r.status === 'Pending' && (role === 'Super_Admin' || (role === 'Manager' && hasPermission('expenses.approve'))) && (
                              <button 
                                className="btn" 
                                style={{ padding: '3px 8px', fontSize: 11, background: 'var(--teal)', color: '#fff' }} 
                                onClick={() => handleStatus(r.id, 'Approved')}
                              >
                                Approve
                              </button>
                            )}
                            {r.status === 'Pending' && (
                              <button 
                                className="btn ghost" 
                                style={{ padding: '3px 8px', fontSize: 11, color: 'var(--red)' }} 
                                onClick={() => handleStatus(r.id, 'Cancelled')}
                              >
                                Cancel
                              </button>
                            )}
                            {r.status === 'Approved' && (role === 'Super_Admin') && (
                              <button 
                                className="btn ghost" 
                                style={{ padding: '3px 8px', fontSize: 11, color: 'var(--red)' }} 
                                onClick={() => handleStatus(r.id, 'Cancelled')}
                              >
                                Cancel
                              </button>
                            )}
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

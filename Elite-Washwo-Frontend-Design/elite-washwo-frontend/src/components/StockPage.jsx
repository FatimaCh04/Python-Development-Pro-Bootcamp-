import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchDistributors,
  fetchSalesmen,
  fetchProducts,
  fetchInventoryTransactions,
  fetchStockBalances,
  submitStockReturn,
  submitInventoryMovement,
  approveTransaction,
  cancelTransaction
} from '../lib/db';
import { formatPakistaniPhoneForWhatsApp } from '../lib/exportUtils';

const fmtNum  = (n) => Number(n || 0).toLocaleString();
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';
const todayISO = () => new Date().toISOString().split('T')[0];

function Msg({ msg }) {
  if (!msg) return null;
  const isErr = msg.startsWith('err:');
  return (
    <div style={{
      padding:'8px 12px', marginBottom:12, borderRadius:4, fontSize:12,
      background: isErr ? 'var(--red-soft)' : 'var(--green-soft)',
      color: isErr ? 'var(--red)' : 'var(--green)'
    }}>
      {msg.replace(/^(ok|err):/, '')}
    </div>
  );
}

function Pagination({ page, pageSize, total, onPageChange }) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;
  return (
    <div style={{ display: 'flex', gap: 8, marginTop: 14, alignItems: 'center', fontSize: 12 }}>
      <button className="btn" disabled={page === 1} onClick={() => onPageChange(page - 1)}>Prev</button>
      <span>Page {page} of {totalPages}</span>
      <button className="btn" disabled={page === totalPages} onClick={() => onPageChange(page + 1)}>Next</button>
    </div>
  );
}

export default function StockPage({ searchTerm = '' }) {
  const { role, user, hasPermission } = useAuth();
  
  // Data State
  const [distributors, setDistributors] = useState([]);
  const [salesmen, setSalesmen] = useState([]);
  const [products, setProducts] = useState([]);
  const [txns, setTxns] = useState([]);
  const [balances, setBalances] = useState({
    saleableStock: 0,
    issuedStock: 0,
    goodReturns: 0,
    damagedStock: 0,
    productionPurchases: 0,
    adjustments: 0
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  // Operation Tab: 'return' | 'issue' | 'production' | 'adjustment'
  const [opTab, setOpTab] = useState('return');

  // Return Form State — Distributor Return only
  const [distSearch, setDistSearch] = useState('');
  const [selDist, setSelDist] = useState(null);
  const [returnForm, setReturnForm] = useState({
    productId: '',
    packagingId: '',
    returnType: 'Distributor_Good_Return', // Good Return vs Damaged
    quantity: '',
    notes: ''
  });

  // Issue Stock Form State
  const [issueDistSearch, setIssueDistSearch] = useState('');
  const [selIssueDist, setSelIssueDist] = useState(null);
  const [issueForm, setIssueForm] = useState({
    productId: '',
    packagingId: '',
    quantity: '',
    notes: '',
    allowNegative: false
  });

  // Production Form State
  const [prodForm, setProdForm] = useState({
    productId: '',
    packagingId: '',
    type: 'Production', // 'Production' | 'Purchase'
    quantity: '',
    unitCost: '',
    notes: ''
  });

  // Adjustment Form State
  const [adjForm, setAdjForm] = useState({
    productId: '',
    packagingId: '',
    quantity: '',
    notes: ''
  });

  // Ledger Filter & Pagination State
  const [localSearch, setLocalSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const loadData = async () => {
    setLoading(true);
    try {
      const [d, s, p, t, b] = await Promise.all([
        fetchDistributors(),
        fetchSalesmen(),
        fetchProducts(),
        fetchInventoryTransactions(),
        fetchStockBalances()
      ]);
      setDistributors(d || []);
      setSalesmen(s || []);
      setProducts(p || []);
      setTxns(t || []);
      setBalances(b || {
        saleableStock: 0,
        issuedStock: 0,
        goodReturns: 0,
        damagedStock: 0,
        productionPurchases: 0,
        adjustments: 0
      });
    } catch (e) {
      console.error(e);
      setMsg('err:Failed to load stock balances.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [role, user]);

  const activeDistributors = distributors.filter(d => d.is_active);
  const filterDistList = (search) => {
    if (!search) return activeDistributors;
    const l = search.toLowerCase();
    return activeDistributors.filter(d =>
      d.code?.toLowerCase().includes(l) ||
      d.name?.toLowerCase().includes(l) ||
      d.id_card?.toLowerCase().includes(l) ||
      d.phone?.toLowerCase().includes(l)
    );
  };

  // ── SUBMIT RETURN ──────────────────────────────────────────────────────────
  const handleReturnSubmit = async (e) => {
    e.preventDefault();
    if (role === 'Manager' && !hasPermission('inventory.create') && !hasPermission('returns.create')) {
      setMsg("err:Permission denied: You do not have 'returns.create' permission.");
      return;
    }
    if (!selDist) {
      setMsg('err:Please select a distributor.'); return;
    }
    if (!returnForm.packagingId || !returnForm.quantity || Number(returnForm.quantity) < 1) {
      setMsg('err:Please select a packaging variant and enter valid quantity.'); return;
    }

    setSaving(true); setMsg('');
    try {
      const selProd = products.find(p => p.id === returnForm.productId);
      const pkgObj = selProd?.product_packaging?.find(pk => pk.id === returnForm.packagingId);
      const unit_cost = pkgObj?.product_prices?.[0]?.unit_cost || 0;

      await submitStockReturn({
        distributorId: selDist.id,
        salesmanId: null,
        packagingId: returnForm.packagingId,
        transaction_type: returnForm.returnType,
        quantity: returnForm.quantity,
        notes: returnForm.notes,
        unit_cost
      });
      
      setMsg('ok:Stock return recorded in Pending status. Enters stock upon approval.');
      setReturnForm({
        productId: '',
        packagingId: '',
        returnType: 'Distributor_Good_Return',
        quantity: '',
        notes: ''
      });
      setSelDist(null);
      setDistSearch('');
      await loadData();
    } catch(e) {
      setMsg('err:' + e.message);
    } finally {
      setSaving(false);
    }
  };

  // ── SUBMIT PHYSICAL STOCK ISSUE ───────────────────────────────────────────
  const handleIssueSubmit = async (e) => {
    e.preventDefault();
    if (!selIssueDist) { setMsg('err:Please select a recipient distributor.'); return; }
    if (!issueForm.packagingId || !issueForm.quantity || Number(issueForm.quantity) < 1) {
      setMsg('err:Please select a packaging variant and enter valid quantity.'); return;
    }

    setSaving(true); setMsg('');
    try {
      const selProd = products.find(p => p.id === issueForm.productId);
      const pkgObj = selProd?.product_packaging?.find(pk => pk.id === issueForm.packagingId);
      const unit_cost = pkgObj?.product_prices?.[0]?.unit_cost || 0;

      await submitInventoryMovement({
        transaction_type: 'Distributor_Issue',
        packagingId: issueForm.packagingId,
        quantity: issueForm.quantity,
        distributorId: selIssueDist.id,
        unit_cost,
        notes: issueForm.notes,
        status: 'Approved',
        isAuthorizedAdjustment: issueForm.allowNegative && role === 'Super_Admin'
      });

      setMsg('ok:Stock issued to distributor. Saleable company stock deducted.');
      setIssueForm({ productId: '', packagingId: '', quantity: '', notes: '', allowNegative: false });
      setSelIssueDist(null);
      setIssueDistSearch('');
      await loadData();
    } catch(e) {
      setMsg('err:' + e.message);
    } finally {
      setSaving(false);
    }
  };

  // ── SUBMIT PRODUCTION / PURCHASE ──────────────────────────────────────────
  const handleProdSubmit = async (e) => {
    e.preventDefault();
    if (!prodForm.packagingId || !prodForm.quantity || Number(prodForm.quantity) < 1) {
      setMsg('err:Please select a variant and valid quantity.'); return;
    }

    setSaving(true); setMsg('');
    try {
      await submitInventoryMovement({
        transaction_type: prodForm.type,
        packagingId: prodForm.packagingId,
        quantity: prodForm.quantity,
        unit_cost: prodForm.unitCost || 0,
        notes: prodForm.notes,
        status: 'Approved'
      });

      setMsg(`ok:${prodForm.type} recorded successfully. Saleable stock updated.`);
      setProdForm({ productId: '', packagingId: '', type: 'Production', quantity: '', unitCost: '', notes: '' });
      await loadData();
    } catch(e) {
      setMsg('err:' + e.message);
    } finally {
      setSaving(false);
    }
  };

  // ── SUBMIT ADJUSTMENT ─────────────────────────────────────────────────────
  const handleAdjSubmit = async (e) => {
    e.preventDefault();
    if (!adjForm.packagingId || !adjForm.quantity || Number(adjForm.quantity) === 0) {
      setMsg('err:Enter valid adjustment quantity (positive or negative).'); return;
    }
    if (!adjForm.notes?.trim()) {
      setMsg('err:Mandatory explanation/audit reason required for adjustments.'); return;
    }

    setSaving(true); setMsg('');
    try {
      await submitInventoryMovement({
        transaction_type: 'Adjustment',
        packagingId: adjForm.packagingId,
        quantity: adjForm.quantity,
        notes: adjForm.notes,
        status: 'Approved',
        isAuthorizedAdjustment: true
      });

      setMsg('ok:Stock adjustment recorded and audited.');
      setAdjForm({ productId: '', packagingId: '', quantity: '', notes: '' });
      await loadData();
    } catch(e) {
      setMsg('err:' + e.message);
    } finally {
      setSaving(false);
    }
  };

  // ── APPROVE & CANCEL ──────────────────────────────────────────────────────
  const handleApprove = async (id) => {
    if (!hasPermission('inventory.approve') && !hasPermission('returns.approve')) {
      alert("Permission denied: You do not have 'inventory.approve' permission.");
      return;
    }
    try { 
      await approveTransaction(id); 
      setMsg('ok:Transaction approved. Stock balances updated.');
      await loadData(); 
    } catch(e) { 
      alert(e.message); 
    }
  };

  const handleCancel = async (id) => {
    const reason = window.prompt('Enter reason for cancelling this stock movement:');
    if (reason === null) return;
    try {
      await cancelTransaction(id, reason);
      setMsg('ok:Transaction marked as Cancelled. Stock reversed.');
      await loadData();
    } catch (e) {
      alert(e.message);
    }
  };

  // ── RECEIPT ACTIONS ───────────────────────────────────────────────────────
  const handleWhatsApp = (r) => {
    const isDist = !!r.distributor_id;
    const distObj = isDist 
      ? ((Array.isArray(r.distributors) ? r.distributors[0] : r.distributors) || distributors.find(d => d.id === r.distributor_id) || null)
      : null;

    let targetPhone = null;
    let entityName = 'Unknown';
    let entityLabel = isDist ? 'Distributor' : 'Salesman';

    if (isDist) {
      if (!distObj) {
        const warn = 'Cannot open WhatsApp: No distributor is linked to this transaction.';
        setMsg('err:' + warn);
        if (typeof alert === 'function') alert(warn);
        return;
      }
      entityName = distObj.name || 'Unknown';
      targetPhone = formatPakistaniPhoneForWhatsApp(distObj.phone);
      if (!targetPhone) {
        const warn = `Cannot open WhatsApp: Distributor ${distObj.name} has no valid registered phone number.`;
        setMsg('err:' + warn);
        if (typeof alert === 'function') alert(warn);
        return;
      }
    } else {
      entityName = r.salesmen?.profiles?.full_name || 'Unknown';
      targetPhone = formatPakistaniPhoneForWhatsApp(r.salesmen?.profiles?.phone || r.salesmen?.phone);
      if (!targetPhone) {
        const warn = `Cannot open WhatsApp: Salesman ${entityName} has no valid registered phone number.`;
        setMsg('err:' + warn);
        if (typeof alert === 'function') alert(warn);
        return;
      }
    }

    setMsg('');
    const text = encodeURIComponent(
      `*Elite Wash — Stock Movement*\n` +
      `Ref: ${r.reference_number}\n` +
      `Date: ${fmtDate(r.transaction_date)}\n` +
      `Type: ${r.transaction_type.replace(/_/g, ' ')}\n` +
      `${entityLabel}: ${entityName}\n` +
      `Product: ${r.product_packaging?.products?.name || ''} - ${r.product_packaging?.name || ''}\n` +
      `Quantity: ${r.quantity} pkts\n` +
      `Status: ${r.status}\n` +
      (r.notes ? `Notes: ${r.notes}` : '')
    );
    window.open(`https://wa.me/${targetPhone}?text=${text}`, '_blank');
  };

  const handlePrint = (r) => {
    const isDist = !!r.distributor_id;
    const entityLabel = isDist ? 'Distributor' : 'Salesman';
    const entityName = isDist 
      ? `${r.distributors?.name || ''} (${r.distributors?.code || ''})`
      : `${r.salesmen?.profiles?.full_name || ''}`;

    const win = window.open('', '_blank');
    win.document.write(`<html><head><title>${r.reference_number}</title>
      <style>body{font-family:sans-serif;padding:24px}table{width:100%;border-collapse:collapse;margin-top:14px}td,th{border:1px solid #ccc;padding:8px;font-size:13px}th{background:#f5f5f5;text-align:left}</style></head>
      <body>
        <h2>Elite Wash — Inventory Voucher</h2>
        <p><strong>Ref #:</strong> ${r.reference_number} &nbsp; <strong>Date:</strong> ${fmtDate(r.transaction_date)} &nbsp; <strong>Status:</strong> ${r.status}</p>
        <p><strong>Movement Type:</strong> ${r.transaction_type.replace(/_/g, ' ')}</p>
        ${(r.distributor_id || r.salesman_id) ? `<p><strong>${entityLabel}:</strong> ${entityName}</p>` : ''}
        ${r.notes ? `<p><strong>Notes:</strong> ${r.notes}</p>` : ''}
        <table>
          <tr><th>Product Variant</th><th>Category</th><th>Quantity</th></tr>
          <tr>
            <td>${r.product_packaging?.products?.name || ''} - ${r.product_packaging?.name || ''}</td>
            <td>${r.category}</td>
            <td><strong>${r.quantity} pkts</strong></td>
          </tr>
        </table>
        <br/><p style="font-size:11px;color:#888">Elite Wash ERP — Balances strictly transaction-derived. No manual overwrite.</p>
      </body></html>`);
    win.document.close(); win.print();
  };

  // ── FILTERING & PAGINATION ────────────────────────────────────────────────
  const query = (localSearch || searchTerm).trim().toLowerCase();
  const filteredTxns = txns.filter(r => {
    if (statusFilter !== 'All' && r.status !== statusFilter) return false;
    
    if (categoryFilter === 'Returns' && !r.transaction_type?.includes('Return')) return false;
    if (categoryFilter === 'Issues' && !r.transaction_type?.includes('Issue')) return false;
    if (categoryFilter === 'Production' && !['Production', 'Purchase'].includes(r.transaction_type)) return false;
    if (categoryFilter === 'Adjustments' && r.transaction_type !== 'Adjustment') return false;

    if (!query) return true;
    
    const distMatch = (r.distributors?.name || '').toLowerCase().includes(query) || (r.distributors?.code || '').toLowerCase().includes(query);
    const smMatch = (r.salesmen?.profiles?.full_name || '').toLowerCase().includes(query);
    const prodMatch = (r.product_packaging?.products?.name || '').toLowerCase().includes(query) || (r.product_packaging?.name || '').toLowerCase().includes(query);
    
    return (
      (r.reference_number || '').toLowerCase().includes(query) ||
      distMatch || smMatch || prodMatch ||
      (r.transaction_type || '').toLowerCase().includes(query) ||
      (r.status || '').toLowerCase().includes(query) ||
      (r.notes || '').toLowerCase().includes(query) ||
      fmtDate(r.transaction_date).toLowerCase().includes(query)
    );
  });

  const paginatedTxns = filteredTxns.slice((page - 1) * pageSize, page * pageSize);

  return (
    <>
      {/* 6 ACCURATE STOCK BALANCES */}
      <div className="grid g4" style={{ marginBottom: 16 }}>
        <div className="tile teal">
          <div className="bar"></div>
          <div className="label">Company Saleable Stock</div>
          <div className="num">{fmtNum(balances.saleableStock)} pkts</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Available for dispatch</div>
        </div>
        <div className="tile amber">
          <div className="bar"></div>
          <div className="label">Distributor Issued Stock</div>
          <div className="num">{fmtNum(balances.issuedStock)} pkts</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>In distributors' possession</div>
        </div>
        <div className="tile green">
          <div className="bar"></div>
          <div className="label">Distributor Good Returns</div>
          <div className="num">{fmtNum(balances.goodReturns)} pkts</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Restocked into saleable</div>
        </div>
        <div className="tile red">
          <div className="bar"></div>
          <div className="label">Damaged Returns &amp; Quarantined</div>
          <div className="num">{fmtNum(balances.damagedStock)} pkts</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Non-saleable isolation</div>
        </div>
      </div>

      <div className="grid g2" style={{ marginBottom: 20 }}>
        <div className="tile gray">
          <div className="bar" style={{ background: '#4A5568' }}></div>
          <div className="label">Production &amp; Purchases Inward</div>
          <div className="num">{fmtNum(balances.productionPurchases)} pkts</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Total inward physical stock</div>
        </div>
        <div className="tile gray">
          <div className="bar" style={{ background: '#718096' }}></div>
          <div className="label">Inventory Adjustments</div>
          <div className="num">{fmtNum(balances.adjustments)} pkts</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>Reconciled variance balance</div>
        </div>
      </div>

      {/* OPERATIONS PANEL */}
      <div className="grid g2">
        <div className="panel">
          <div className="section-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
            <h2 style={{ margin: 0 }}>Stock Operations</h2>
            <div className="tabs" style={{ margin: 0, borderBottom: 'none' }}>
              <div className={`tab${opTab==='return'?' active':''}`} onClick={()=>setOpTab('return')} style={{padding:'4px 10px',fontSize:12}}>Returns</div>
              <div className={`tab${opTab==='issue'?' active':''}`} onClick={()=>setOpTab('issue')} style={{padding:'4px 10px',fontSize:12}}>Issue Stock</div>
              <div className={`tab${opTab==='production'?' active':''}`} onClick={()=>setOpTab('production')} style={{padding:'4px 10px',fontSize:12}}>Production</div>
              <div className={`tab${opTab==='adjustment'?' active':''}`} onClick={()=>setOpTab('adjustment')} style={{padding:'4px 10px',fontSize:12}}>Adjustments</div>
            </div>
          </div>
          
          <Msg msg={msg} />

          {/* TAB 1: RETURNS */}
          {opTab === 'return' && (
            <form onSubmit={handleReturnSubmit}>
              <div style={{ marginBottom: 14, padding: 12, background: '#FAFBF8', border: '1px solid var(--line)', borderRadius: 6 }}>
                  <label style={{ fontWeight: 600, fontSize: 12, display: 'block', marginBottom: 6 }}>Select Distributor *</label>
                  {selDist ? (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(14,124,134,.06)', padding: '8px 12px', borderRadius: 4 }}>
                      <div>
                        <strong>{selDist.code}</strong> — {selDist.name} ({selDist.phone || 'No phone'})
                      </div>
                      <span className="link" style={{ color: 'var(--red)', fontSize: 12 }} onClick={()=>setSelDist(null)}>Change</span>
                    </div>
                  ) : (
                    <>
                      <input 
                        placeholder="Search distributor code, name..." 
                        value={distSearch} 
                        onChange={e=>setDistSearch(e.target.value)} 
                        style={{ width: '100%', marginBottom: 6 }} 
                      />
                      {distSearch && (
                        <div style={{ border: '1px solid var(--line)', borderRadius: 4, maxHeight: 130, overflowY: 'auto', background: '#fff' }}>
                          {filterDistList(distSearch).map(d => (
                            <div key={d.id} onClick={()=>{setSelDist(d); setDistSearch('');}} style={{ padding: '6px 10px', cursor: 'pointer', borderBottom: '1px solid var(--line)', fontSize: 12 }}>
                              <strong>{d.code}</strong> — {d.name}
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>

              <div className="form-grid">
                <div className="field">
                  <label>Product *</label>
                  <select value={returnForm.productId} onChange={e=>setReturnForm({...returnForm, productId: e.target.value, packagingId: ''})}>
                    <option value="">-- Select Product --</option>
                    {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>

                <div className="field">
                  <label>Packaging Variant *</label>
                  <select value={returnForm.packagingId} onChange={e=>setReturnForm({...returnForm, packagingId: e.target.value})} disabled={!returnForm.productId}>
                    <option value="">-- Select Variant --</option>
                    {products.find(p => p.id === returnForm.productId)?.product_packaging?.map(pk => (
                      <option key={pk.id} value={pk.id}>{pk.name}</option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label>Return Type *</label>
                  <select value={returnForm.returnType} onChange={e=>setReturnForm({...returnForm, returnType: e.target.value})}>
                    <option value="Distributor_Good_Return">Good Condition (Restock into Saleable)</option>
                    <option value="Distributor_Damaged_Return">Damaged / Expired / Unsellable (Quarantine)</option>
                  </select>
                </div>

                <div className="field">
                  <label>Quantity (Packets) *</label>
                  <input type="number" min="1" placeholder="e.g. 50" value={returnForm.quantity} onChange={e=>setReturnForm({...returnForm, quantity: e.target.value})} />
                </div>

                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>Notes / Inspection Remarks</label>
                  <textarea rows="2" placeholder="Condition details, route notes..." value={returnForm.notes} onChange={e=>setReturnForm({...returnForm, notes: e.target.value})} />
                </div>
              </div>

              <button type="submit" className="btn primary" disabled={saving} style={{ marginTop: 14 }}>
                {saving ? 'Submitting...' : 'Submit Return for Approval'}
              </button>
            </form>
          )}

          {/* TAB 2: PHYSICAL STOCK ISSUE */}
          {opTab === 'issue' && (
            <form onSubmit={handleIssueSubmit}>
              <div style={{ marginBottom: 14, padding: 12, background: '#FAFBF8', border: '1px solid var(--line)', borderRadius: 6 }}>
                <label style={{ fontWeight: 600, fontSize: 12, display: 'block', marginBottom: 6 }}>Issue To Distributor *</label>
                {selIssueDist ? (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(14,124,134,.06)', padding: '8px 12px', borderRadius: 4 }}>
                    <div>
                      <strong>{selIssueDist.code}</strong> — {selIssueDist.name} ({selIssueDist.phone || 'No phone'})
                    </div>
                    <span className="link" style={{ color: 'var(--red)', fontSize: 12 }} onClick={()=>setSelIssueDist(null)}>Change</span>
                  </div>
                ) : (
                  <>
                    <input 
                      placeholder="Search distributor code, name..." 
                      value={issueDistSearch} 
                      onChange={e=>setIssueDistSearch(e.target.value)} 
                      style={{ width: '100%', marginBottom: 6 }} 
                    />
                    {issueDistSearch && (
                      <div style={{ border: '1px solid var(--line)', borderRadius: 4, maxHeight: 130, overflowY: 'auto', background: '#fff' }}>
                        {filterDistList(issueDistSearch).map(d => (
                          <div key={d.id} onClick={()=>{setSelIssueDist(d); setIssueDistSearch('');}} style={{ padding: '6px 10px', cursor: 'pointer', borderBottom: '1px solid var(--line)', fontSize: 12 }}>
                            <strong>{d.code}</strong> — {d.name}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="form-grid">
                <div className="field">
                  <label>Product *</label>
                  <select value={issueForm.productId} onChange={e=>setIssueForm({...issueForm, productId: e.target.value, packagingId: ''})}>
                    <option value="">-- Select Product --</option>
                    {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>

                <div className="field">
                  <label>Packaging Variant *</label>
                  <select value={issueForm.packagingId} onChange={e=>setIssueForm({...issueForm, packagingId: e.target.value})} disabled={!issueForm.productId}>
                    <option value="">-- Select Variant --</option>
                    {products.find(p => p.id === issueForm.productId)?.product_packaging?.map(pk => (
                      <option key={pk.id} value={pk.id}>{pk.name}</option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label>Quantity to Issue (Packets) *</label>
                  <input type="number" min="1" placeholder="e.g. 100" value={issueForm.quantity} onChange={e=>setIssueForm({...issueForm, quantity: e.target.value})} />
                </div>

                <div className="field">
                  <label>Available Saleable Stock</label>
                  <input type="text" readOnly value={`${fmtNum(balances.saleableStock)} pkts`} style={{ background: '#f5f5f5', color: balances.saleableStock < Number(issueForm.quantity) ? 'var(--red)' : 'var(--text)' }} />
                </div>

                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>Notes / Vehicle Ref</label>
                  <input type="text" placeholder="Driver name, vehicle number..." value={issueForm.notes} onChange={e=>setIssueForm({...issueForm, notes: e.target.value})} />
                </div>

                {role === 'Super_Admin' && (
                  <div className="field" style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <input type="checkbox" id="negStockChk" checked={issueForm.allowNegative} onChange={e=>setIssueForm({...issueForm, allowNegative: e.target.checked})} />
                    <label htmlFor="negStockChk" style={{ fontSize: 12, cursor: 'pointer', margin: 0 }}>
                      Explicitly authorize negative stock adjustment if warehouse physical count exceeds recorded balance.
                    </label>
                  </div>
                )}
              </div>

              <button type="submit" className="btn primary" disabled={saving} style={{ marginTop: 14 }}>
                {saving ? 'Processing...' : 'Confirm Physical Stock Issuance'}
              </button>
            </form>
          )}

          {/* TAB 3: PRODUCTION & INWARD */}
          {opTab === 'production' && (
            <form onSubmit={handleProdSubmit}>
              <div className="form-grid">
                <div className="field">
                  <label>Transaction Type *</label>
                  <select value={prodForm.type} onChange={e=>setProdForm({...prodForm, type: e.target.value})}>
                    <option value="Production">Factory Production Inward</option>
                    <option value="Purchase">Supplier Purchase Inward</option>
                  </select>
                </div>

                <div className="field">
                  <label>Product *</label>
                  <select value={prodForm.productId} onChange={e=>setProdForm({...prodForm, productId: e.target.value, packagingId: ''})}>
                    <option value="">-- Select Product --</option>
                    {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>

                <div className="field">
                  <label>Packaging Variant *</label>
                  <select value={prodForm.packagingId} onChange={e=>setProdForm({...prodForm, packagingId: e.target.value})} disabled={!prodForm.productId}>
                    <option value="">-- Select Variant --</option>
                    {products.find(p => p.id === prodForm.productId)?.product_packaging?.map(pk => (
                      <option key={pk.id} value={pk.id}>{pk.name}</option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label>Quantity Inward (Packets) *</label>
                  <input type="number" min="1" placeholder="e.g. 500" value={prodForm.quantity} onChange={e=>setProdForm({...prodForm, quantity: e.target.value})} />
                </div>

                <div className="field">
                  <label>Unit Cost (PKR) (Optional)</label>
                  <input type="number" step="0.01" placeholder="e.g. 95.00" value={prodForm.unitCost} onChange={e=>setProdForm({...prodForm, unitCost: e.target.value})} />
                </div>

                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>Batch / Production Details</label>
                  <input type="text" placeholder="Batch #, shift, supplier invoice..." value={prodForm.notes} onChange={e=>setProdForm({...prodForm, notes: e.target.value})} />
                </div>
              </div>

              <button type="submit" className="btn primary" disabled={saving} style={{ marginTop: 14 }}>
                {saving ? 'Recording...' : 'Add to Company Saleable Stock'}
              </button>
            </form>
          )}

          {/* TAB 4: ADJUSTMENTS */}
          {opTab === 'adjustment' && (
            <form onSubmit={handleAdjSubmit}>
              <div className="form-grid">
                <div className="field">
                  <label>Product *</label>
                  <select value={adjForm.productId} onChange={e=>setAdjForm({...adjForm, productId: e.target.value, packagingId: ''})}>
                    <option value="">-- Select Product --</option>
                    {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>

                <div className="field">
                  <label>Packaging Variant *</label>
                  <select value={adjForm.packagingId} onChange={e=>setAdjForm({...adjForm, packagingId: e.target.value})} disabled={!adjForm.productId}>
                    <option value="">-- Select Variant --</option>
                    {products.find(p => p.id === adjForm.productId)?.product_packaging?.map(pk => (
                      <option key={pk.id} value={pk.id}>{pk.name}</option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label>Adjustment Quantity (+ or -) *</label>
                  <input type="number" placeholder="e.g. 5 or -5" value={adjForm.quantity} onChange={e=>setAdjForm({...adjForm, quantity: e.target.value})} />
                </div>

                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>Audited Explanation Reason <span style={{ color: 'var(--red)' }}>*</span></label>
                  <textarea rows="2" placeholder="Mandatory explanation: Physical audit variance, damaged in warehouse, packaging burst..." value={adjForm.notes} onChange={e=>setAdjForm({...adjForm, notes: e.target.value})} required />
                </div>
              </div>

              <button type="submit" className="btn primary" disabled={saving} style={{ marginTop: 14 }}>
                {saving ? 'Saving...' : 'Apply Authorized Stock Adjustment'}
              </button>
            </form>
          )}
        </div>

        {/* AUDIT SUMMARY SIDE PANEL */}
        <div className="panel">
          <div className="section-head"><h2>Stock Rules &amp; Integrity</h2></div>
          <table>
            <tbody>
              <tr><td>Saleable Stock Policy</td><td style={{textAlign:'right',fontWeight:600,color:'var(--teal)'}}>Physical Issue Only</td></tr>
              <tr><td>Booking Stock Effect</td><td style={{textAlign:'right',fontWeight:600}}>Never Deducts Stock</td></tr>
              <tr><td>Pending Transactions</td><td style={{textAlign:'right',fontWeight:600}}>Zero Stock Impact</td></tr>
              <tr><td>Cancelled Transactions</td><td style={{textAlign:'right',fontWeight:600}}>Fully Excluded</td></tr>
              <tr><td>Damaged Returns</td><td style={{textAlign:'right',fontWeight:600,color:'var(--red)'}}>Quarantined Only</td></tr>
              <tr><td>Good Returns</td><td style={{textAlign:'right',fontWeight:600,color:'var(--green)'}}>Restocked on Approval</td></tr>
            </tbody>
          </table>
          <div style={{ marginTop: 16, padding: 12, background: 'rgba(14,124,134,.05)', border: '1px solid rgba(14,124,134,.2)', borderRadius: 6, fontSize: 12 }}>
            <strong>Accounting Guarantee:</strong> All inventory balances derive strictly from approved transactions. Booking orders never decrease physical stock.
          </div>
        </div>
      </div>

      {/* LEDGER OF INVENTORY MOVEMENTS */}
      <div className="panel" style={{ marginTop: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 14 }}>
          <div className="section-head" style={{ margin: 0 }}>
            <h2>Auditable Stock Movements</h2>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <input 
              type="text" 
              placeholder="Search ref, dist, product..." 
              value={localSearch} 
              onChange={e => { setLocalSearch(e.target.value); setPage(1); }}
              style={{ padding: '5px 10px', fontSize: 12, border: '1px solid var(--line)', borderRadius: 6, width: 180 }}
            />
            <div className="chip-list" style={{ gap: 4 }}>
              {['All', 'Returns', 'Issues', 'Production', 'Adjustments'].map(cat => (
                <div key={cat} className={`chip${categoryFilter===cat?' active':''}`} onClick={() => { setCategoryFilter(cat); setPage(1); }} style={{ padding: '4px 8px', fontSize: 11 }}>
                  {cat}
                </div>
              ))}
            </div>
            <div className="chip-list" style={{ gap: 4 }}>
              {['All', 'Approved', 'Pending', 'Cancelled'].map(st => (
                <div key={st} className={`chip${statusFilter===st?' active':''}`} onClick={() => { setStatusFilter(st); setPage(1); }} style={{ padding: '4px 8px', fontSize: 11 }}>
                  {st}
                </div>
              ))}
            </div>
          </div>
        </div>

        {loading ? <div style={{ padding: 20, color: 'var(--text-dim)' }}>Loading inventory transactions...</div> : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ minWidth: 850 }}>
              <thead>
                <tr>
                  <th>Ref #</th>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Entity</th>
                  <th>Product Variant</th>
                  <th>Category</th>
                  <th style={{ textAlign: 'center' }}>Qty</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedTxns.length === 0 ? (
                  <tr><td colSpan={9} style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>No matching inventory movements found.</td></tr>
                ) : (
                  paginatedTxns.map(r => {
                    const isGoodReturn = r.transaction_type?.includes('Good');
                    const isDamaged = r.transaction_type?.includes('Damaged') || r.transaction_type?.includes('Damage');
                    return (
                      <tr key={r.id}>
                        <td style={{ fontSize: 11, fontWeight: 600, fontFamily: 'monospace' }}>{r.reference_number}</td>
                        <td>{fmtDate(r.transaction_date)}</td>
                        <td>
                          <span style={{ fontWeight: 500 }}>
                            {r.transaction_type.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td>
                          {r.distributors ? (
                            <span><span className="badge teal" style={{ marginRight: 4, padding: '1px 4px', fontSize: 9 }}>Dist</span>{r.distributors.name}</span>
                          ) : r.salesmen ? (
                            <span><span className="badge" style={{ marginRight: 4, padding: '1px 4px', fontSize: 9 }}>SM</span>{r.salesmen.profiles?.full_name}</span>
                          ) : (
                            <span style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>Company Internal</span>
                          )}
                        </td>
                        <td>{r.product_packaging?.products?.name || ''} — {r.product_packaging?.name || ''}</td>
                        <td>
                          <span className={`badge ${isGoodReturn ? 'green' : isDamaged ? 'red' : 'gray'}`} style={{ fontSize: 10 }}>
                            {r.category}
                          </span>
                        </td>
                        <td className="num-cell" style={{ textAlign: 'center', fontWeight: 600 }}>{r.quantity} pkts</td>
                        <td>
                          <span className={`badge ${r.status==='Approved'?'green':r.status==='Pending'?'amber':'gray'}`}>
                            {r.status}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end', alignItems: 'center' }}>
                            {r.status === 'Pending' && (role === 'Super_Admin' || (role === 'Manager' && (hasPermission('inventory.approve') || hasPermission('returns.approve')))) && (
                              <button className="btn" style={{ padding: '3px 8px', fontSize: 11, background: 'var(--teal)', color: '#fff' }} onClick={()=>handleApprove(r.id)}>
                                Approve
                              </button>
                            )}
                            {r.status === 'Pending' && (
                              <button className="btn ghost" style={{ padding: '3px 8px', fontSize: 11, color: 'var(--red)' }} onClick={()=>handleCancel(r.id)}>
                                Cancel
                              </button>
                            )}
                            {r.status === 'Approved' && role === 'Super_Admin' && (
                              <button className="btn ghost" style={{ padding: '3px 8px', fontSize: 11, color: 'var(--red)' }} onClick={()=>handleCancel(r.id)}>
                                Cancel
                              </button>
                            )}
                            <button className="btn" style={{ padding: '3px 8px', fontSize: 11 }} onClick={()=>handlePrint(r)}>Print</button>
                            <button className="btn" style={{ padding: '3px 8px', fontSize: 11, background: '#25d366', color: '#fff', border: 'none' }} onClick={()=>handleWhatsApp(r)}>WA</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
            <Pagination page={page} pageSize={pageSize} total={filteredTxns.length} onPageChange={setPage} />
          </div>
        )}
      </div>
    </>
  );
}

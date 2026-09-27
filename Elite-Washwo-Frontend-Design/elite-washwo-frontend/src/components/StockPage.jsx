import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchDistributors,
  fetchSalesmen,
  fetchProducts,
  fetchInventoryTransactions,
  submitStockReturn,
  approveTransaction
} from '../lib/db';

const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

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
  
  // Data
  const [distributors, setDistributors] = useState([]);
  const [salesmen, setSalesmen] = useState([]);
  const [products, setProducts] = useState([]);
  const [txns, setTxns] = useState([]);
  const [loading, setLoading] = useState(false);

  // Form states
  const [formType, setFormType] = useState('distributor'); // 'distributor' | 'salesman'
  const [msg, setMsg] = useState('');
  const [saving, setSaving] = useState(false);
  
  // Distributor form state
  const [distSearch, setDistSearch] = useState('');
  const [selDist, setSelDist] = useState(null);
  
  // General form state
  const [form, setForm] = useState({
    salesmanId: '',
    productId: '',
    packagingId: '',
    returnType: 'Salesman_Good_Return', // Reuses existing valid enum — distributor_id column identifies entity
    quantity: '',
    notes: ''
  });

  // Filters
  const [localSearch, setLocalSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const loadData = async () => {
    setLoading(true);
    try {
      const [d, s, p, t] = await Promise.all([
        fetchDistributors(),
        fetchSalesmen(),
        fetchProducts(),
        fetchInventoryTransactions()
      ]);
      setDistributors(d || []);
      setSalesmen(s || []);
      setProducts(p || []);
      setTxns(t || []);
      
      // Auto-select salesman if role is Salesman
      if (role === 'Salesman' && s) {
        const own = s.find(x => x.profile_id === user?.id);
        if (own && !form.salesmanId) {
          setForm(prev => ({ ...prev, salesmanId: own.id }));
        }
      }
    } catch (e) {
      console.error(e);
      setMsg('err:Failed to load stock data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [role, user]);

  const activeDistributors = distributors.filter(d => d.is_active);
  const distSearchL = distSearch.toLowerCase();
  const filteredDists = distSearch
    ? activeDistributors.filter(d =>
        d.code?.toLowerCase().includes(distSearchL) ||
        d.name?.toLowerCase().includes(distSearchL) ||
        d.id_card?.toLowerCase().includes(distSearchL) ||
        d.phone?.toLowerCase().includes(distSearchL)
      )
    : activeDistributors;

  const selProdObj = products.find(p => p.id === form.productId);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (role === 'Manager' && !hasPermission('inventory.create') && !hasPermission('returns.create')) {
      setMsg("err:Permission denied: You do not have permission to submit returns ('returns.create').");
      return;
    }
    
    if (formType === 'distributor' && !selDist) {
      setMsg('err:Please select a distributor.'); return;
    }
    if (formType === 'salesman' && !form.salesmanId) {
      setMsg('err:Please select a salesman.'); return;
    }
    if (!form.packagingId || !form.quantity || Number(form.quantity) < 1) {
      setMsg('err:Please select a product variant and enter a valid quantity.'); return;
    }

    setSaving(true); setMsg('');
    try {
      const pkgObj = selProdObj?.product_packaging?.find(pk => pk.id === form.packagingId);
      const unit_cost = pkgObj?.product_prices?.[0]?.unit_cost || 0;

      await submitStockReturn({
        distributorId: formType === 'distributor' ? selDist.id : null,
        salesmanId: formType === 'salesman' ? form.salesmanId : null,
        packagingId: form.packagingId,
        transaction_type: form.returnType,
        quantity: form.quantity,
        notes: form.notes,
        unit_cost
      });
      
      setMsg('ok:Return submitted for approval.');
      setForm({
        ...form,
        packagingId: '',
        productId: '',
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

  const handleApprove = async (id) => {
    if (!hasPermission('inventory.approve') && !hasPermission('returns.approve')) {
      alert("Permission denied: You do not have permission to approve returns ('returns.approve').");
      return;
    }
    try { 
      await approveTransaction(id); 
      await loadData(); 
    } catch(e) { 
      alert(e.message); 
    }
  };

  // WhatsApp
  const handleWhatsApp = (r) => {
    const isDist = !!r.distributor_id;
    const entityLabel = isDist ? 'Distributor' : 'Salesman';
    const entityName = isDist ? (r.distributors?.name || 'Unknown') : (r.salesmen?.profiles?.full_name || 'Unknown');
    const text = encodeURIComponent(
      `*Elite Wash — Stock Return*\n` +
      `Ref: ${r.reference_number}\n` +
      `Date: ${fmtDate(r.transaction_date)}\n` +
      `${entityLabel}: ${entityName}\n` +
      `Product: ${r.product_packaging?.products?.name || ''} - ${r.product_packaging?.name || ''}\n` +
      `Return Cause: ${r.transaction_type.replace(/_/g, ' ')}\n` +
      `Quantity: ${r.quantity} pkts\n` +
      `Status: ${r.status}\n` +
      (r.notes ? `Notes: ${r.notes}` : '')
    );
    window.open(`https://wa.me/923240106056?text=${text}`, '_blank');
  };

  // Print
  const handlePrint = (r) => {
    const isDist = !!r.distributor_id;
    const entityLabel = isDist ? 'Distributor' : 'Salesman';
    const entityName = isDist 
      ? `${r.distributors?.name || ''} (${r.distributors?.code || ''})`
      : `${r.salesmen?.profiles?.full_name || ''}`;

    const win = window.open('', '_blank');
    win.document.write(`<html><head><title>Return ${r.reference_number}</title>
      <style>body{font-family:sans-serif;padding:20px}h2{margin-bottom:4px}table{width:100%;border-collapse:collapse;margin-top:12px}td,th{border:1px solid #ccc;padding:8px;font-size:13px}th{background:#f5f5f5}</style></head>
      <body>
        <h2>Elite Wash — Stock Return</h2>
        <p><strong>Ref #:</strong> ${r.reference_number} &nbsp; <strong>Date:</strong> ${fmtDate(r.transaction_date)} &nbsp; <strong>Status:</strong> ${r.status}</p>
        <p><strong>${entityLabel}:</strong> ${entityName}</p>
        <p><strong>Return Cause:</strong> ${r.transaction_type.replace(/_/g, ' ')}</p>
        ${r.notes ? `<p><strong>Notes:</strong> ${r.notes}</p>` : ''}
        <table>
          <tr><th>Product Variant</th><th>Quantity</th></tr>
          <tr>
            <td>${r.product_packaging?.products?.name || ''} - ${r.product_packaging?.name || ''}</td>
            <td>${r.quantity} pkts</td>
          </tr>
        </table>
        <br/><p style="font-size:11px;color:#999">Elite Wash ERP — Stock adjustments are strictly derived from approved transactions.</p>
      </body></html>`);
    win.document.close(); win.print();
  };

  // List processing
  const returnsList = txns.filter(t => t.reference_number?.startsWith('RTN') || t.transaction_type?.includes('Return'));
  const query = (localSearch || searchTerm).trim().toLowerCase();

  const filteredReturns = returnsList.filter(r => {
    if (statusFilter !== 'All' && r.status !== statusFilter) return false;
    
    const isGood = r.transaction_type?.includes('Good');
    const isDamaged = r.transaction_type?.includes('Damaged');
    if (typeFilter === 'Good' && !isGood) return false;
    if (typeFilter === 'Damaged' && !isDamaged) return false;
    
    if (!query) return true;
    
    const distMatch = (r.distributors?.name || '').toLowerCase().includes(query) || (r.distributors?.code || '').toLowerCase().includes(query);
    const smMatch = (r.salesmen?.profiles?.full_name || '').toLowerCase().includes(query);
    
    return (
      (r.reference_number || '').toLowerCase().includes(query) ||
      distMatch || smMatch ||
      (r.transaction_type || '').toLowerCase().includes(query) ||
      (r.status || '').toLowerCase().includes(query) ||
      (r.notes || '').toLowerCase().includes(query) ||
      fmtDate(r.transaction_date).toLowerCase().includes(query)
    );
  });

  const paginatedReturns = filteredReturns.slice((page - 1) * pageSize, page * pageSize);
  const isFiltered = localSearch || statusFilter !== 'All' || typeFilter !== 'All';
  const resetFilters = () => { setLocalSearch(''); setStatusFilter('All'); setTypeFilter('All'); setPage(1); };

  return (
    <>
      <div className="grid g2">
        <div className="panel">
          <div className="section-head" style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <h2 style={{margin:0}}>Submit Stock Return</h2>
            <div className="tabs" style={{margin:0, borderBottom:'none'}}>
              <div className={`tab${formType==='distributor'?' active':''}`} onClick={()=>{setFormType('distributor'); setForm(f=>({...f,returnType:'Salesman_Good_Return'}));}} style={{padding:'4px 10px',fontSize:12}}>Distributor</div>
              <div className={`tab${formType==='salesman'?' active':''}`} onClick={()=>{setFormType('salesman'); setForm(f=>({...f,returnType:'Salesman_Good_Return'}));}} style={{padding:'4px 10px',fontSize:12}}>Salesman</div>
            </div>
          </div>
          
          <Msg msg={msg} />
          
          <form onSubmit={handleSubmit}>
            {/* DISTRIBUTOR SELECTOR */}
            {formType === 'distributor' && (
              <div style={{marginBottom:16,padding:14,background:'#FAFBF8',border:'1px solid var(--line)',borderRadius:6}}>
                <div style={{fontWeight:600,fontSize:13,marginBottom:10}}>Select Distributor *</div>
                {selDist ? (
                  <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(120px,1fr))',gap:10,background:'rgba(14,124,134,.05)',border:'1px solid rgba(14,124,134,.25)',borderRadius:6,padding:12}}>
                    <div><div style={{fontSize:10,textTransform:'uppercase',color:'var(--text-dim)'}}>Code</div><div style={{fontWeight:600}}>{selDist.code}</div></div>
                    <div><div style={{fontSize:10,textTransform:'uppercase',color:'var(--text-dim)'}}>Name</div><div style={{fontWeight:600}}>{selDist.name}</div></div>
                    <div><div style={{fontSize:10,textTransform:'uppercase',color:'var(--text-dim)'}}>Phone</div><div>{selDist.phone || '—'}</div></div>
                    <div style={{display:'flex',alignItems:'flex-end'}}>
                      <span className="link" style={{color:'var(--red)',fontSize:12}} onClick={()=>{setSelDist(null);setDistSearch('');}}>Change</span>
                    </div>
                  </div>
                ) : (
                  <>
                    <input
                      placeholder="Search Code, Name, Phone..."
                      value={distSearch}
                      onChange={e=>setDistSearch(e.target.value)}
                      style={{width:'100%',boxSizing:'border-box',marginBottom:8}}
                    />
                    {distSearch && (
                      <div style={{border:'1px solid var(--line)',borderRadius:4,maxHeight:150,overflowY:'auto',background:'#fff'}}>
                        {filteredDists.length === 0 ? <div style={{padding:10,fontSize:12,color:'var(--text-dim)'}}>No distributors found.</div> :
                          filteredDists.map(d => (
                            <div key={d.id} onClick={()=>{setSelDist(d);setDistSearch('');}} style={{padding:'8px 12px',cursor:'pointer',borderBottom:'1px solid var(--line)',fontSize:13}}>
                              <span style={{fontWeight:600}}>{d.name}</span> <span style={{fontSize:11,color:'var(--text-dim)'}}>({d.code})</span>
                            </div>
                          ))
                        }
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* SALESMAN SELECTOR */}
            {formType === 'salesman' && (
              <div className="field" style={{marginBottom:16}}>
                <label>Salesman *</label>
                {role === 'Salesman' ? (
                  <select value={form.salesmanId} disabled style={{background:'var(--paper)'}}>
                    {salesmen.filter(s => s.profile_id === user?.id).map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
                  </select>
                ) : (
                  <select value={form.salesmanId} onChange={e=>setForm(f=>({...f,salesmanId:e.target.value}))}>
                    <option value="">-- Select --</option>
                    {salesmen.map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
                  </select>
                )}
              </div>
            )}

            <div className="form-grid">
              <div className="field">
                <label>Product *</label>
                <select value={form.productId} onChange={e=>setForm(f=>({...f,productId:e.target.value, packagingId:''}))}>
                  <option value="">-- Select --</option>
                  {products.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Variant *</label>
                <select value={form.packagingId} onChange={e=>setForm(f=>({...f,packagingId:e.target.value}))} disabled={!form.productId}>
                  <option value="">-- Select --</option>
                  {selProdObj?.product_packaging?.map(pk=><option key={pk.id} value={pk.id}>{pk.name}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Return Cause *</label>
                <select value={form.returnType} onChange={e=>setForm(f=>({...f,returnType:e.target.value}))}>
                  {formType === 'distributor' ? (
                    <>
                      {/* Uses existing valid enum values — distributor_id column identifies the entity */}
                      <option value="Salesman_Good_Return">Unsold Return (Good)</option>
                      <option value="Salesman_Damaged_Return">Damaged Return</option>
                      <option value="Customer_Good_Return">Expired / Unsellable Return</option>
                    </>
                  ) : (
                    <>
                      <option value="Salesman_Good_Return">Unsold Return (Good)</option>
                      <option value="Salesman_Damaged_Return">Damaged Return</option>
                      <option value="Customer_Good_Return">Customer Return (Good)</option>
                      <option value="Customer_Damaged_Return">Customer Return (Damaged)</option>
                    </>
                  )}
                </select>
              </div>
              <div className="field">
                <label>Quantity (Packets) *</label>
                <input type="number" min="1" placeholder="e.g. 20" value={form.quantity} onChange={e=>setForm(f=>({...f,quantity:e.target.value}))}/>
              </div>
              <div className="field" style={{gridColumn:'1/-1'}}>
                <label>Notes</label>
                <textarea rows={2} placeholder="Optional explanation/details" value={form.notes} onChange={e=>setForm(f=>({...f,notes:e.target.value}))}/>
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
              <tr><td>Total returns submitted</td><td className="num-cell" style={{textAlign:'right'}}>{returnsList.length}</td></tr>
              <tr><td>Pending approval</td><td className="num-cell" style={{textAlign:'right'}}>{returnsList.filter(r=>r.status==='Pending').length}</td></tr>
              <tr><td>Approved</td><td className="num-cell" style={{textAlign:'right'}}>{returnsList.filter(r=>r.status==='Approved').length}</td></tr>
              <tr><td>Good condition returns</td><td className="num-cell" style={{textAlign:'right'}}>{returnsList.filter(r=>r.transaction_type?.includes('Good')).length}</td></tr>
              <tr><td>Damaged/Expired returns</td><td className="num-cell" style={{textAlign:'right'}}>{returnsList.filter(r=>r.transaction_type?.includes('Damaged') || r.transaction_type?.includes('Expired')).length}</td></tr>
            </tbody>
          </table>
          <p style={{fontSize:12,color:'var(--text-dim)',marginTop:16}}>
            Note: Stock is strictly transaction-derived. Balances are updated exactly once when a return is approved.
          </p>
        </div>
      </div>

      <div className="panel" style={{marginTop:20}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,marginBottom:14}}>
          <div className="section-head" style={{margin:0}}><h2>Return transactions ledger</h2></div>
          <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}>
            <input 
              type="text" 
              placeholder="Search ref, dist, salesman..." 
              value={localSearch} 
              onChange={e => { setLocalSearch(e.target.value); setPage(1); }}
              style={{padding:'5px 10px',fontSize:12,border:'1px solid var(--line)',borderRadius:6,background:'var(--panel)',color:'var(--text)',outline:'none',width:190}}
            />
            <div className="chip-list" style={{gap:4}}>
              {['All', 'Pending', 'Approved'].map(st => (
                <div key={st} className={`chip${statusFilter===st?' active':''}`} onClick={() => { setStatusFilter(st); setPage(1); }} style={{padding:'4px 10px',fontSize:11}}>
                  {st}
                </div>
              ))}
              {['All Types', 'Good', 'Damaged'].map(tp => (
                <div key={tp} className={`chip${typeFilter===(tp==='All Types'?'All':tp)?' active':''}`} onClick={() => { setTypeFilter(tp==='All Types'?'All':tp); setPage(1); }} style={{padding:'4px 10px',fontSize:11}}>
                  {tp}
                </div>
              ))}
            </div>
            {isFiltered && (
              <span className="link" onClick={resetFilters} style={{color:'var(--red)',fontSize:12}}>Reset</span>
            )}
          </div>
        </div>

        {loading ? <div style={{padding:20,color:'var(--text-dim)'}}>Loading transactions...</div> : (
          <div style={{overflowX:'auto'}}>
            <table style={{minWidth:800}}>
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Date</th>
                  <th>Entity (Dist / SM)</th>
                  <th>Return Cause</th>
                  <th>Product</th>
                  <th style={{textAlign:'center'}}>Qty</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedReturns.length===0 ? 
                  <tr><td colSpan={8} style={{textAlign:'center',padding:20,color:'var(--text-dim)'}}>No matching return transactions found.</td></tr> :
                  paginatedReturns.map(r=>(
                    <tr key={r.id}>
                      <td style={{fontSize:11,fontWeight:600}}>{r.reference_number}</td>
                      <td>{fmtDate(r.transaction_date)}</td>
                      <td>
                        {r.distributor_id ? (
                          <span><span className="badge teal" style={{marginRight:6,padding:'2px 4px',fontSize:9}}>Dist</span>{r.distributors?.name} <span style={{fontSize:11,color:'var(--text-dim)'}}>({r.distributors?.code})</span></span>
                        ) : r.salesman_id ? (
                          <span><span className="badge" style={{marginRight:6,padding:'2px 4px',fontSize:9}}>SM</span>{r.salesmen?.profiles?.full_name}</span>
                        ) : (
                          <span style={{fontStyle:'italic',color:'var(--text-dim)'}}>Unassigned</span>
                        )}
                      </td>
                      <td>{r.transaction_type?.replace(/_/g,' ')}</td>
                      <td>{r.product_packaging?.products?.name} - {r.product_packaging?.name}</td>
                      <td className="num-cell" style={{textAlign:'center'}}>{r.quantity}</td>
                      <td>
                        <span className={`badge ${r.status==='Approved'?'green':r.status==='Pending'?'amber':'gray'}`}>
                          {r.status}
                        </span>
                      </td>
                      <td>
                        <div style={{display:'flex',gap:6,alignItems:'center'}}>
                          {r.status==='Pending' && hasPermission('inventory.approve') && (
                            <button className="btn ghost" style={{padding:'3px 8px',fontSize:12,color:'var(--teal)'}} onClick={()=>handleApprove(r.id)}>Approve</button>
                          )}
                          <button className="btn" style={{padding:'3px 8px',fontSize:12}} onClick={()=>handlePrint(r)}>Print</button>
                          <button className="btn" style={{padding:'3px 8px',fontSize:12,background:'#25d366',color:'#fff',border:'none'}} onClick={()=>handleWhatsApp(r)}>WA</button>
                        </div>
                      </td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
            <Pagination page={page} pageSize={pageSize} total={filteredReturns.length} onPageChange={setPage} />
          </div>
        )}
      </div>
    </>
  );
}

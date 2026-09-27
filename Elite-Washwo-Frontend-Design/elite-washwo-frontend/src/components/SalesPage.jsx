import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchDistributors,
  fetchSalesmen,
  fetchCustomers,
  fetchProducts,
  fetchSales,
  fetchDistributorOutstanding,
  fetchDistributorTodayRecovery,
  submitSale
} from '../lib/db';

// Per-packet fee constants (configurable per business rules)
const COMMISSION_PER_PACKET    = 30;
const ADVERTISEMENT_PER_PACKET = 20;
const WELFARE_PER_PACKET       = 10;

const fmtNum  = (n) => Number(n || 0).toLocaleString('en-PK');
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';
const todayISO = () => new Date().toISOString().split('T')[0];
const dayStart  = (d) => `${d}T00:00:00.000Z`;
const dayEnd    = (d) => `${d}T23:59:59.999Z`;

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

export default function SalesPage({ searchTerm = '' }) {
  const { role } = useAuth();

  const [activeTab, setActiveTab] = useState('list');

  // Reference data
  const [distributors, setDistributors] = useState([]);
  const [salesmen,     setSalesmen]     = useState([]);
  const [customers,    setCustomers]    = useState([]);
  const [products,     setProducts]     = useState([]);

  // List state
  const [sales,         setSales]        = useState([]);
  const [loading,       setLoading]      = useState(false);
  const [msg,           setMsg]          = useState('');
  const [filterDate,    setFilterDate]   = useState(todayISO());
  const [filterDist,    setFilterDist]   = useState('');
  const [filterSearch,  setFilterSearch] = useState('');

  // Distributor info panel (list view selected dist)
  const [distOutstanding,    setDistOutstanding]    = useState(null);
  const [distTodayRecovery,  setDistTodayRecovery]  = useState(null);

  // Create form state
  const [selDist,        setSelDist]        = useState(null);
  const [distSearch,     setDistSearch]     = useState('');
  const [salesmanId,     setSalesmanId]     = useState('');
  const [customerId,     setCustomerId]     = useState('');
  const [items,          setItems]          = useState([]);
  const [saving,         setSaving]         = useState(false);
  const [formMsg,        setFormMsg]        = useState('');

  // Item picker
  const [selProduct,  setSelProduct]  = useState('');
  const [selPkg,      setSelPkg]      = useState('');
  const [selQty,      setSelQty]      = useState('');

  // ── Load reference data once ──────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const [d, s, c, p] = await Promise.all([
          fetchDistributors(), fetchSalesmen(), fetchCustomers(), fetchProducts()
        ]);
        setDistributors(d || []);
        setSalesmen(s || []);
        setCustomers(c || []);
        setProducts(p || []);
      } catch (e) { console.error(e); }
    })();
  }, []);

  // ── Load sales (with filters) ─────────────────────────────────────────────
  const loadSales = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchSales({
        dateFrom: filterDate ? dayStart(filterDate) : undefined,
        dateTo:   filterDate ? dayEnd(filterDate)   : undefined,
        distributorId: filterDist || undefined
      });
      setSales(data || []);
    } catch (e) {
      console.error(e);
      setMsg('err:Failed to load sales.');
    }
    setLoading(false);
  }, [filterDate, filterDist]);

  useEffect(() => { loadSales(); }, [loadSales]);

  // ── Load distributor outstanding when filterDist changes ─────────────────
  useEffect(() => {
    if (!filterDist) { setDistOutstanding(null); setDistTodayRecovery(null); return; }
    (async () => {
      try {
        const [out, rec] = await Promise.all([
          fetchDistributorOutstanding(filterDist),
          fetchDistributorTodayRecovery(filterDist)
        ]);
        setDistOutstanding(out);
        setDistTodayRecovery(rec);
      } catch (e) { console.error(e); }
    })();
  }, [filterDist]);

  // ── Commission calculations (derived from TODAY's loaded sales) ───────────
  const totalPacketsToday = sales.reduce((sum, s) =>
    sum + (s.sale_items || []).reduce((a, i) => a + Number(i.quantity), 0), 0
  );
  const todayCommission    = totalPacketsToday * COMMISSION_PER_PACKET;
  const todayAdvertisement = totalPacketsToday * ADVERTISEMENT_PER_PACKET;
  const todayWelfare       = totalPacketsToday * WELFARE_PER_PACKET;

  // ── Distributor search (create form) ─────────────────────────────────────
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

  // ── Product pricing ───────────────────────────────────────────────────────
  const selProdObj  = products.find(p => p.id === selProduct);
  const selPkgObj   = selProdObj?.product_packaging?.find(pk => pk.id === selPkg);
  const autoPrice   = selPkgObj?.product_prices?.[0]?.sales_price || 0;

  const handleAddItem = () => {
    if (!selProduct || !selPkg || !selQty || Number(selQty) < 1) {
      setFormMsg('err:Select a product, packaging, and enter valid quantity.');
      return;
    }
    const name = (selProdObj?.name || '') + (selPkgObj?.name ? ' — ' + selPkgObj.name : '');
    setItems([...items, { packagingId: selPkg, name, price: Number(autoPrice), quantity: parseInt(selQty, 10) }]);
    setSelProduct(''); setSelPkg(''); setSelQty('');
    setFormMsg('');
  };
  const removeItem = (i) => setItems(items.filter((_, idx) => idx !== i));
  const totalAmount = items.reduce((s, i) => s + i.price * i.quantity, 0);

  // ── Save sale ─────────────────────────────────────────────────────────────
  // NOTE: sales_orders.salesman_id and customer_id have NOT NULL constraints.
  // They must always be selected to ensure the DB insert succeeds and
  // distributor_id is persisted correctly.
  const handleSubmit = async () => {
    if (!selDist)           { setFormMsg('err:Please select a distributor.'); return; }
    if (!salesmanId)        { setFormMsg('err:Please select a salesman (required by the database).'); return; }
    if (!customerId)        { setFormMsg('err:Please select a customer (required by the database).'); return; }
    if (items.length === 0) { setFormMsg('err:Add at least one product item.'); return; }
    setSaving(true); setFormMsg('');
    try {
      await submitSale({
        distributorId: selDist.id,   // UUID — stored in sales_orders.distributor_id
        salesmanId,                  // Required — NOT NULL in DB
        customerId,                  // Required — NOT NULL in DB
        items,
        totalAmount
      });
      setFormMsg('ok:Sale recorded successfully.');
      setSelDist(null); setDistSearch('');
      setSalesmanId(''); setCustomerId('');
      setItems([]); setSelProduct(''); setSelPkg(''); setSelQty('');
      await loadSales();
      setTimeout(() => { setActiveTab('list'); setFormMsg(''); }, 1500);
    } catch (e) {
      setFormMsg('err:' + e.message);
    } finally { setSaving(false); }
  };

  // ── WhatsApp ──────────────────────────────────────────────────────────────
  const handleWhatsApp = (s) => {
    const dist = s.distributors ? `${s.distributors.name} (${s.distributors.code})` : 'Not Assigned';
    const packets = (s.sale_items || []).reduce((a, i) => a + Number(i.quantity), 0);
    const text = encodeURIComponent(
      `*Elite Wash — Sale*\n` +
      `Ref: ${s.reference_number}\n` +
      `Date: ${fmtDate(s.sale_date)}\n` +
      `Distributor: ${dist}\n` +
      `Packets: ${packets}\n` +
      `Total: Rs. ${fmtNum(s.total_amount)}\n` +
      `Status: ${s.status}`
    );
    window.open(`https://wa.me/923240106056?text=${text}`, '_blank');
  };

  // ── Print ─────────────────────────────────────────────────────────────────
  const handlePrint = (s) => {
    const dist = s.distributors
      ? `${s.distributors.name} | ${s.distributors.code} | ${s.distributors.id_card || ''} | ${s.distributors.phone || ''}`
      : 'Not Assigned';
    const packets = (s.sale_items || []).reduce((a, i) => a + Number(i.quantity), 0);
    const win = window.open('', '_blank');
    win.document.write(`<html><head><title>Sale ${s.reference_number}</title>
      <style>body{font-family:sans-serif;padding:20px}h2{margin-bottom:4px}table{width:100%;border-collapse:collapse;margin-top:12px}td,th{border:1px solid #ccc;padding:8px;font-size:13px}th{background:#f5f5f5}</style></head>
      <body>
        <h2>Elite Wash — Sale</h2>
        <p><strong>Sale #:</strong> ${s.reference_number} &nbsp; <strong>Date:</strong> ${fmtDate(s.sale_date)} &nbsp; <strong>Status:</strong> ${s.status}</p>
        <p><strong>Distributor:</strong> ${dist}</p>
        <p><strong>Customer:</strong> ${s.customers?.name || '—'}</p>
        <table>
          <tr><th>Total Packets</th><th>Total Amount</th></tr>
          <tr><td>${packets}</td><td>Rs. ${fmtNum(s.total_amount)}</td></tr>
        </table>
        <br/><p style="font-size:11px;color:#999">Elite Wash ERP — All balances derived from transactions.</p>
      </body></html>`);
    win.document.close(); win.print();
  };

  // ── Client search filter ──────────────────────────────────────────────────
  const sq = (filterSearch || searchTerm).toLowerCase();
  const displaySales = sq
    ? sales.filter(s =>
        s.reference_number?.toLowerCase().includes(sq) ||
        s.distributors?.name?.toLowerCase().includes(sq) ||
        s.distributors?.code?.toLowerCase().includes(sq) ||
        s.customers?.name?.toLowerCase().includes(sq)
      )
    : sales;

  const distLabel = (s) => {
    if (!s.distributors) return <span style={{color:'var(--text-dim)',fontStyle:'italic'}}>Not Assigned</span>;
    return <span>{s.distributors.name} <span style={{fontSize:11,color:'var(--text-dim)'}}>({s.distributors.code})</span></span>;
  };

  const selectedDistObj = distributors.find(d => d.id === filterDist);

  return (
    <>
      {/* Tabs */}
      <div className="panel" style={{marginBottom:20}}>
        <div className="tabs">
          <div className={`tab${activeTab==='list'?' active':''}`}   onClick={()=>setActiveTab('list')}>Sales Ledger</div>
          <div className={`tab${activeTab==='create'?' active':''}`} onClick={()=>setActiveTab('create')}>Create Sale</div>
        </div>
      </div>

      <Msg msg={msg} />

      {/* ── SALES LIST ─────────────────────────────────────────────── */}
      {activeTab === 'list' && (
        <>
          {/* Summary tiles when distributor is selected */}
          {filterDist && (
            <div className="grid g4" style={{marginBottom:16}}>
              <div className="tile teal">
                <div className="bar"></div>
                <div className="label">Outstanding Balance</div>
                <div className="num">Rs. {distOutstanding !== null ? fmtNum(distOutstanding) : '…'}</div>
              </div>
              <div className="tile green">
                <div className="bar"></div>
                <div className="label">Today's Recovery</div>
                <div className="num">Rs. {distTodayRecovery !== null ? fmtNum(distTodayRecovery) : '…'}</div>
              </div>
              <div className="tile amber">
                <div className="bar"></div>
                <div className="label">Commission (today)</div>
                <div className="num">Rs. {fmtNum(todayCommission)}</div>
                <div style={{fontSize:10,color:'rgba(255,255,255,.7)',marginTop:4}}>{totalPacketsToday} pkts × {COMMISSION_PER_PACKET} PKR</div>
              </div>
              <div className="tile red">
                <div className="bar"></div>
                <div className="label">Adv + Welfare</div>
                <div className="num">Rs. {fmtNum(todayAdvertisement + todayWelfare)}</div>
                <div style={{fontSize:10,color:'rgba(255,255,255,.7)',marginTop:4}}>Adv: {fmtNum(todayAdvertisement)} · W: {fmtNum(todayWelfare)}</div>
              </div>
            </div>
          )}

          <div className="panel">
            {/* Filters */}
            <div style={{display:'flex',gap:12,flexWrap:'wrap',alignItems:'flex-end',marginBottom:16}}>
              <div className="field" style={{flex:'1 1 155px',margin:0}}>
                <label style={{fontSize:11,fontWeight:600,color:'var(--text-dim)',textTransform:'uppercase',letterSpacing:'.04em'}}>Date</label>
                <input type="date" value={filterDate} onChange={e=>setFilterDate(e.target.value)} />
              </div>
              <div className="field" style={{flex:'1 1 190px',margin:0}}>
                <label style={{fontSize:11,fontWeight:600,color:'var(--text-dim)',textTransform:'uppercase',letterSpacing:'.04em'}}>Distributor</label>
                <select value={filterDist} onChange={e=>setFilterDist(e.target.value)}>
                  <option value="">All Distributors</option>
                  {distributors.map(d=><option key={d.id} value={d.id}>{d.name} ({d.code})</option>)}
                </select>
              </div>
              <div className="field" style={{flex:'2 1 220px',margin:0}}>
                <label style={{fontSize:11,fontWeight:600,color:'var(--text-dim)',textTransform:'uppercase',letterSpacing:'.04em'}}>Search</label>
                <input placeholder="Sale #, distributor, customer..." value={filterSearch} onChange={e=>setFilterSearch(e.target.value)} />
              </div>
              <button className="btn" onClick={loadSales} style={{alignSelf:'flex-end'}}>Refresh</button>
            </div>

            {/* Distributor detail bar */}
            {selectedDistObj && (
              <div style={{display:'flex',gap:24,flexWrap:'wrap',background:'rgba(14,124,134,.05)',border:'1px solid rgba(14,124,134,.2)',borderRadius:6,padding:'10px 14px',marginBottom:14,fontSize:12}}>
                <span><strong>Code:</strong> {selectedDistObj.code}</span>
                <span><strong>Name:</strong> {selectedDistObj.name}</span>
                <span><strong>ID Card:</strong> {selectedDistObj.id_card || '—'}</span>
                <span><strong>Phone:</strong> {selectedDistObj.phone || '—'}</span>
                <span><strong>Commission Rate:</strong> Rs. {fmtNum(selectedDistObj.commission)} / pkt</span>
              </div>
            )}

            <div className="section-head">
              <h2>
                {filterDist ? (selectedDistObj?.name || 'Distributor') + ' — Sales' : 'All Distributor Sales'}
                {filterDate && <span style={{fontSize:12,fontWeight:400,color:'var(--text-dim)',marginLeft:10}}>{fmtDate(filterDate)}</span>}
              </h2>
              <span className="link" style={{fontSize:12}}>{displaySales.length} record{displaySales.length!==1?'s':''}</span>
            </div>

            {loading ? (
              <div style={{padding:20,color:'var(--text-dim)'}}>Loading sales...</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Sale #</th>
                    <th>Date</th>
                    <th>Distributor</th>
                    <th>Customer</th>
                    <th style={{textAlign:'center'}}>Packets</th>
                    <th style={{textAlign:'right'}}>Total</th>
                    <th style={{textAlign:'right'}}>Commission</th>
                    <th style={{textAlign:'right'}}>Adv.</th>
                    <th style={{textAlign:'right'}}>Welfare</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {displaySales.length === 0 ? (
                    <tr><td colSpan={11} style={{textAlign:'center',padding:20,color:'var(--text-dim)'}}>No sales found for selected filters.</td></tr>
                  ) : displaySales.map(s => {
                    const pkts = (s.sale_items || []).reduce((a, i) => a + Number(i.quantity), 0);
                    const comm = pkts * COMMISSION_PER_PACKET;
                    const adv  = pkts * ADVERTISEMENT_PER_PACKET;
                    const welf = pkts * WELFARE_PER_PACKET;
                    return (
                      <tr key={s.id}>
                        <td style={{fontWeight:600}}>{s.reference_number}</td>
                        <td>{fmtDate(s.sale_date)}</td>
                        <td>{distLabel(s)}</td>
                        <td>{s.customers?.name || '—'}</td>
                        <td style={{textAlign:'center'}}>{pkts}</td>
                        <td className="num-cell">Rs. {fmtNum(s.total_amount)}</td>
                        <td className="num-cell" style={{color:'var(--teal)'}}>Rs. {fmtNum(comm)}</td>
                        <td className="num-cell" style={{color:'var(--amber)'}}>Rs. {fmtNum(adv)}</td>
                        <td className="num-cell" style={{color:'var(--green)'}}>Rs. {fmtNum(welf)}</td>
                        <td><span className="badge green">{s.status}</span></td>
                        <td>
                          <div style={{display:'flex',gap:6}}>
                            <button className="btn" style={{padding:'3px 8px',fontSize:12}} onClick={()=>handlePrint(s)}>Print</button>
                            <button className="btn" style={{padding:'3px 8px',fontSize:12,background:'#25d366',color:'#fff',border:'none'}} onClick={()=>handleWhatsApp(s)}>WA</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                {displaySales.length > 0 && (
                  <tfoot>
                    <tr style={{background:'#f9f9f9',fontWeight:600}}>
                      <td colSpan={4}>Totals ({displaySales.length} sales)</td>
                      <td style={{textAlign:'center'}}>{totalPacketsToday}</td>
                      <td className="num-cell">Rs. {fmtNum(displaySales.reduce((a,s)=>a+Number(s.total_amount),0))}</td>
                      <td className="num-cell" style={{color:'var(--teal)'}}>Rs. {fmtNum(todayCommission)}</td>
                      <td className="num-cell" style={{color:'var(--amber)'}}>Rs. {fmtNum(todayAdvertisement)}</td>
                      <td className="num-cell" style={{color:'var(--green)'}}>Rs. {fmtNum(todayWelfare)}</td>
                      <td colSpan={2}></td>
                    </tr>
                  </tfoot>
                )}
              </table>
            )}
          </div>
        </>
      )}

      {/* ── CREATE SALE ─────────────────────────────────────────────── */}
      {activeTab === 'create' && (
        <div className="panel">
          <div className="section-head"><h2>Create New Sale</h2></div>
          <Msg msg={formMsg} />

          {/* Distributor selector */}
          <div style={{marginBottom:20,padding:14,background:'#FAFBF8',border:'1px solid var(--line)',borderRadius:6}}>
            <div style={{fontWeight:600,fontSize:13,marginBottom:10}}>Select Distributor *</div>
            {selDist ? (
              <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))',gap:10,background:'rgba(14,124,134,.05)',border:'1px solid rgba(14,124,134,.25)',borderRadius:6,padding:12}}>
                <div><div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.05em',color:'var(--text-dim)'}}>Code</div><div style={{fontWeight:600}}>{selDist.code}</div></div>
                <div><div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.05em',color:'var(--text-dim)'}}>Name</div><div style={{fontWeight:600}}>{selDist.name}</div></div>
                <div><div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.05em',color:'var(--text-dim)'}}>ID Card</div><div>{selDist.id_card || '—'}</div></div>
                <div><div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.05em',color:'var(--text-dim)'}}>Phone</div><div>{selDist.phone || '—'}</div></div>
                <div><div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.05em',color:'var(--text-dim)'}}>Commission Rate</div><div>Rs. {fmtNum(selDist.commission)} / pkt</div></div>
                <div style={{display:'flex',alignItems:'flex-end'}}>
                  <span className="link" style={{color:'var(--red)',fontSize:12}} onClick={()=>{setSelDist(null);setDistSearch('');}}>Change Distributor</span>
                </div>
              </div>
            ) : (
              <>
                <input
                  placeholder="Search by Code, Name, ID Card or Phone..."
                  value={distSearch}
                  onChange={e=>setDistSearch(e.target.value)}
                  style={{width:'100%',boxSizing:'border-box',marginBottom:8}}
                />
                {distSearch && (
                  <div style={{border:'1px solid var(--line)',borderRadius:4,maxHeight:200,overflowY:'auto',background:'#fff'}}>
                    {filteredDists.length === 0
                      ? <div style={{padding:10,fontSize:12,color:'var(--text-dim)'}}>No active distributors found.</div>
                      : filteredDists.map(d => (
                          <div key={d.id} onClick={()=>{setSelDist(d);setDistSearch('');}} style={{padding:'9px 12px',cursor:'pointer',borderBottom:'1px solid var(--line)',fontSize:13}}>
                            <span style={{fontWeight:600}}>{d.name}</span> <span style={{fontSize:11,color:'var(--text-dim)'}}>({d.code}) | {d.phone} | {d.id_card}</span>
                          </div>
                        ))
                    }
                  </div>
                )}
                {!distSearch && <p style={{fontSize:12,color:'var(--text-dim)',margin:0}}>Type to search active distributors.</p>}
              </>
            )}
          </div>

          {/* Product picker */}
          <div style={{border:'1px solid var(--line)',padding:14,borderRadius:6,background:'#fff',marginBottom:16}}>
            <div style={{fontWeight:600,fontSize:13,marginBottom:10}}>+ Add Product</div>
            <div className="form-grid">
              <div className="field">
                <label>Product</label>
                <select value={selProduct} onChange={e=>{setSelProduct(e.target.value);setSelPkg('');}}>
                  <option value="">-- Select --</option>
                  {products.length === 0
                    ? <option disabled>No products — add in Surf Product</option>
                    : products.map(p=><option key={p.id} value={p.id}>{p.name} ({p.code})</option>)
                  }
                </select>
              </div>
              <div className="field">
                <label>Packaging / Variant</label>
                <select value={selPkg} onChange={e=>setSelPkg(e.target.value)} disabled={!selProduct}>
                  <option value="">-- Select --</option>
                  {selProdObj?.product_packaging?.map(pk=>(
                    <option key={pk.id} value={pk.id}>{pk.name} (Rs. {pk.product_prices?.[0]?.sales_price || 0})</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Quantity</label>
                <input type="number" min="1" value={selQty} onChange={e=>setSelQty(e.target.value)} placeholder="Qty" />
              </div>
              <div className="field" style={{display:'flex',alignItems:'flex-end'}}>
                <button type="button" className="btn primary" onClick={handleAddItem} style={{width:'100%'}}>+ Add Item</button>
              </div>
            </div>
            {selPkg && (
              <div style={{marginTop:8,fontSize:12,color:'var(--text-dim)'}}>
                Price: Rs. {fmtNum(autoPrice)} per unit
                {selQty > 0 && <> &nbsp;|&nbsp; Amount: Rs. {fmtNum(Number(autoPrice) * Number(selQty))}</>}
              </div>
            )}
          </div>

          {/* Items table */}
          {items.length > 0 && (
            <div className="panel" style={{marginBottom:16,padding:12}}>
              <div style={{fontWeight:600,fontSize:13,marginBottom:10}}>Items Added</div>
              <table>
                <thead><tr><th>Product</th><th style={{textAlign:'center'}}>Qty</th><th style={{textAlign:'right'}}>Price</th><th style={{textAlign:'right'}}>Amount</th><th style={{textAlign:'right'}}>Commission</th><th></th></tr></thead>
                <tbody>
                  {items.map((item, i) => (
                    <tr key={i}>
                      <td>{item.name}</td>
                      <td style={{textAlign:'center'}}>{item.quantity}</td>
                      <td style={{textAlign:'right'}}>Rs. {fmtNum(item.price)}</td>
                      <td style={{textAlign:'right'}}>Rs. {fmtNum(item.price * item.quantity)}</td>
                      <td style={{textAlign:'right',color:'var(--teal)'}}>Rs. {fmtNum(item.quantity * COMMISSION_PER_PACKET)}</td>
                      <td style={{textAlign:'center'}}><span className="link" style={{color:'var(--red)',fontSize:12}} onClick={()=>removeItem(i)}>Remove</span></td>
                    </tr>
                  ))}
                  <tr style={{fontWeight:'bold',background:'#f9f9f9'}}>
                    <td colSpan={3} style={{textAlign:'right',paddingTop:8}}>Total</td>
                    <td style={{textAlign:'right',paddingTop:8,color:'var(--teal)'}}>Rs. {fmtNum(totalAmount)}</td>
                    <td style={{textAlign:'right',paddingTop:8,color:'var(--teal)'}}>Rs. {fmtNum(items.reduce((a,i)=>a+i.quantity*COMMISSION_PER_PACKET,0))}</td>
                    <td></td>
                  </tr>
                </tbody>
              </table>

              {/* Fee breakdown */}
              <div style={{marginTop:12,padding:10,background:'rgba(14,124,134,.04)',borderRadius:6,fontSize:12,display:'flex',gap:24,flexWrap:'wrap'}}>
                <span>📦 <strong>Packets:</strong> {items.reduce((a,i)=>a+i.quantity,0)}</span>
                <span style={{color:'var(--teal)'}}>💰 <strong>Commission ({COMMISSION_PER_PACKET} PKR/pkt):</strong> Rs. {fmtNum(items.reduce((a,i)=>a+i.quantity*COMMISSION_PER_PACKET,0))}</span>
                <span style={{color:'var(--amber)'}}>📢 <strong>Advertisement ({ADVERTISEMENT_PER_PACKET} PKR/pkt):</strong> Rs. {fmtNum(items.reduce((a,i)=>a+i.quantity*ADVERTISEMENT_PER_PACKET,0))}</span>
                <span style={{color:'var(--green)'}}>🤝 <strong>Welfare ({WELFARE_PER_PACKET} PKR/pkt):</strong> Rs. {fmtNum(items.reduce((a,i)=>a+i.quantity*WELFARE_PER_PACKET,0))}</span>
              </div>
            </div>
          )}

          {/* Required fields */}
          <div className="form-grid" style={{marginBottom:16}}>
            <div className="field">
              <label>Salesman *</label>
              <select value={salesmanId} onChange={e=>setSalesmanId(e.target.value)}>
                <option value="">-- None --</option>
                {salesmen.map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
              </select>
            </div>
            <div className="field">
              <label>Customer *</label>
              <select value={customerId} onChange={e=>setCustomerId(e.target.value)}>
                <option value="">-- None --</option>
                {customers.map(c=><option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}
              </select>
            </div>
          </div>

          <div className="btn-row">
            <button className="btn primary" onClick={handleSubmit} disabled={saving}>
              {saving ? 'Saving...' : 'Submit Sale'}
            </button>
            <button className="btn" onClick={()=>setActiveTab('list')}>Cancel</button>
          </div>
        </div>
      )}
    </>
  );
}

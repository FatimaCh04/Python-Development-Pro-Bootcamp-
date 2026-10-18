import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchDistributors,
  fetchProducts,
  fetchSales,
  fetchDistributorOutstanding,
  fetchDistributorTodayRecovery,
  submitSale
} from '../lib/db';
import { printDistributorPad, shareDistributorPadOnWhatsApp, formatPakistaniPhoneForWhatsApp } from '../lib/exportUtils';

// Default fallback rates (only used if distributor snapshot is missing)
const DEFAULT_ADVERTISEMENT_PER_PACKET = 20;
const DEFAULT_WELFARE_PER_PACKET       = 10;

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
  const [products,     setProducts]     = useState([]);

  // List state
  const [sales,        setSales]       = useState([]);
  const [loading,      setLoading]     = useState(false);
  const [allDates,     setAllDates]    = useState(false);
  const [msg,          setMsg]         = useState('');
  const [filterDate,   setFilterDate]  = useState(todayISO());
  const [filterDist,   setFilterDist]  = useState('');
  const [filterSearch, setFilterSearch] = useState('');

  // Distributor info panel (list view selected dist)
  const [distOutstanding,   setDistOutstanding]   = useState(null);
  const [distTodayRecovery, setDistTodayRecovery] = useState(null);

  // WhatsApp share state
  const [sharingSaleId, setSharingSaleId] = useState(null);
  const [shareModal,    setShareModal]    = useState(null);

  // Create form state
  const [selDist,    setSelDist]    = useState(null);
  const [distSearch, setDistSearch] = useState('');
  const [items,      setItems]      = useState([]);
  const [saving,     setSaving]     = useState(false);
  const [formMsg,    setFormMsg]    = useState('');

  // Item picker
  const [selProduct, setSelProduct] = useState('');
  const [selPkg,     setSelPkg]     = useState('');
  const [selQty,     setSelQty]     = useState('');

  // ── Load reference data once ──────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const [d, p] = await Promise.all([
          fetchDistributors(), fetchProducts()
        ]);
        setDistributors(d || []);
        setProducts(p || []);
      } catch (e) { console.error(e); }
    })();
  }, []);

  // ── Load sales (with filters) ─────────────────────────────────────────────
  const loadSales = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchSales({
        dateFrom: (!allDates && filterDate) ? dayStart(filterDate) : undefined,
        dateTo:   (!allDates && filterDate) ? dayEnd(filterDate)   : undefined,
        distributorId: filterDist || undefined
      });
      setSales(data || []);
    } catch (e) {
      console.error(e);
      setMsg('err:Failed to load sales.');
    }
    setLoading(false);
  }, [filterDate, filterDist, allDates]);

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

  // ── Summary tiles — derived from snapshot rates per row ──────────────────
  const selectedDistObj = distributors.find(d => d.id === filterDist);

  // Total packets across currently displayed sales
  const totalPackets = sales.reduce((sum, s) =>
    sum + (s.sale_items || []).reduce((a, i) => a + Number(i.quantity), 0), 0
  );

  // Commission today: sum per row using snapshot rate (or selectedDistObj.commission fallback)
  const todayCommission = sales.reduce((sum, s) => {
    const pkts = (s.sale_items || []).reduce((a, i) => a + Number(i.quantity), 0);
    const rate = s.commission_rate_snapshot != null
      ? Number(s.commission_rate_snapshot)
      : (selectedDistObj?.commission != null ? Number(selectedDistObj.commission) : 0);
    return sum + pkts * rate;
  }, 0);

  const todayAdvertisement = totalPackets * DEFAULT_ADVERTISEMENT_PER_PACKET;
  const todayWelfare       = totalPackets * DEFAULT_WELFARE_PER_PACKET;

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
  const selProdObj = products.find(p => p.id === selProduct);
  const selPkgObj  = selProdObj?.product_packaging?.find(pk => pk.id === selPkg);
  const autoPrice  = selPkgObj?.product_prices?.[0]?.sales_price || 0;

  const handleAddItem = () => {
    if (!selProduct || !selPkg) {
      setFormMsg('err:Select a product and packaging.');
      return;
    }
    const qty = parseInt(selQty, 10);
    if (!qty || qty < 1) {
      setFormMsg('err:Enter a valid quantity (greater than 0).');
      return;
    }
    if (!autoPrice || Number(autoPrice) <= 0) {
      setFormMsg('err:Selected packaging has no valid price.');
      return;
    }
    const name = (selProdObj?.name || '') + (selPkgObj?.name ? ' — ' + selPkgObj.name : '');
    setItems([...items, { packagingId: selPkg, name, price: Number(autoPrice), quantity: qty }]);
    setSelProduct(''); setSelPkg(''); setSelQty('');
    setFormMsg('');
  };

  const removeItem = (i) => setItems(items.filter((_, idx) => idx !== i));
  const totalAmount = items.reduce((s, i) => s + i.price * i.quantity, 0);

  // Commission preview in create form — uses selDist.commission
  const createCommRate = selDist?.commission != null ? Number(selDist.commission) : 0;
  const totalItemPkts  = items.reduce((a, i) => a + i.quantity, 0);

  // ── Save sale ─────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!selDist) {
      setFormMsg('err:Please select a distributor.');
      return;
    }
    if (items.length === 0) {
      setFormMsg('err:Add at least one product item.');
      return;
    }
    const invalidItem = items.find(i => i.quantity <= 0 || i.price <= 0);
    if (invalidItem) {
      setFormMsg(`err:Item "${invalidItem.name}" has invalid qty or price.`);
      return;
    }
    setSaving(true);
    setFormMsg('');
    try {
      await submitSale({
        distributorId: selDist.id,
        salesmanId: null,
        customerId: null,
        items,
        totalAmount,
        saleDate: new Date().toISOString()
      });
      setFormMsg('ok:Sale recorded successfully.');
      setSelDist(null); setDistSearch('');
      setItems([]); setSelProduct(''); setSelPkg(''); setSelQty('');
      await loadSales();
      setTimeout(() => { setActiveTab('list'); setFormMsg(''); }, 1500);
    } catch (e) {
      setFormMsg('err:' + (e.message || 'Failed to submit sale.'));
    } finally {
      setSaving(false);
    }
  };

  // ── WhatsApp PDF share workflow ───────────────────────────────────────────
  const handleWhatsApp = async (s) => {
    let targetWindow = null;
    if (typeof window !== 'undefined') {
      targetWindow = window.open('about:blank', '_blank');
    }

    try {
      const distObj = (Array.isArray(s.distributors) ? s.distributors[0] : s.distributors)
        || distributors.find(d => d.id === s.distributor_id)
        || null;

      if (!distObj) {
        if (targetWindow && !targetWindow.closed) {
          try { targetWindow.close(); } catch (_) {}
        }
        const warn = 'Cannot open WhatsApp: No distributor is linked to this sale.';
        setMsg('err:' + warn);
        if (typeof alert === 'function') alert(warn);
        return;
      }

      const formattedPhone = formatPakistaniPhoneForWhatsApp(distObj.phone);
      if (!formattedPhone) {
        if (targetWindow && !targetWindow.closed) {
          try { targetWindow.close(); } catch (_) {}
        }
        const warn = `Cannot open WhatsApp: Distributor ${distObj.name || ''} has no valid registered phone number.`;
        setMsg('err:' + warn);
        if (typeof alert === 'function') alert(warn);
        return;
      }

      setSharingSaleId(s.id);
      setMsg(`ok:Opening WhatsApp & generating signed delivery PDF for ${s.reference_number}...`);

      const mappedSale = {
        ...s,
        billNo: s.reference_number,
        date: fmtDate(s.sale_date),
        distributorName: distObj?.name || '—',
        distributorCode: distObj?.code || '',
        items: (s.sale_items || []).map(i => ({
          description: i.product_packaging?.name ? `Elite Wash Surf (${i.product_packaging.name})` : 'Elite Wash Surf',
          quantity: i.quantity,
          unit_price: i.unit_price,
          amount: Number(i.quantity || 0) * Number(i.unit_price || 0)
        })),
        totalAmount: s.total_amount
      };

      await shareDistributorPadOnWhatsApp({
        sale: mappedSale,
        distributor: distObj,
        targetWindow,
        onProgress: (statusText) => setMsg('ok:' + statusText),
        onSuccess: (successMsg, details) => {
          setMsg('ok:' + successMsg);
          if (details && details.mode === 'download_and_chat') {
            setShareModal({
              sale: mappedSale,
              distName: distObj.name,
              phone: formattedPhone,
              filename: details.filename,
              waUrl: details.waUrl,
              popupBlocked: details.popupBlocked
            });
          }
        },
        onError: (errMsg) => {
          if (targetWindow && !targetWindow.closed) {
            try { targetWindow.close(); } catch (_) {}
          }
          setMsg('err:' + errMsg);
          if (typeof alert === 'function') alert(errMsg);
        }
      });
    } catch (e) {
      if (targetWindow && !targetWindow.closed) {
        try { targetWindow.close(); } catch (_) {}
      }
      setMsg('err:Failed to generate or share delivery PDF: ' + e.message);
    } finally {
      setSharingSaleId(null);
    }
  };

  // ── Print ─────────────────────────────────────────────────────────────────
  const handlePrint = (s) => {
    const mappedSale = {
      ...s,
      billNo: s.reference_number,
      date: fmtDate(s.sale_date),
      distributorName: s.distributors?.name || '—',
      items: (s.sale_items || []).map(i => ({
        description: i.product_packaging?.name ? `Elite Wash Surf (${i.product_packaging.name})` : 'Elite Wash Surf',
        quantity: i.quantity,
        unit_price: i.unit_price,
        amount: Number(i.quantity || 0) * Number(i.unit_price || 0)
      })),
      totalAmount: s.total_amount
    };
    printDistributorPad(mappedSale);
  };

  // ── Client search filter ──────────────────────────────────────────────────
  const sq = (filterSearch || searchTerm).toLowerCase();
  const displaySales = sq
    ? sales.filter(s =>
        s.reference_number?.toLowerCase().includes(sq) ||
        s.distributors?.name?.toLowerCase().includes(sq) ||
        s.distributors?.code?.toLowerCase().includes(sq)
      )
    : sales;

  const distLabel = (s) => {
    if (!s.distributors) return <span style={{color:'var(--text-dim)',fontStyle:'italic'}}>Not Assigned</span>;
    return <span>{s.distributors.name} <span style={{fontSize:11,color:'var(--text-dim)'}}>({s.distributors.code})</span></span>;
  };

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
                <div className="label">{distOutstanding?.advanceBalance > 0 ? 'Advance Credit Held' : 'Outstanding Balance'}</div>
                <div className="num">
                  Rs. {distOutstanding !== null ? fmtNum(distOutstanding.advanceBalance > 0 ? distOutstanding.advanceBalance : distOutstanding.outstanding) : '…'}
                </div>
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
                <div style={{fontSize:10,color:'rgba(255,255,255,.7)',marginTop:4}}>{totalPackets} pkts (snapshot rates)</div>
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
                <input type="date" value={filterDate} onChange={e=>setFilterDate(e.target.value)} disabled={allDates} />
                <label style={{fontSize:11,marginTop:4,display:'flex',alignItems:'center',gap:4,cursor:'pointer'}}>
                  <input type="checkbox" checked={allDates} onChange={e=>setAllDates(e.target.checked)} style={{margin:0}} />
                  All Dates
                </label>
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
                <input placeholder="Sale #, distributor name or code..." value={filterSearch} onChange={e=>setFilterSearch(e.target.value)} />
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
                {!allDates && filterDate && <span style={{fontSize:12,fontWeight:400,color:'var(--text-dim)',marginLeft:10}}>{fmtDate(filterDate)}</span>}
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
                    <th style={{textAlign:'center'}}>Packets</th>
                    <th style={{textAlign:'right'}}>Total</th>
                    <th style={{textAlign:'right'}}>Commission</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {displaySales.length === 0 ? (
                    <tr><td colSpan={8} style={{textAlign:'center',padding:20,color:'var(--text-dim)'}}>No sales found for selected filters.</td></tr>
                  ) : displaySales.map(s => {
                    const pkts = (s.sale_items || []).reduce((a, i) => a + Number(i.quantity), 0);
                    const commRate = s.commission_rate_snapshot ?? null;
                    let commCell;
                    if (commRate === null) {
                      commCell = <span className="badge amber">No Snapshot</span>;
                    } else {
                      commCell = <span style={{color:'var(--teal)'}}>Rs. {fmtNum(pkts * Number(commRate))}</span>;
                    }
                    return (
                      <tr key={s.id}>
                        <td style={{fontWeight:600}}>{s.reference_number}</td>
                        <td>{fmtDate(s.sale_date)}</td>
                        <td>{distLabel(s)}</td>
                        <td style={{textAlign:'center'}}>{pkts}</td>
                        <td className="num-cell">Rs. {fmtNum(s.total_amount)}</td>
                        <td className="num-cell">{commCell}</td>
                        <td><span className="badge green">{s.status}</span></td>
                        <td>
                          <div style={{display:'flex',gap:6}}>
                            <button className="btn" style={{padding:'3px 8px',fontSize:12}} onClick={()=>handlePrint(s)}>Print</button>
                            <button
                              className="btn"
                              style={{
                                padding:'3px 8px',
                                fontSize:12,
                                background:'#25d366',
                                color:'#fff',
                                border:'none',
                                opacity: sharingSaleId === s.id ? 0.7 : 1,
                                cursor: sharingSaleId === s.id ? 'wait' : 'pointer'
                              }}
                              disabled={sharingSaleId === s.id}
                              onClick={()=>handleWhatsApp(s)}
                              title="Share complete signed delivery PDF receipt on WhatsApp"
                            >
                              {sharingSaleId === s.id ? 'PDF...' : 'WA'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                {displaySales.length > 0 && (
                  <tfoot>
                    <tr style={{background:'#f9f9f9',fontWeight:600}}>
                      <td colSpan={3}>Totals ({displaySales.length} sales)</td>
                      <td style={{textAlign:'center'}}>{totalPackets}</td>
                      <td className="num-cell">Rs. {fmtNum(displaySales.reduce((a,s)=>a+Number(s.total_amount),0))}</td>
                      <td className="num-cell" style={{color:'var(--teal)'}}>Rs. {fmtNum(todayCommission)}</td>
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
                {Number(selQty) > 0 && <> &nbsp;|&nbsp; Amount: Rs. {fmtNum(Number(autoPrice) * Number(selQty))}</>}
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
                      <td style={{textAlign:'right',color:'var(--teal)'}}>
                        {selDist
                          ? `Rs. ${fmtNum(item.quantity * createCommRate)}`
                          : <span style={{color:'var(--text-dim)',fontSize:11}}>Select dist.</span>
                        }
                      </td>
                      <td style={{textAlign:'center'}}><span className="link" style={{color:'var(--red)',fontSize:12}} onClick={()=>removeItem(i)}>Remove</span></td>
                    </tr>
                  ))}
                  <tr style={{fontWeight:'bold',background:'#f9f9f9'}}>
                    <td colSpan={3} style={{textAlign:'right',paddingTop:8}}>Total</td>
                    <td style={{textAlign:'right',paddingTop:8,color:'var(--teal)'}}>Rs. {fmtNum(totalAmount)}</td>
                    <td style={{textAlign:'right',paddingTop:8,color:'var(--teal)'}}>
                      {selDist ? `Rs. ${fmtNum(totalItemPkts * createCommRate)}` : '—'}
                    </td>
                    <td></td>
                  </tr>
                </tbody>
              </table>

              {/* Fee breakdown */}
              <div style={{marginTop:12,padding:10,background:'rgba(14,124,134,.04)',borderRadius:6,fontSize:12,display:'flex',gap:24,flexWrap:'wrap'}}>
                <span>📦 <strong>Packets:</strong> {totalItemPkts}</span>
                {selDist ? (
                  <span style={{color:'var(--teal)'}}>💰 <strong>Commission ({fmtNum(createCommRate)} PKR/pkt):</strong> Rs. {fmtNum(totalItemPkts * createCommRate)}</span>
                ) : (
                  <span style={{color:'var(--text-dim)'}}>💰 Commission: select a distributor to preview</span>
                )}
                <span style={{color:'var(--amber)'}}>📢 <strong>Advertisement ({DEFAULT_ADVERTISEMENT_PER_PACKET} PKR/pkt):</strong> Rs. {fmtNum(totalItemPkts * DEFAULT_ADVERTISEMENT_PER_PACKET)}</span>
                <span style={{color:'var(--green)'}}>🤝 <strong>Welfare ({DEFAULT_WELFARE_PER_PACKET} PKR/pkt):</strong> Rs. {fmtNum(totalItemPkts * DEFAULT_WELFARE_PER_PACKET)}</span>
              </div>
            </div>
          )}

          {/* Submit */}
          <div className="btn-row">
            <button className="btn primary" onClick={handleSubmit} disabled={saving}>
              {saving ? 'Saving...' : 'Submit Sale'}
            </button>
            <button className="btn" onClick={()=>setActiveTab('list')}>Cancel</button>
          </div>
        </div>
      )}

      {/* ── WHATSAPP SHARE INSTRUCTIONS MODAL ──────────────────────────── */}
      {shareModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="panel" style={{ width: 500, maxWidth: '92%', padding: 24, boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, borderBottom: '1px solid var(--line)', paddingBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#25d366', color: '#fff', display: 'grid', placeItems: 'center', fontWeight: 'bold' }}>✓</div>
                <div>
                  <h3 style={{ margin: 0, fontSize: 16 }}>Delivery Receipt PDF Ready to Share</h3>
                  <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>{shareModal.distName} &bull; +{shareModal.phone}</div>
                </div>
              </div>
              <button className="btn ghost" style={{ padding: '4px 8px' }} onClick={() => setShareModal(null)}>✕</button>
            </div>

            <div style={{ background: '#FAFBF8', border: '1px solid var(--line)', borderRadius: 6, padding: 14, fontSize: 13, lineHeight: 1.6, marginBottom: 16 }}>
              <div style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 18 }}>📄</span>
                <div>
                  <strong>Downloaded Delivery Slip:</strong>
                  <div style={{ color: 'var(--teal)', fontWeight: 600 }}>{shareModal.filename}</div>
                </div>
              </div>
              <div style={{ padding: '10px 12px', background: '#FFF8E7', border: '1px solid #F0D78C', borderRadius: 6, fontSize: 12.5, color: '#856404' }}>
                <strong>How to complete sending on WhatsApp:</strong>
                <ol style={{ margin: '6px 0 0 16px', padding: 0 }}>
                  <li>WhatsApp chat with <strong>{shareModal.distName}</strong> (+{shareModal.phone}) opens in your browser.</li>
                  <li>In WhatsApp, click the <strong>attach icon (📎) &rarr; Document</strong>.</li>
                  <li>Select the downloaded <strong>{shareModal.filename}</strong> from your Downloads folder.</li>
                  <li>Click <strong>Send</strong> to deliver the signed bill pad receipt.</li>
                </ol>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
              <button
                className="btn primary"
                style={{ fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 6 }}
                onClick={() => window.open(shareModal.waUrl, '_blank')}
              >
                <span>💬</span> Open WhatsApp Chat
              </button>
              <button className="btn ghost" onClick={() => setShareModal(null)}>
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

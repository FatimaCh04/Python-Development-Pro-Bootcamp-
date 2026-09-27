import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchBookings,
  fetchCustomers,
  fetchSalesmen,
  fetchProducts,
  fetchDistributors,
  submitBooking,
  addBookingRecovery
} from '../lib/db';

const fmtNum = (n) => Number(n || 0).toLocaleString('en-PK');
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';
const todayISO = () => new Date().toISOString().split('T')[0];
const dayStart = (d) => `${d}T00:00:00.000Z`;
const dayEnd   = (d) => `${d}T23:59:59.999Z`;

function Msg({ msg }) {
  if (!msg) return null;
  const isErr = msg.startsWith('err:');
  return (
    <div style={{
      padding: '8px 12px', marginBottom: 12, borderRadius: 4, fontSize: 12,
      background: isErr ? 'var(--red-soft)' : 'var(--green-soft)',
      color: isErr ? 'var(--red)' : 'var(--green)'
    }}>
      {msg.replace(/^(ok|err):/, '')}
    </div>
  );
}

export default function BookingPage() {
  const { role } = useAuth();

  // Tab state
  const [activeTab, setActiveTab] = useState('list');

  // Data
  const [bookings, setBookings]         = useState([]);
  const [distributors, setDistributors] = useState([]);
  const [customers, setCustomers]       = useState([]);
  const [salesmen, setSalesmen]         = useState([]);
  const [products, setProducts]         = useState([]);
  const [loading, setLoading]           = useState(false);
  const [msg, setMsg]                   = useState('');

  // Filters (list view)
  const [filterDate, setFilterDate]             = useState(todayISO());
  const [filterDistributor, setFilterDistributor] = useState('');   // '' = all
  const [filterSearch, setFilterSearch]           = useState('');

  // Create booking form states
  const [distSearch, setDistSearch]         = useState('');
  const [selectedDistributor, setSelectedDistributor] = useState(null); // full object
  const [selectedCustomer, setSelectedCustomer]       = useState('');
  const [selectedSalesman, setSelectedSalesman]       = useState('');
  const [selectedProduct, setSelectedProduct]         = useState('');
  const [selectedPackaging, setSelectedPackaging]     = useState('');
  const [quantity, setQuantity]                       = useState('');

  // Recovery Modal
  const [showRecovery, setShowRecovery]     = useState(false);
  const [recoveryBooking, setRecoveryBooking] = useState(null);
  const [recoveryAmount, setRecoveryAmount] = useState('');
  const [paymentMethod, setPaymentMethod]   = useState('Cash');

  // ── Load static reference data once ──────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const [cData, sData, pData, dData] = await Promise.all([
          fetchCustomers(),
          fetchSalesmen(),
          fetchProducts(),
          fetchDistributors()
        ]);
        setCustomers(cData || []);
        setSalesmen(sData || []);
        setProducts(pData || []);
        setDistributors(dData || []);
      } catch (e) { console.error(e); }
    })();
  }, []);

  // ── Load bookings whenever filters change ─────────────────────────────────
  const loadBookings = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchBookings({
        dateFrom: filterDate ? dayStart(filterDate) : undefined,
        dateTo:   filterDate ? dayEnd(filterDate)   : undefined,
        distributorId: filterDistributor || undefined
      });
      setBookings(data || []);
    } catch (e) {
      console.error(e);
      setMsg('err:Failed to load bookings.');
    }
    setLoading(false);
  }, [filterDate, filterDistributor]);

  useEffect(() => { loadBookings(); }, [loadBookings]);

  // ── Derived: product pricing ──────────────────────────────────────────────
  const selectedProdObj = products.find(p => p.id === selectedProduct);
  const selectedPkgObj  = selectedProdObj?.product_packaging?.find(pk => pk.id === selectedPackaging);
  const unitPrice       = selectedPkgObj?.product_prices?.[0]?.sales_price || 0;
  const totalAmount     = unitPrice * (Number(quantity) || 0);

  // ── Distributor search (for create form) ─────────────────────────────────
  const activeDistributors  = distributors.filter(d => d.is_active);
  const distSearchLower     = distSearch.toLowerCase();
  const filteredDists       = distSearch
    ? activeDistributors.filter(d =>
        d.code?.toLowerCase().includes(distSearchLower) ||
        d.name?.toLowerCase().includes(distSearchLower) ||
        d.id_card?.toLowerCase().includes(distSearchLower) ||
        d.phone?.toLowerCase().includes(distSearchLower)
      )
    : activeDistributors;

  function handleSelectDist(d) {
    setSelectedDistributor(d);
    setDistSearch('');
  }

  function handleClearDist() {
    setSelectedDistributor(null);
    setDistSearch('');
  }

  // ── Save booking ──────────────────────────────────────────────────────────
  async function handleSaveBooking() {
    if (!selectedDistributor) { setMsg('err:Please select a distributor.'); return; }
    if (!selectedPackaging)   { setMsg('err:Please select a product and packaging.'); return; }
    if (!quantity || Number(quantity) <= 0) { setMsg('err:Please enter a valid quantity.'); return; }

    try {
      setLoading(true); setMsg('');
      await submitBooking({
        distributorId: selectedDistributor.id,
        customerId:    selectedCustomer  || null,
        salesmanId:    selectedSalesman  || null,
        items: [{ packagingId: selectedPackaging, quantity: Number(quantity), price: unitPrice }],
        totalAmount
      });
      setMsg('ok:Booking saved successfully.');
      // Reset form
      setSelectedDistributor(null); setDistSearch('');
      setSelectedCustomer(''); setSelectedSalesman('');
      setSelectedProduct(''); setSelectedPackaging(''); setQuantity('');
      await loadBookings();
      setTimeout(() => { setActiveTab('list'); setMsg(''); }, 1500);
    } catch (e) {
      setMsg('err:' + e.message);
    } finally { setLoading(false); }
  }

  // ── Save recovery ─────────────────────────────────────────────────────────
  async function handleSaveRecovery() {
    if (!recoveryAmount || Number(recoveryAmount) <= 0) { setMsg('err:Amount must be greater than zero.'); return; }
    if (Number(recoveryAmount) > recoveryBooking.remaining_balance) { setMsg('err:Amount exceeds remaining balance.'); return; }
    try {
      setLoading(true); setMsg('');
      await addBookingRecovery({
        bookingId:     recoveryBooking.id,
        customerId:    recoveryBooking.customer_id,
        salesmanId:    recoveryBooking.salesman_id,
        amount:        recoveryAmount,
        paymentMethod
      });
      setMsg('ok:Recovery added successfully.');
      await loadBookings();
      setTimeout(() => { setShowRecovery(false); setMsg(''); }, 1500);
    } catch (e) {
      setMsg('err:' + e.message);
    } finally { setLoading(false); }
  }

  // ── WhatsApp share ────────────────────────────────────────────────────────
  function handleWhatsApp(b) {
    const dist  = b.distributors ? `${b.distributors.name} (${b.distributors.code})` : 'Not Assigned';
    const text  = encodeURIComponent(
      `*Elite Wash — Booking Ledger*\n` +
      `Booking: ${b.reference_number}\n` +
      `Date: ${fmtDate(b.sale_date)}\n` +
      `Distributor: ${dist}\n` +
      `Total: Rs. ${fmtNum(b.total_amount)}\n` +
      `Recovered: Rs. ${fmtNum(b.total_recovered)}\n` +
      `Remaining: Rs. ${fmtNum(b.remaining_balance)}\n` +
      `Status: ${b.status}`
    );
    window.open(`https://wa.me/923240106056?text=${text}`, '_blank');
  }

  // ── Print booking ─────────────────────────────────────────────────────────
  function handlePrint(b) {
    const dist = b.distributors
      ? `${b.distributors.name} | ${b.distributors.code} | ${b.distributors.id_card || ''} | ${b.distributors.phone || ''}`
      : 'Not Assigned';
    const win = window.open('', '_blank');
    win.document.write(`
      <html><head><title>Booking ${b.reference_number}</title>
      <style>body{font-family:sans-serif;padding:20px}h2{margin-bottom:4px}table{width:100%;border-collapse:collapse;margin-top:12px}td,th{border:1px solid #ccc;padding:8px;font-size:13px}th{background:#f5f5f5}</style></head>
      <body>
        <h2>Elite Wash — Booking Ledger</h2>
        <p><strong>Booking #:</strong> ${b.reference_number} &nbsp; <strong>Date:</strong> ${fmtDate(b.sale_date)} &nbsp; <strong>Status:</strong> ${b.status}</p>
        <p><strong>Distributor:</strong> ${dist}</p>
        <p><strong>Customer:</strong> ${b.customers?.name || '—'}</p>
        <table>
          <tr><th>Total Amount</th><th>Recovered</th><th>Remaining Balance</th></tr>
          <tr><td>Rs. ${fmtNum(b.total_amount)}</td><td>Rs. ${fmtNum(b.total_recovered)}</td><td>Rs. ${fmtNum(b.remaining_balance)}</td></tr>
        </table>
        <br/><p style="font-size:11px;color:#999">Elite Wash ERP — All balances derived from transactions.</p>
      </body></html>
    `);
    win.document.close();
    win.print();
  }

  // ── Client-side search filter (on top of date/distributor DB filter) ──────
  const displayBookings = filterSearch
    ? bookings.filter(b => {
        const s = filterSearch.toLowerCase();
        return (
          b.reference_number?.toLowerCase().includes(s) ||
          b.distributors?.name?.toLowerCase().includes(s) ||
          b.distributors?.code?.toLowerCase().includes(s) ||
          b.customers?.name?.toLowerCase().includes(s)
        );
      })
    : bookings;

  // ── Helper to show distributor label in list ──────────────────────────────
  function distLabel(b) {
    if (!b.distributors) return <span style={{color:'var(--text-dim)',fontStyle:'italic'}}>Not Assigned</span>;
    return <span>{b.distributors.name} <span style={{fontSize:11,color:'var(--text-dim)'}}>({b.distributors.code})</span></span>;
  }

  // ── RENDER ────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Tabs */}
      <div className="panel" style={{marginBottom:20}}>
        <div className="tabs">
          <div className={`tab${activeTab==='list'?' active':''}`}   onClick={()=>setActiveTab('list')}>Booking Ledger</div>
          <div className={`tab${activeTab==='create'?' active':''}`} onClick={()=>setActiveTab('create')}>Create Booking</div>
        </div>
      </div>

      <Msg msg={msg} />

      {/* ── BOOKING LIST ────────────────────────────────────────────── */}
      {activeTab === 'list' && (
        <div className="panel">
          {/* Filters row */}
          <div style={{display:'flex',gap:12,flexWrap:'wrap',alignItems:'flex-end',marginBottom:16}}>
            <div className="field" style={{flex:'1 1 160px',margin:0}}>
              <label style={{fontSize:11,fontWeight:600,color:'var(--text-dim)',textTransform:'uppercase',letterSpacing:'.04em'}}>Date</label>
              <input type="date" value={filterDate} onChange={e=>setFilterDate(e.target.value)} />
            </div>
            <div className="field" style={{flex:'1 1 180px',margin:0}}>
              <label style={{fontSize:11,fontWeight:600,color:'var(--text-dim)',textTransform:'uppercase',letterSpacing:'.04em'}}>Distributor</label>
              <select value={filterDistributor} onChange={e=>setFilterDistributor(e.target.value)}>
                <option value="">All Distributors</option>
                {distributors.map(d=><option key={d.id} value={d.id}>{d.name} ({d.code})</option>)}
              </select>
            </div>
            <div className="field" style={{flex:'2 1 220px',margin:0}}>
              <label style={{fontSize:11,fontWeight:600,color:'var(--text-dim)',textTransform:'uppercase',letterSpacing:'.04em'}}>Search</label>
              <input placeholder="Booking #, distributor, customer..." value={filterSearch} onChange={e=>setFilterSearch(e.target.value)} />
            </div>
            <button className="btn" onClick={loadBookings} style={{alignSelf:'flex-end'}}>Refresh</button>
          </div>

          <div className="section-head">
            <h2>
              {filterDistributor
                ? (distributors.find(d=>d.id===filterDistributor)?.name || 'Distributor') + ' — Bookings'
                : 'All Distributor Bookings'}
              {filterDate && <span style={{fontSize:12,fontWeight:400,color:'var(--text-dim)',marginLeft:10}}>{fmtDate(filterDate)}</span>}
            </h2>
            <span className="link" style={{fontSize:12}}>{displayBookings.length} record{displayBookings.length!==1?'s':''}</span>
          </div>

          {loading ? (
            <div style={{padding:20,color:'var(--text-dim)'}}>Loading bookings...</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Booking #</th>
                  <th>Date</th>
                  <th>Distributor</th>
                  <th>Customer</th>
                  <th style={{textAlign:'right'}}>Total</th>
                  <th style={{textAlign:'right'}}>Recovered</th>
                  <th style={{textAlign:'right'}}>Remaining</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {displayBookings.length === 0 ? (
                  <tr><td colSpan={9} style={{textAlign:'center',padding:20,color:'var(--text-dim)'}}>No bookings found for selected filters.</td></tr>
                ) : displayBookings.map(b => (
                  <tr key={b.id}>
                    <td style={{fontWeight:600}}>{b.reference_number}</td>
                    <td>{fmtDate(b.sale_date)}</td>
                    <td>{distLabel(b)}</td>
                    <td>{b.customers?.name || '—'}</td>
                    <td className="num-cell">Rs. {fmtNum(b.total_amount)}</td>
                    <td className="num-cell" style={{color:'var(--green)'}}>Rs. {fmtNum(b.total_recovered)}</td>
                    <td className="num-cell" style={{color:b.remaining_balance>0?'var(--amber)':'var(--green)'}}>Rs. {fmtNum(b.remaining_balance)}</td>
                    <td><span className={`badge ${b.remaining_balance<=0?'green':'amber'}`}>{b.remaining_balance<=0?'Cleared':b.status}</span></td>
                    <td>
                      <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
                        {b.remaining_balance > 0 && (
                          <button className="btn" style={{padding:'3px 10px',fontSize:12}} onClick={()=>{
                            setRecoveryBooking(b);
                            setRecoveryAmount(b.remaining_balance);
                            setPaymentMethod('Cash');
                            setShowRecovery(true);
                            setMsg('');
                          }}>Recovery</button>
                        )}
                        <button className="btn" style={{padding:'3px 10px',fontSize:12}} onClick={()=>handlePrint(b)}>Print</button>
                        <button className="btn" style={{padding:'3px 10px',fontSize:12,background:'#25d366',color:'#fff',border:'none'}} onClick={()=>handleWhatsApp(b)}>WA</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── CREATE BOOKING ─────────────────────────────────────────── */}
      {activeTab === 'create' && (
        <div className="panel">
          <div className="section-head"><h2>Create New Booking</h2></div>

          {/* Distributor Search & Select */}
          <div style={{marginBottom:20,padding:14,background:'#FAFBF8',border:'1px solid var(--line)',borderRadius:6}}>
            <div style={{fontWeight:600,fontSize:13,marginBottom:10}}>Select Distributor *</div>
            {selectedDistributor ? (
              <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))',gap:10,background:'rgba(14,124,134,.05)',border:'1px solid rgba(14,124,134,.25)',borderRadius:6,padding:12}}>
                <div><div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.05em',color:'var(--text-dim)'}}>Code</div><div style={{fontWeight:600}}>{selectedDistributor.code}</div></div>
                <div><div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.05em',color:'var(--text-dim)'}}>Name</div><div style={{fontWeight:600}}>{selectedDistributor.name}</div></div>
                <div><div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.05em',color:'var(--text-dim)'}}>ID Card</div><div>{selectedDistributor.id_card || '—'}</div></div>
                <div><div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.05em',color:'var(--text-dim)'}}>Phone</div><div>{selectedDistributor.phone || '—'}</div></div>
                <div style={{display:'flex',alignItems:'flex-end'}}>
                  <span className="link" style={{color:'var(--red)',fontSize:12}} onClick={handleClearDist}>Change Distributor</span>
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
                  <div style={{border:'1px solid var(--line)',borderRadius:4,maxHeight:220,overflowY:'auto',background:'#fff'}}>
                    {filteredDists.length === 0 ? (
                      <div style={{padding:10,fontSize:12,color:'var(--text-dim)'}}>No active distributors found.</div>
                    ) : filteredDists.map(d => (
                      <div key={d.id} onClick={()=>handleSelectDist(d)} style={{padding:'9px 12px',cursor:'pointer',borderBottom:'1px solid var(--line)',fontSize:13}} className="dist-row">
                        <span style={{fontWeight:600}}>{d.name}</span> <span style={{fontSize:11,color:'var(--text-dim)'}}>({d.code}) | {d.phone} | {d.id_card}</span>
                      </div>
                    ))}
                  </div>
                )}
                {!distSearch && <p style={{fontSize:12,color:'var(--text-dim)',margin:0}}>Type to search active distributors.</p>}
              </>
            )}
          </div>

          {/* Product & Quantity */}
          <div className="form-grid">
            <div className="field">
              <label>Surf Product</label>
              <select value={selectedProduct} onChange={e=>{setSelectedProduct(e.target.value);setSelectedPackaging('');}}>
                <option value="">-- Select Product --</option>
                {products.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              {products.length===0 && <span style={{fontSize:11,color:'var(--amber)'}}>No products — add in Surf Product</span>}
            </div>

            <div className="field">
              <label>Packaging / Variant</label>
              <select value={selectedPackaging} onChange={e=>setSelectedPackaging(e.target.value)} disabled={!selectedProduct}>
                <option value="">-- Select Packaging --</option>
                {selectedProdObj?.product_packaging?.map(pkg=>(
                  <option key={pkg.id} value={pkg.id}>{pkg.name} — Rs. {pkg.product_prices?.[0]?.sales_price || 0} / unit</option>
                ))}
              </select>
            </div>

            <div className="field">
              <label>Quantity (packets)</label>
              <input type="number" min="1" value={quantity} onChange={e=>setQuantity(e.target.value)} placeholder="e.g. 50" />
            </div>

            <div className="field">
              <label>Price per Packet (Rs.)</label>
              <input type="text" value={selectedPackaging ? `Rs. ${fmtNum(unitPrice)}` : '—'} disabled style={{background:'#f9f9f9',color:'var(--ink)'}} />
            </div>

            <div className="field">
              <label>Total Booking Amount (Rs.)</label>
              <input type="text" value={`Rs. ${fmtNum(totalAmount)}`} disabled style={{background:'#f9f9f9',fontWeight:'bold',color:'var(--ink)'}} />
            </div>

            {/* Optional: Customer & Salesman (legacy fields kept intact) */}
            <div className="field">
              <label>Customer <span style={{fontSize:10,color:'var(--text-dim)'}}>(optional)</span></label>
              <select value={selectedCustomer} onChange={e=>{
                setSelectedCustomer(e.target.value);
                const cust=customers.find(c=>c.id===e.target.value);
                if(cust?.default_salesman_id) setSelectedSalesman(cust.default_salesman_id);
              }}>
                <option value="">-- None --</option>
                {customers.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>

            <div className="field">
              <label>Salesman <span style={{fontSize:10,color:'var(--text-dim)'}}>(optional)</span></label>
              <select value={selectedSalesman} onChange={e=>setSelectedSalesman(e.target.value)}>
                <option value="">-- None --</option>
                {salesmen.map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name}</option>)}
              </select>
            </div>
          </div>

          <div className="btn-row" style={{marginTop:16}}>
            <button className="btn primary" onClick={handleSaveBooking} disabled={loading}>
              {loading ? 'Saving...' : 'Save Booking'}
            </button>
            <button className="btn ghost" onClick={()=>setActiveTab('list')}>Cancel</button>
          </div>
        </div>
      )}

      {/* ── RECOVERY MODAL ─────────────────────────────────────────── */}
      {showRecovery && recoveryBooking && (
        <div style={{position:'fixed',top:0,left:0,right:0,bottom:0,background:'rgba(0,0,0,0.5)',display:'flex',alignItems:'center',justifyContent:'center',zIndex:100}}>
          <div className="panel" style={{width:440,maxWidth:'90%'}}>
            <div className="section-head">
              <h2>Add Recovery — {recoveryBooking.reference_number}</h2>
              <button className="btn ghost" style={{padding:'4px 8px'}} onClick={()=>{setShowRecovery(false);setMsg('');}}>✕</button>
            </div>

            <div style={{marginBottom:14,fontSize:13,lineHeight:1.7,background:'#FAFBF8',padding:10,borderRadius:6,border:'1px solid var(--line)'}}>
              <strong>Distributor:</strong> {recoveryBooking.distributors?.name || 'Not Assigned'}<br/>
              {recoveryBooking.distributors?.code && <><strong>Code:</strong> {recoveryBooking.distributors.code}<br/></>}
              <strong>Customer:</strong> {recoveryBooking.customers?.name || '—'}<br/>
              <strong>Total Booking:</strong> Rs. {fmtNum(recoveryBooking.total_amount)}<br/>
              <strong>Recovered:</strong> <span style={{color:'var(--green)'}}>Rs. {fmtNum(recoveryBooking.total_recovered)}</span><br/>
              <strong>Remaining:</strong> <span style={{color:'var(--amber)'}}>Rs. {fmtNum(recoveryBooking.remaining_balance)}</span>
            </div>

            <Msg msg={msg} />

            <div className="form-grid" style={{gridTemplateColumns:'1fr'}}>
              <div className="field">
                <label>Recovery Amount (Rs.) *</label>
                <input type="number" max={recoveryBooking.remaining_balance} value={recoveryAmount} onChange={e=>setRecoveryAmount(e.target.value)} />
              </div>
              <div className="field">
                <label>Payment Method</label>
                <select value={paymentMethod} onChange={e=>setPaymentMethod(e.target.value)}>
                  <option>Cash</option>
                  <option>Bank Transfer</option>
                  <option>Cheque</option>
                </select>
              </div>
            </div>

            <div className="btn-row" style={{marginTop:20}}>
              <button className="btn primary" onClick={handleSaveRecovery} disabled={loading}>
                {loading ? 'Processing...' : 'Save Recovery'}
              </button>
              <button className="btn ghost" onClick={()=>{setShowRecovery(false);setMsg('');}}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

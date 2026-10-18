import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabase';
import { fetchBookings, fetchProducts, fetchDistributors, submitBooking, addBookingRecovery, fetchRecoveries } from '../lib/db';
import { printBookingPad, shareBookingPadOnWhatsApp, formatPakistaniPhoneForWhatsApp } from '../lib/exportUtils';

const fmtNum  = (n) => Number(n || 0).toLocaleString('en-PK');
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

  // ── Tab: 'list' | 'create' | 'recoveries' ─────────────────────────────────
  const [activeTab, setActiveTab] = useState('list');

  // ── Data ──────────────────────────────────────────────────────────────────
  const [bookings,      setBookings]      = useState([]);
  const [distributors,  setDistributors]  = useState([]);
  const [products,      setProducts]      = useState([]);
  const [recoveries,    setRecoveries]    = useState([]);
  const [loading,       setLoading]       = useState(false);
  const [msg,           setMsg]           = useState('');

  // ── List filters ──────────────────────────────────────────────────────────
  const [filterDate,        setFilterDate]        = useState(todayISO());
  const [allDates,          setAllDates]          = useState(false);
  const [filterDistributor, setFilterDistributor] = useState('');
  const [filterSearch,      setFilterSearch]      = useState('');

  // ── Recoveries tab filters ────────────────────────────────────────────────
  const [recDistFilter,     setRecDistFilter]     = useState('');
  const [recSearch,         setRecSearch]         = useState('');

  // ── Create form ───────────────────────────────────────────────────────────
  const [selectedDistributor, setSelectedDistributor] = useState(null);
  const [distSearch,          setDistSearch]          = useState('');
  const [bookingDate,         setBookingDate]         = useState(todayISO());
  const [items,               setItems]               = useState([]); // [{packagingId, name, qty, price}]

  // Item picker (with editable unit price)
  const [selProduct, setSelProduct] = useState('');
  const [selPkg,     setSelPkg]     = useState('');
  const [selQty,     setSelQty]     = useState('');
  const [inputPrice, setInputPrice] = useState('');

  // ── Recovery modal ────────────────────────────────────────────────────────
  const [showRecovery,    setShowRecovery]    = useState(false);
  const [recoveryBooking, setRecoveryBooking] = useState(null);
  const [recoveryAmount,  setRecoveryAmount]  = useState('');
  const [paymentMethod,   setPaymentMethod]   = useState('Cash');

  // ── WhatsApp PDF sharing state ──────────────────────────────────────────
  const [sharingBookingId, setSharingBookingId] = useState(null);
  const [shareModal,       setShareModal]       = useState(null);

  // ── Load reference data on mount ──────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const [pData, dData] = await Promise.all([fetchProducts(), fetchDistributors()]);
        setProducts(pData     || []);
        setDistributors(dData || []);
      } catch (e) { console.error(e); }
    })();
  }, []);

  // ── Load bookings whenever filters change ─────────────────────────────────
  const loadBookings = useCallback(async () => {
    setLoading(true);
    try {
      const params = { distributorId: filterDistributor || undefined };
      if (!allDates) {
        params.dateFrom = dayStart(filterDate);
        params.dateTo   = dayEnd(filterDate);
      }
      const data = await fetchBookings(params);
      setBookings(data || []);
    } catch (e) {
      console.error(e);
      setMsg('err:Failed to load bookings.');
    }
    setLoading(false);
  }, [filterDate, allDates, filterDistributor]);

  useEffect(() => { loadBookings(); }, [loadBookings]);

  // ── Distributor search helpers ────────────────────────────────────────────
  const activeDistributors = distributors.filter(d => d.is_active);
  const distSearchLower    = distSearch.toLowerCase();
  const filteredDists      = distSearch
    ? activeDistributors.filter(d =>
        d.code?.toLowerCase().includes(distSearchLower) ||
        d.name?.toLowerCase().includes(distSearchLower) ||
        d.id_card?.toLowerCase().includes(distSearchLower) ||
        d.phone?.toLowerCase().includes(distSearchLower)
      )
    : activeDistributors;

  function handleSelectDist(d) { setSelectedDistributor(d); setDistSearch(''); }
  function handleClearDist()   { setSelectedDistributor(null); setDistSearch(''); }

  // ── Load recoveries whenever recDistFilter changes ───────────────────────
  const loadRecoveries = useCallback(async () => {
    try {
      const data = await fetchRecoveries({
        distributorId: recDistFilter || undefined
      });
      setRecoveries(data || []);
    } catch (e) {
      console.error('Failed to load recoveries:', e);
    }
  }, [recDistFilter]);

  useEffect(() => {
    loadRecoveries();
  }, [loadRecoveries]);

  // ── Item picker derived values ────────────────────────────────────────────
  const selProdObj = products.find(p => p.id === selProduct);
  const selPkgObj  = selProdObj?.product_packaging?.find(pk => pk.id === selPkg);
  const defaultCatalogPrice = selPkgObj?.product_prices?.[0]?.sales_price || 0;
  const currentUnitPrice = inputPrice !== '' ? Number(inputPrice) : defaultCatalogPrice;
  const selLineTotal = (currentUnitPrice || 0) * (Number(selQty) || 0);

  function handleAddItem() {
    if (!selPkg)                        { setMsg('err:Select a packaging variant.'); return; }
    if (!selQty || Number(selQty) <= 0) { setMsg('err:Enter a valid quantity (greater than 0).'); return; }
    const unitP = Number(inputPrice !== '' ? inputPrice : defaultCatalogPrice);
    if (isNaN(unitP) || unitP <= 0)     { setMsg('err:Enter a valid agreed unit price.'); return; }

    const label = `${selProdObj?.name || ''} — ${selPkgObj?.name || ''}`;
    setItems(prev => [...prev, { packagingId: selPkg, name: label, qty: Number(selQty), price: unitP }]);
    setSelProduct(''); setSelPkg(''); setSelQty(''); setInputPrice(''); setMsg('');
  }

  function handleRemoveItem(idx) {
    setItems(prev => prev.filter((_, i) => i !== idx));
  }

  const totalPackets = items.reduce((s, i) => s + i.qty,           0);
  const totalAmount  = items.reduce((s, i) => s + i.qty * i.price, 0);

  // ── Save booking ──────────────────────────────────────────────────────────
  async function handleSaveBooking() {
    if (!selectedDistributor)  { setMsg('err:Please select a distributor.'); return; }
    if (items.length === 0)    { setMsg('err:Add at least one item.'); return; }
    if (items.some(i => i.qty <= 0)) { setMsg('err:All items must have qty > 0.'); return; }
    if (items.some(i => i.price <= 0)) { setMsg('err:All items must have unit price > 0.'); return; }

    try {
      setLoading(true); setMsg('');
      await submitBooking({
        distributorId: selectedDistributor.id,
        bookingDate,
        items: items.map(i => ({ packagingId: i.packagingId, quantity: i.qty, price: i.price })),
        totalAmount
      });
      setMsg('ok:Booking saved successfully.');
      // Reset form
      setSelectedDistributor(null); setDistSearch('');
      setBookingDate(todayISO()); setItems([]);
      setSelProduct(''); setSelPkg(''); setSelQty(''); setInputPrice('');
      await loadBookings();
      setTimeout(() => { setActiveTab('list'); setMsg(''); }, 1500);
    } catch (e) {
      setMsg('err:' + e.message);
    } finally { setLoading(false); }
  }

  // ── Save recovery ─────────────────────────────────────────────────────────
  async function handleSaveRecovery() {
    if (!recoveryAmount || Number(recoveryAmount) <= 0) {
      setMsg('err:Amount must be greater than zero.'); return;
    }
    if (Number(recoveryAmount) > recoveryBooking.remaining_balance) {
      setMsg('err:Amount exceeds remaining balance.'); return;
    }
    try {
      setLoading(true); setMsg('');
      await addBookingRecovery({
        bookingId:     recoveryBooking.id,
        bookingRef:    recoveryBooking.reference_number,
        distributorId: recoveryBooking.distributor_id || null,
        amount:        recoveryAmount,
        paymentMethod
      });
      setMsg(`ok:Recovery of Rs. ${fmtNum(recoveryAmount)} recorded successfully. View in Recovery History tab.`);
      await loadBookings();
      await loadRecoveries();
      setTimeout(() => { setShowRecovery(false); }, 1500);
    } catch (e) {
      setMsg('err:' + e.message);
    } finally { setLoading(false); }
  }
  // Helper to ensure booking line items are loaded before printing or PDF export
async function ensureBookingItems(b) {
  const hasItems = (b.items && b.items.length > 0) || (b.sale_items && b.sale_items.length > 0);
  if (hasItems) return b;

  try {
    const { data, error } = await supabase
      .from('sale_items')
      .select('*, product_packaging(name, products(name))')
      .eq('sales_order_id', b.id);
    if (!error && data && data.length > 0) {
      return { ...b, sale_items: data };
    }
  } catch (err) {
    console.warn('Could not load sale_items on demand:', err);
  }
  return b;
}

  async function handlePrintBooking(b) {
    const resolvedBooking = await ensureBookingItems(b);
    printBookingPad(resolvedBooking);
  }

  // ── WhatsApp PDF share workflow ───────────────────────────────────────────
  async function handleWhatsApp(b) {
    // 1. Immediately open a blank tab synchronously within the user click gesture
    // This guarantees browsers (Edge, Chrome, Safari) never block the tab as an untrusted async popup.
    let targetWindow = null;
    if (typeof window !== 'undefined') {
      targetWindow = window.open('about:blank', '_blank');
    }

    try {
      // 2. Resolve booking line items and linked distributor
      const resolvedBooking = await ensureBookingItems(b);
      const dist = (Array.isArray(resolvedBooking.distributors) ? resolvedBooking.distributors[0] : resolvedBooking.distributors)
        || distributors.find(d => d.id === resolvedBooking.distributor_id)
        || null;

      if (!dist) {
        if (targetWindow && !targetWindow.closed) {
          try { targetWindow.close(); } catch (_) {}
        }
        const warn = 'Cannot share receipt: No distributor is linked to this booking.';
        setMsg('err:' + warn);
        if (typeof alert === 'function') alert(warn);
        return;
      }

      const formattedPhone = formatPakistaniPhoneForWhatsApp(dist.phone);
      if (!formattedPhone) {
        if (targetWindow && !targetWindow.closed) {
          try { targetWindow.close(); } catch (_) {}
        }
        const warn = `Cannot share receipt: Distributor ${dist.name || ''} has no valid registered phone number.`;
        setMsg('err:' + warn);
        if (typeof alert === 'function') alert(warn);
        return;
      }

      setSharingBookingId(resolvedBooking.id);
      setMsg('ok:Opening WhatsApp & generating signed PDF receipt for ' + resolvedBooking.reference_number + '...');

      await shareBookingPadOnWhatsApp({
        booking: resolvedBooking,
        distributor: dist,
        targetWindow,
        onProgress: (statusText) => setMsg('ok:' + statusText),
        onSuccess: (successMsg, details) => {
          setMsg('ok:' + successMsg);
          if (details && details.mode === 'download_and_chat') {
            setShareModal({
              booking: resolvedBooking,
              distName: dist.name,
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
      setMsg('err:Failed to generate or share booking PDF: ' + e.message);
    } finally {
      setSharingBookingId(null);
    }
  }

  // ── Client-side search filter ─────────────────────────────────────────────
  const displayBookings = filterSearch
    ? bookings.filter(b => {
        const s = filterSearch.toLowerCase();
        return (
          b.reference_number?.toLowerCase().includes(s) ||
          b.distributors?.name?.toLowerCase().includes(s) ||
          b.distributors?.code?.toLowerCase().includes(s)
        );
      })
    : bookings;

  // ── Recovery filters ──────────────────────────────────────────────────────
  const recQuery = (recSearch || '').toLowerCase();
  const displayRecoveries = recSearch
    ? recoveries.filter(r =>
        r.reference_number?.toLowerCase().includes(recQuery) ||
        r.distributors?.name?.toLowerCase().includes(recQuery) ||
        r.distributors?.code?.toLowerCase().includes(recQuery) ||
        r.payment_method?.toLowerCase().includes(recQuery) ||
        (r.notes || '').toLowerCase().includes(recQuery)
      )
    : recoveries;
  const totalRecAmt = displayRecoveries.reduce((sum, r) => sum + Number(r.amount || 0), 0);

  function distLabel(b) {
    if (!b.distributors) return <span style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>Not Assigned</span>;
    return (
      <span>
        {b.distributors.name}{' '}
        <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>({b.distributors.code})</span>
      </span>
    );
  }

  // ── RENDER ────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Tabs */}
      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="tabs">
          <div className={`tab${activeTab === 'list'       ? ' active' : ''}`} onClick={() => setActiveTab('list')}>Booking Ledger</div>
          <div className={`tab${activeTab === 'create'     ? ' active' : ''}`} onClick={() => setActiveTab('create')}>Create Booking</div>
          <div className={`tab${activeTab === 'recoveries' ? ' active' : ''}`} onClick={() => setActiveTab('recoveries')}>
            Recovery History ({recoveries.length})
          </div>
        </div>
      </div>

      <Msg msg={msg} />

      {/* ── BOOKING LIST ──────────────────────────────────────────────────── */}
      {activeTab === 'list' && (
        <div className="panel">
          {/* Filters row */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 16 }}>
            {!allDates && (
              <div className="field" style={{ flex: '1 1 160px', margin: 0 }}>
                <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.04em' }}>Date</label>
                <input type="date" value={filterDate} onChange={e => setFilterDate(e.target.value)} />
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, paddingBottom: 2 }}>
              <input
                id="allDatesChk"
                type="checkbox"
                checked={allDates}
                onChange={e => setAllDates(e.target.checked)}
                style={{ width: 'auto', margin: 0 }}
              />
              <label htmlFor="allDatesChk" style={{ fontSize: 13, cursor: 'pointer', margin: 0 }}>All Dates</label>
            </div>
            <div className="field" style={{ flex: '1 1 180px', margin: 0 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.04em' }}>Distributor</label>
              <select value={filterDistributor} onChange={e => setFilterDistributor(e.target.value)}>
                <option value="">All Distributors</option>
                {distributors.map(d => <option key={d.id} value={d.id}>{d.name} ({d.code})</option>)}
              </select>
            </div>
            <div className="field" style={{ flex: '2 1 220px', margin: 0 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.04em' }}>Search</label>
              <input placeholder="Booking #, distributor..." value={filterSearch} onChange={e => setFilterSearch(e.target.value)} />
            </div>
            <button className="btn" onClick={loadBookings} style={{ alignSelf: 'flex-end' }}>Refresh</button>
          </div>

          <div className="section-head">
            <h2>
              {filterDistributor
                ? (distributors.find(d => d.id === filterDistributor)?.name || 'Distributor') + ' — Bookings'
                : 'All Distributor Bookings'}
              {!allDates && filterDate && (
                <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--text-dim)', marginLeft: 10 }}>{fmtDate(filterDate)}</span>
              )}
            </h2>
            <span className="link" style={{ fontSize: 12 }}>{displayBookings.length} record{displayBookings.length !== 1 ? 's' : ''}</span>
          </div>

          {loading ? (
            <div style={{ padding: 20, color: 'var(--text-dim)' }}>Loading bookings...</div>
          ) : (
            <>
              <div style={{ padding: '8px 12px', background: '#F5F3ED', border: '1px solid var(--line)', borderRadius: 6, fontSize: 12, color: 'var(--text-dim)', marginBottom: 12 }}>
                ℹ️ <strong>Booking Ledger Notice:</strong> Bookings represent customer order reservations. Values below track <em>Advance Deposits</em> and do not post to trade debt receivables until fulfilled as an approved Delivery Bill (<code>SAL-</code>).
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Bill # / Ref</th>
                    <th>Date</th>
                    <th>Distributor</th>
                    <th style={{ textAlign: 'right' }}>Packets</th>
                    <th style={{ textAlign: 'right' }}>Booking Value</th>
                    <th style={{ textAlign: 'right' }}>Advance Paid</th>
                    <th style={{ textAlign: 'right' }}>Advance Remaining</th>
                    <th>Booking Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {displayBookings.length === 0 ? (
                    <tr><td colSpan={9} style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>No bookings found for selected filters.</td></tr>
                  ) : displayBookings.map(b => {
                    const pkts = (b.sale_items || []).reduce((sum, item) => sum + Number(item.quantity || 0), 0);
                    return (
                      <tr key={b.id}>
                        <td>
                          <div style={{ fontWeight: 700, color: 'var(--teal)', fontSize: 13 }}>Bill #{b.formattedBillNo || '01'}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'monospace' }}>{b.reference_number}</div>
                        </td>
                        <td>{fmtDate(b.sale_date)}</td>
                        <td>{distLabel(b)}</td>
                        <td style={{ textAlign: 'right' }}>{fmtNum(pkts)} pkts</td>
                        <td style={{ textAlign: 'right', fontWeight: 600 }}>Rs. {fmtNum(b.total_amount)}</td>
                        <td style={{ textAlign: 'right', color: 'var(--green)', fontWeight: 600 }}>Rs. {fmtNum(b.total_recovered)}</td>
                        <td style={{ textAlign: 'right', fontWeight: 700, color: b.remaining_balance > 0 ? 'var(--red)' : 'var(--green)' }}>
                          Rs. {fmtNum(b.remaining_balance)}
                        </td>
                        <td>
                          <span className={`badge ${b.remaining_balance <= 0 ? 'green' : b.total_recovered > 0 ? 'amber' : 'gray'}`}>
                            {b.remaining_balance <= 0 ? 'Advance Fully Paid' : b.total_recovered > 0 ? 'Partially Paid (Adv)' : 'Unpaid Advance'}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            {b.remaining_balance > 0 && (
                              <button
                                className="btn"
                                style={{ padding: '3px 8px', fontSize: 11.5 }}
                                onClick={() => {
                                  setRecoveryBooking(b);
                                  setRecoveryAmount(b.remaining_balance);
                                  setPaymentMethod('Cash');
                                  setShowRecovery(true);
                                  setMsg('');
                                }}
                              >
                                + Record Advance
                              </button>
                            )}
                          <button className="btn" style={{ padding: '3px 8px', fontSize: 11.5 }} onClick={() => handlePrintBooking(b)}>Print</button>
                          <button
                            className="btn"
                            style={{
                              padding: '3px 8px',
                              fontSize: 11.5,
                              background: '#25d366',
                              color: '#fff',
                              border: 'none',
                              opacity: sharingBookingId === b.id ? 0.7 : 1,
                              cursor: sharingBookingId === b.id ? 'wait' : 'pointer'
                            }}
                            disabled={sharingBookingId === b.id}
                            onClick={() => handleWhatsApp(b)}
                            title="Share complete signed PDF receipt on WhatsApp"
                          >
                            {sharingBookingId === b.id ? 'PDF...' : 'WA'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            </>
          )}
        </div>
      )}

      {/* ── CREATE BOOKING ────────────────────────────────────────────────── */}
      {activeTab === 'create' && (
        <div className="panel">
          <div className="section-head"><h2>Create New Booking</h2></div>

          {/* Booking Date */}
          <div className="form-grid" style={{ marginBottom: 16 }}>
            <div className="field">
              <label>Booking Date *</label>
              <input type="date" value={bookingDate} onChange={e => setBookingDate(e.target.value)} />
            </div>
          </div>

          {/* Distributor selector */}
          <div style={{ marginBottom: 20, padding: 14, background: '#FAFBF8', border: '1px solid var(--line)', borderRadius: 6 }}>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10 }}>Select Distributor *</div>
            {selectedDistributor ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: 10, background: 'rgba(14,124,134,.05)', border: '1px solid rgba(14,124,134,.25)', borderRadius: 6, padding: 12 }}>
                <div>
                  <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '.05em', color: 'var(--text-dim)' }}>Code</div>
                  <div style={{ fontWeight: 600 }}>{selectedDistributor.code}</div>
                </div>
                <div>
                  <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '.05em', color: 'var(--text-dim)' }}>Name</div>
                  <div style={{ fontWeight: 600 }}>{selectedDistributor.name}</div>
                </div>
                <div>
                  <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '.05em', color: 'var(--text-dim)' }}>ID Card</div>
                  <div>{selectedDistributor.id_card || '—'}</div>
                </div>
                <div>
                  <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '.05em', color: 'var(--text-dim)' }}>Phone</div>
                  <div>{selectedDistributor.phone || '—'}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                  <span className="link" style={{ color: 'var(--red)', fontSize: 12 }} onClick={handleClearDist}>Change Distributor</span>
                </div>
              </div>
            ) : (
              <>
                <input
                  placeholder="Search by Code, Name, ID Card or Phone..."
                  value={distSearch}
                  onChange={e => setDistSearch(e.target.value)}
                  style={{ width: '100%', boxSizing: 'border-box', marginBottom: 8 }}
                />
                {distSearch && (
                  <div style={{ border: '1px solid var(--line)', borderRadius: 4, maxHeight: 220, overflowY: 'auto', background: '#fff' }}>
                    {filteredDists.length === 0 ? (
                      <div style={{ padding: 10, fontSize: 12, color: 'var(--text-dim)' }}>No active distributors found.</div>
                    ) : filteredDists.map(d => (
                      <div
                        key={d.id}
                        onClick={() => handleSelectDist(d)}
                        style={{ padding: '9px 12px', cursor: 'pointer', borderBottom: '1px solid var(--line)', fontSize: 13 }}
                      >
                        <span style={{ fontWeight: 600 }}>{d.name}</span>{' '}
                        <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>({d.code}) | {d.phone} | {d.id_card}</span>
                      </div>
                    ))}
                  </div>
                )}
                {!distSearch && <p style={{ fontSize: 12, color: 'var(--text-dim)', margin: 0 }}>Type to search active distributors.</p>}
              </>
            )}
          </div>

          {/* Product picker */}
          <div style={{ marginBottom: 16, padding: 14, background: '#FAFBF8', border: '1px solid var(--line)', borderRadius: 6 }}>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10 }}>Add Item</div>
            <div className="form-grid">
              <div className="field">
                <label>Product</label>
                <select value={selProduct} onChange={e => { setSelProduct(e.target.value); setSelPkg(''); }}>
                  <option value="">-- Select Product --</option>
                  {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Packaging / Variant</label>
                <select value={selPkg} onChange={e => {
                  const pkgId = e.target.value;
                  setSelPkg(pkgId);
                  const pkgObj = selProdObj?.product_packaging?.find(pk => pk.id === pkgId);
                  const p = pkgObj?.product_prices?.[0]?.sales_price || 0;
                  setInputPrice(p ? String(p) : '');
                }} disabled={!selProduct}>
                  <option value="">-- Select Packaging --</option>
                  {selProdObj?.product_packaging?.map(pkg => (
                    <option key={pkg.id} value={pkg.id}>
                      {pkg.name} — Default Rs. {fmtNum(pkg.product_prices?.[0]?.sales_price || 0)} / unit
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Qty (packets) *</label>
                <input type="number" min="1" value={selQty} onChange={e => setSelQty(e.target.value)} placeholder="e.g. 50" />
              </div>
              <div className="field">
                <label>Agreed Price / pkt (Rs.) *</label>
                <input
                  type="number"
                  min="1"
                  step="any"
                  value={inputPrice}
                  onChange={e => setInputPrice(e.target.value)}
                  placeholder={selPkg ? "Agreed Unit Price" : "—"}
                  disabled={!selPkg}
                  style={{ fontWeight: 600, color: 'var(--ink)' }}
                />
              </div>
              <div className="field">
                <label>Line Total (Rs.)</label>
                <input type="text" value={selPkg && selQty && inputPrice ? `Rs. ${fmtNum(selLineTotal)}` : '—'} disabled style={{ background: '#f9f9f9', color: 'var(--ink)', fontWeight: 600 }} />
              </div>
            </div>
            <button className="btn primary" onClick={handleAddItem} style={{ marginTop: 6 }}>+ Add Item</button>
          </div>

          {/* Items table */}
          {items.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th style={{ textAlign: 'right' }}>Qty</th>
                    <th style={{ textAlign: 'right' }}>Agreed Unit Price</th>
                    <th style={{ textAlign: 'right' }}>Line Total</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.name}</td>
                      <td style={{ textAlign: 'right' }}>{fmtNum(item.qty)}</td>
                      <td style={{ textAlign: 'right' }}>Rs. {fmtNum(item.price)}</td>
                      <td style={{ textAlign: 'right' }}>Rs. {fmtNum(item.qty * item.price)}</td>
                      <td>
                        <span className="link" style={{ color: 'var(--red)', fontSize: 12, cursor: 'pointer' }} onClick={() => handleRemoveItem(idx)}>Remove</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr style={{ fontWeight: 600, borderTop: '2px solid var(--line)' }}>
                    <td>Total</td>
                    <td style={{ textAlign: 'right' }}>{fmtNum(totalPackets)} pkts</td>
                    <td></td>
                    <td style={{ textAlign: 'right', color: 'var(--teal)' }}>Rs. {fmtNum(totalAmount)}</td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}

          <div className="btn-row" style={{ marginTop: 16 }}>
            <button className="btn primary" onClick={handleSaveBooking} disabled={loading}>
              {loading ? 'Saving...' : 'Save Booking'}
            </button>
            <button className="btn ghost" onClick={() => setActiveTab('list')}>Cancel</button>
          </div>
        </div>
      )}

      {/* ── RECOVERY HISTORY TAB ─────────────────────────────────────────── */}
      {activeTab === 'recoveries' && (
        <div className="panel">
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 16 }}>
            <div className="field" style={{ flex: '1 1 200px', margin: 0 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.04em' }}>Distributor</label>
              <select value={recDistFilter} onChange={e => setRecDistFilter(e.target.value)}>
                <option value="">All Distributors</option>
                {distributors.map(d => <option key={d.id} value={d.id}>{d.name} ({d.code})</option>)}
              </select>
            </div>
            <div className="field" style={{ flex: '2 1 240px', margin: 0 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.04em' }}>Search</label>
              <input placeholder="Receipt #, booking ref, distributor..." value={recSearch} onChange={e => setRecSearch(e.target.value)} />
            </div>
            <button className="btn" onClick={loadRecoveries} style={{ alignSelf: 'flex-end' }}>Refresh</button>
          </div>

          <div className="section-head">
            <h2>
              {recDistFilter
                ? (distributors.find(d => d.id === recDistFilter)?.name || 'Distributor') + ' — Recoveries'
                : 'All Recorded Recoveries & Advance Payments'}
            </h2>
            <span className="link" style={{ fontSize: 12 }}>
              {displayRecoveries.length} record{displayRecoveries.length !== 1 ? 's' : ''} · Total: Rs. {fmtNum(totalRecAmt)}
            </span>
          </div>

          <table>
            <thead>
              <tr>
                <th>Recovery #</th>
                <th>Date</th>
                <th>Distributor</th>
                <th>Linked Booking / Ref</th>
                <th>Payment Mode</th>
                <th style={{ textAlign: 'right' }}>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {displayRecoveries.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>
                    No recoveries found for selected filters.
                  </td>
                </tr>
              ) : displayRecoveries.map(r => {
                const cleanRef = r.clean_recovery_ref || (r.reference_number && r.reference_number.includes('|') ? r.reference_number.split('|')[0] : r.reference_number);
                const displayLinkedRef = r.linked_order_ref;
                const rawLinked = r.raw_linked_id || (r.reference_number && r.reference_number.includes('|') ? r.reference_number.split('|')[1]?.trim() : null);

                return (
                  <tr key={r.id}>
                    <td style={{ fontWeight: 600 }}>{cleanRef}</td>
                    <td>{fmtDate(r.recovery_date)}</td>
                    <td>
                      {r.distributors ? (
                        <span>
                          <strong>{r.distributors.name}</strong>{' '}
                          <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>({r.distributors.code})</span>
                        </span>
                      ) : r.booking_distributor ? (
                        <span>
                          <strong>{r.booking_distributor.name}</strong>{' '}
                          <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>({r.booking_distributor.code})</span>
                          <span style={{ display: 'block', fontSize: 10, color: 'var(--teal)' }}>(via Linked Booking)</span>
                        </span>
                      ) : r.salesmen?.profiles?.full_name ? (
                        <span>
                          {r.salesmen.profiles.full_name}{' '}
                          <span className="badge gray" style={{ fontSize: 10, padding: '2px 5px' }}>Legacy Salesman</span>
                        </span>
                      ) : r.customers?.name ? (
                        <span>
                          {r.customers.name}{' '}
                          <span className="badge gray" style={{ fontSize: 10, padding: '2px 5px' }}>Customer</span>
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontStyle: 'italic', fontSize: 12 }}>Unassigned (Legacy)</span>
                      )}
                    </td>
                    <td>
                      {displayLinkedRef ? (
                        <span
                          title={rawLinked ? `Database Reference ID: ${rawLinked}` : ''}
                          style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--teal)' }}
                        >
                          {displayLinkedRef}
                        </span>
                      ) : rawLinked ? (
                        <span
                          title={`Database Reference ID: ${rawLinked}`}
                          style={{ color: 'var(--text-dim)', fontStyle: 'italic', fontSize: 11.5 }}
                        >
                          Ref: {rawLinked.slice(0, 8)}... (Unavailable)
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)' }}>Direct Recovery</span>
                      )}
                    </td>
                    <td>{r.payment_method || 'Cash'}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--green)' }}>
                      Rs. {fmtNum(r.amount)}
                    </td>
                    <td>
                      <span className={`badge ${['Approved','Posted'].includes(r.status) ? 'green' : 'amber'}`}>
                        {r.status || 'Approved'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── RECOVERY MODAL ────────────────────────────────────────────────── */}
      {showRecovery && recoveryBooking && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="panel" style={{ width: 440, maxWidth: '90%' }}>
            <div className="section-head">
              <h2>Record Booking Advance — {recoveryBooking.reference_number}</h2>
              <button className="btn ghost" style={{ padding: '4px 8px' }} onClick={() => { setShowRecovery(false); setMsg(''); }}>✕</button>
            </div>

            <div style={{ marginBottom: 14, fontSize: 13, lineHeight: 1.7, background: '#FAFBF8', padding: 10, borderRadius: 6, border: '1px solid var(--line)' }}>
              <strong>Distributor:</strong> {recoveryBooking.distributors?.name || 'Not Assigned'}<br />
              {recoveryBooking.distributors?.code && <><strong>Code:</strong> {recoveryBooking.distributors.code}<br /></>}
              <strong>Booking Value:</strong> Rs. {fmtNum(recoveryBooking.total_amount)}<br />
              <strong>Advance Paid:</strong> <span style={{ color: 'var(--green)' }}>Rs. {fmtNum(recoveryBooking.total_recovered)}</span><br />
              <strong>Advance Remaining:</strong> <span style={{ color: 'var(--amber)' }}>Rs. {fmtNum(recoveryBooking.remaining_balance)}</span>
            </div>

            <Msg msg={msg} />

            <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
              <div className="field">
                <label>Recovery Amount (Rs.) *</label>
                <input
                  type="number"
                  max={recoveryBooking.remaining_balance}
                  value={recoveryAmount}
                  onChange={e => setRecoveryAmount(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Payment Method</label>
                <select value={paymentMethod} onChange={e => setPaymentMethod(e.target.value)}>
                  <option>Cash</option>
                  <option>Bank Transfer</option>
                  <option>Cheque</option>
                </select>
              </div>
            </div>

            <div className="btn-row" style={{ marginTop: 20 }}>
              <button className="btn primary" onClick={handleSaveRecovery} disabled={loading}>
                {loading ? 'Processing...' : 'Save Recovery'}
              </button>
              <button className="btn ghost" onClick={() => { setShowRecovery(false); setMsg(''); }}>Cancel</button>
            </div>
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
                  <h3 style={{ margin: 0, fontSize: 16 }}>PDF Receipt Ready to Share</h3>
                  <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>{shareModal.distName} &bull; +{shareModal.phone}</div>
                </div>
              </div>
              <button className="btn ghost" style={{ padding: '4px 8px' }} onClick={() => setShareModal(null)}>✕</button>
            </div>

            <div style={{ background: '#FAFBF8', border: '1px solid var(--line)', borderRadius: 6, padding: 14, fontSize: 13, lineHeight: 1.6, marginBottom: 16 }}>
              <div style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 18 }}>📄</span>
                <div>
                  <strong>Downloaded Receipt:</strong>
                  <div style={{ color: 'var(--teal)', fontWeight: 600 }}>{shareModal.filename}</div>
                </div>
              </div>
              <div style={{ padding: '10px 12px', background: '#FFF8E7', border: '1px solid #F0D78C', borderRadius: 6, fontSize: 12.5, color: '#856404' }}>
                <strong>How to complete sending on WhatsApp:</strong>
                <ol style={{ margin: '6px 0 0 16px', padding: 0 }}>
                  <li>WhatsApp chat with <strong>{shareModal.distName}</strong> (+{shareModal.phone}) opens in your browser.</li>
                  <li>In WhatsApp, click the <strong>attach icon (📎) &rarr; Document</strong>.</li>
                  <li>Select the downloaded <strong>{shareModal.filename}</strong> from your Downloads folder.</li>
                  <li>Click <strong>Send</strong> to deliver the signed receipt.</li>
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

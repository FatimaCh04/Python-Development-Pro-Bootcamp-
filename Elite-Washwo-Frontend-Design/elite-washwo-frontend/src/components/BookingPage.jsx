import React, { useState, useEffect } from 'react';
import { fetchBookings, fetchCustomers, fetchSalesmen, fetchProducts, submitBooking, addBookingRecovery } from '../lib/db';

export default function BookingPage() {
  const [activeTab, setActiveTab] = useState('list');
  const [bookings, setBookings] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [salesmen, setSalesmen] = useState([]);
  const [products, setProducts] = useState([]);
  
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  // Form states
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [selectedSalesman, setSelectedSalesman] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedPackaging, setSelectedPackaging] = useState('');
  const [quantity, setQuantity] = useState('');

  // Recovery Modal states
  const [showRecovery, setShowRecovery] = useState(false);
  const [recoveryBooking, setRecoveryBooking] = useState(null);
  const [recoveryAmount, setRecoveryAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('Cash');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [bData, cData, sData, pData] = await Promise.all([
        fetchBookings(),
        fetchCustomers(),
        fetchSalesmen(),
        fetchProducts()
      ]);
      setBookings(bData || []);
      setCustomers(cData || []);
      setSalesmen(sData || []);
      setProducts(pData || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const selectedProdObj = products.find(p => p.id === selectedProduct);
  const selectedPkgObj = selectedProdObj?.product_packaging?.find(pkg => pkg.id === selectedPackaging);
  const unitPrice = selectedPkgObj?.product_prices?.[0]?.sales_price || 0;
  const totalAmount = unitPrice * (Number(quantity) || 0);

  const fmtNum = (n) => Number(n || 0).toLocaleString('en-PK');
  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' }) : '';

  async function handleSaveBooking() {
    if (!selectedCustomer || !selectedSalesman || !selectedPackaging || !quantity || Number(quantity) <= 0) {
      setMsg('err:Please fill all required fields correctly (quantity must be > 0).');
      return;
    }
    try {
      setLoading(true);
      setMsg('');
      await submitBooking({
        customerId: selectedCustomer,
        salesmanId: selectedSalesman,
        items: [{
          packagingId: selectedPackaging,
          quantity: Number(quantity),
          price: unitPrice
        }],
        totalAmount
      });
      setMsg('ok:Booking saved successfully.');
      setSelectedCustomer('');
      setSelectedSalesman('');
      setSelectedProduct('');
      setSelectedPackaging('');
      setQuantity('');
      
      await loadData();
      setTimeout(() => { setActiveTab('list'); setMsg(''); }, 1500);
    } catch (e) {
      setMsg('err:' + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveRecovery() {
    if (!recoveryAmount || Number(recoveryAmount) <= 0) {
      setMsg('err:Amount must be greater than zero.');
      return;
    }
    if (Number(recoveryAmount) > recoveryBooking.remaining_balance) {
      setMsg('err:Amount exceeds remaining balance.');
      return;
    }
    
    try {
      setLoading(true);
      setMsg('');
      await addBookingRecovery({
        bookingId: recoveryBooking.id,
        customerId: recoveryBooking.customer_id,
        salesmanId: recoveryBooking.salesman_id,
        amount: recoveryAmount,
        paymentMethod
      });
      setMsg('ok:Recovery added successfully.');
      
      await loadData();
      setTimeout(() => { setShowRecovery(false); setMsg(''); }, 1500);
    } catch (e) {
      setMsg('err:' + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="panel" style={{marginBottom:20}}>
        <div className="tabs">
          <div className={`tab${activeTab==='list'?' active':''}`} onClick={()=>setActiveTab('list')}>Booking List</div>
          <div className={`tab${activeTab==='create'?' active':''}`} onClick={()=>setActiveTab('create')}>Create Booking</div>
        </div>
      </div>

      {msg && (
        <div className={`perm-message ${msg.startsWith('ok:') ? 'ok' : 'err'}`} style={{marginBottom:16}}>
          {msg.substring(3)}
        </div>
      )}

      {activeTab === 'list' && (
        <div className="panel">
          <div className="section-head"><h2>Active Bookings</h2></div>
          {loading ? (
            <div style={{padding:20, color:'var(--text-dim)'}}>Loading bookings...</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Booking #</th>
                  <th>Date</th>
                  <th>Customer</th>
                  <th>Salesman</th>
                  <th>Total Amount</th>
                  <th>Recovered</th>
                  <th>Remaining</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {bookings.length === 0 ? (
                  <tr><td colSpan={9} style={{textAlign:'center', padding:20, color:'var(--text-dim)'}}>No bookings available</td></tr>
                ) : (
                  bookings.map(b => (
                    <tr key={b.id}>
                      <td>{b.reference_number}</td>
                      <td>{fmtDate(b.sale_date)}</td>
                      <td>{b.customers?.name}</td>
                      <td>{b.salesmen?.profiles?.full_name}</td>
                      <td className="num-cell">Rs. {fmtNum(b.total_amount)}</td>
                      <td className="num-cell" style={{color:'var(--green)'}}>Rs. {fmtNum(b.total_recovered)}</td>
                      <td className="num-cell" style={{color:'var(--amber)'}}>Rs. {fmtNum(b.remaining_balance)}</td>
                      <td><span className="badge amber">{b.status}</span></td>
                      <td>
                        {b.remaining_balance > 0 ? (
                          <button className="btn" onClick={() => {
                            setRecoveryBooking(b);
                            setRecoveryAmount(b.remaining_balance);
                            setPaymentMethod('Cash');
                            setShowRecovery(true);
                          }}>Add Recovery</button>
                        ) : (
                          <span className="badge green">Cleared</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'create' && (
        <div className="panel">
          <div className="section-head"><h2>Create New Booking</h2></div>
          <div className="form-grid">
            <div className="field">
              <label>Customer</label>
              <select value={selectedCustomer} onChange={e => {
                  setSelectedCustomer(e.target.value);
                  const cust = customers.find(c => c.id === e.target.value);
                  if (cust?.default_salesman_id) setSelectedSalesman(cust.default_salesman_id);
                }}>
                <option value="">-- Select Customer --</option>
                {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              {customers.length === 0 && <span style={{fontSize:11, color:'var(--amber)'}}>No customers available</span>}
            </div>
            
            <div className="field">
              <label>Salesman</label>
              <select value={selectedSalesman} onChange={e => setSelectedSalesman(e.target.value)}>
                <option value="">-- Select Salesman --</option>
                {salesmen.map(s => <option key={s.id} value={s.id}>{s.profiles?.full_name}</option>)}
              </select>
            </div>

            <div className="field">
              <label>Surf Product</label>
              <select value={selectedProduct} onChange={e => {
                setSelectedProduct(e.target.value);
                setSelectedPackaging('');
              }}>
                <option value="">-- Select Product --</option>
                {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              {products.length === 0 && <span style={{fontSize:11, color:'var(--amber)'}}>No products available</span>}
            </div>

            <div className="field">
              <label>Packaging Variant</label>
              <select value={selectedPackaging} onChange={e => setSelectedPackaging(e.target.value)} disabled={!selectedProduct}>
                <option value="">-- Select Packaging --</option>
                {selectedProdObj?.product_packaging?.map(pkg => (
                  <option key={pkg.id} value={pkg.id}>{pkg.name} — Rs. {pkg.product_prices?.[0]?.sales_price || 0}</option>
                ))}
              </select>
            </div>

            <div className="field">
              <label>Quantity</label>
              <input type="number" min="1" value={quantity} onChange={e => setQuantity(e.target.value)} placeholder="e.g. 50" />
            </div>

            <div className="field">
              <label>Total Amount (Rs.)</label>
              <input type="text" value={fmtNum(totalAmount)} disabled style={{background:'#f9f9f9', fontWeight:'bold', color:'var(--ink)'}} />
            </div>
          </div>
          
          <div className="btn-row" style={{marginTop:16}}>
            <button className="btn primary" onClick={handleSaveBooking} disabled={loading}>
              {loading ? 'Saving...' : 'Save Booking'}
            </button>
            <button className="btn ghost" onClick={() => setActiveTab('list')}>Cancel</button>
          </div>
        </div>
      )}

      {/* Recovery Modal / Inline Panel */}
      {showRecovery && recoveryBooking && (
        <div style={{position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:100}}>
          <div className="panel" style={{width: 400, maxWidth: '90%'}}>
            <div className="section-head">
              <h2>Add Recovery for {recoveryBooking.reference_number}</h2>
              <button className="btn ghost" style={{padding:'4px 8px'}} onClick={() => setShowRecovery(false)}>✕</button>
            </div>
            
            <div style={{marginBottom:16, fontSize:13}}>
              Customer: <strong>{recoveryBooking.customers?.name}</strong><br/>
              Remaining Balance: <strong style={{color:'var(--amber)'}}>Rs. {fmtNum(recoveryBooking.remaining_balance)}</strong>
            </div>

            <div className="form-grid" style={{gridTemplateColumns:'1fr'}}>
              <div className="field">
                <label>Recovery Amount (Rs.)</label>
                <input type="number" max={recoveryBooking.remaining_balance} value={recoveryAmount} onChange={e => setRecoveryAmount(e.target.value)} />
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

            <div className="btn-row" style={{marginTop:20}}>
              <button className="btn primary" onClick={handleSaveRecovery} disabled={loading}>
                {loading ? 'Processing...' : 'Save Recovery'}
              </button>
              <button className="btn ghost" onClick={() => setShowRecovery(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

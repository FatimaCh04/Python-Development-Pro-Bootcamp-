import re

content = open("src/main.jsx", "r", encoding="utf-8").read()

if "function SalesForm" not in content:
    # Add submitSale to db imports
    content = content.replace("fetchAuditLogs\n} from './lib/db';", "fetchAuditLogs,\n  submitSale\n} from './lib/db';")

    sales_form_code = """
function SalesForm({ onCancel, onSuccess }) {
  const { data: salesmen } = useAsync(fetchSalesmen);
  const { data: customers } = useAsync(fetchCustomers);
  const { data: packagings } = useAsync(fetchPackagings);
  
  const [salesmanId, setSalesmanId] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [items, setItems] = useState([]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const [selPkg, setSelPkg] = useState('');
  const [selQty, setSelQty] = useState('');

  const handleAddItem = () => {
    if (!selPkg || !selQty) return;
    const pkg = packagings?.find(p => p.id === selPkg);
    if (!pkg) return;
    const price = pkg.product_prices?.[0]?.sales_price || 0;
    setItems([...items, { packagingId: selPkg, name: `${pkg.products?.name} ${pkg.packagings?.name}`, price, quantity: parseInt(selQty, 10) }]);
    setSelPkg('');
    setSelQty('');
  };

  const totalAmount = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!salesmanId || !customerId || items.length === 0) {
      setMsg('err:Please select a salesman, customer, and add at least one product.');
      return;
    }
    setSaving(true); setMsg('');
    try {
      await submitSale({ salesmanId, customerId, items, totalAmount });
      setMsg('ok:Sale recorded successfully.');
      setTimeout(onSuccess, 1500);
    } catch(e) {
      setMsg('err:' + e.message);
      setSaving(false);
    }
  };

  return (
    <div style={{marginBottom:20,padding:16,background:'#FAFBF8',borderRadius:6,border:'1px solid var(--line)'}}>
      <div style={{display:'flex',justifyContent:'space-between',marginBottom:16}}>
        <h3 style={{margin:0,fontSize:14}}>Create Sale</h3>
        <span className="link" onClick={onCancel} style={{color:'var(--red)'}}>Cancel</span>
      </div>
      <Msg msg={msg} />
      <div className="form-grid" style={{marginBottom:16}}>
        <div className="field">
          <label>Salesman *</label>
          <select value={salesmanId} onChange={e=>setSalesmanId(e.target.value)}>
            <option value="">-- Select Salesman --</option>
            {(salesmen||[]).map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Customer *</label>
          <select value={customerId} onChange={e=>setCustomerId(e.target.value)}>
            <option value="">-- Select Customer --</option>
            {(customers||[]).map(c=><option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}
          </select>
        </div>
      </div>
      
      <div style={{border:'1px solid var(--line)',padding:12,borderRadius:4,background:'#fff',marginBottom:16}}>
        <h4 style={{margin:'0 0 12px',fontSize:13}}>Add Product</h4>
        <div className="form-grid">
          <div className="field">
            <label>Product & Packaging</label>
            <select value={selPkg} onChange={e=>setSelPkg(e.target.value)}>
              <option value="">-- Select Product --</option>
              {(packagings||[]).map(p=><option key={p.id} value={p.id}>{p.products?.name} {p.packagings?.name} (Rs. {p.product_prices?.[0]?.sales_price||0})</option>)}
            </select>
          </div>
          <div className="field">
            <label>Quantity</label>
            <div style={{display:'flex',gap:8}}>
              <input type="number" min="1" value={selQty} onChange={e=>setSelQty(e.target.value)} placeholder="Qty" style={{flex:1}}/>
              <button type="button" className="btn" onClick={handleAddItem}>+ Add</button>
            </div>
          </div>
        </div>
        
        {items.length > 0 && (
          <table style={{marginTop:16}}>
            <thead><tr><th>Product</th><th style={{textAlign:'center'}}>Qty</th><th style={{textAlign:'right'}}>Price</th><th style={{textAlign:'right'}}>Amount</th><th></th></tr></thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={i}>
                  <td>{item.name}</td>
                  <td style={{textAlign:'center'}}>{item.quantity}</td>
                  <td style={{textAlign:'right'}}>Rs. {item.price}</td>
                  <td style={{textAlign:'right'}}>Rs. {item.price * item.quantity}</td>
                  <td style={{textAlign:'center'}}><span className="link" style={{color:'var(--red)'}} onClick={() => setItems(items.filter((_,idx)=>idx!==i))}>Remove</span></td>
                </tr>
              ))}
              <tr><td colSpan="3" style={{textAlign:'right',fontWeight:'bold'}}>Total</td><td style={{textAlign:'right',fontWeight:'bold'}}>Rs. {totalAmount}</td><td></td></tr>
            </tbody>
          </table>
        )}
      </div>
      <button className="btn primary" onClick={handleSubmit} disabled={saving}>{saving?'Saving...':'Submit Sale'}</button>
    </div>
  );
}
"""

    # Insert SalesForm before CustomersPage
    content = content.replace("function CustomersPage({ searchTerm = '' }) {", sales_form_code + "\nfunction CustomersPage({ searchTerm = '' }) {")
    
    # Add a "Create Sale" button in CustomersPage
    old_btn_html = """<span className="link" onClick={()=>setShowAdd(s=>!s)}>{showAdd?'Cancel':'Add customer'}</span>"""
    new_btn_html = """<span className="link" onClick={()=>setShowSale(s=>!s)}>{showSale?'Cancel Sale':'Create Sale'}</span>\n              <span className="link" onClick={()=>setShowAdd(s=>!s)}>{showAdd?'Cancel':'Add customer'}</span>"""
    content = content.replace(old_btn_html, new_btn_html)

    # Add showSale state
    old_state = "const [showAdd, setShowAdd] = useState(false);"
    new_state = "const [showAdd, setShowAdd] = useState(false);\n  const [showSale, setShowSale] = useState(false);"
    content = content.replace(old_state, new_state)

    # Render SalesForm if showSale
    old_render = "{showAdd && ("
    new_render = "{showSale && <SalesForm onCancel={() => setShowSale(false)} onSuccess={() => {setShowSale(false); reload();}} />}\n\n          {showAdd && ("
    content = content.replace(old_render, new_render)
    
    open("src/main.jsx", "w", encoding="utf-8").write(content)
    print("SalesForm added")
else:
    print("SalesForm already exists")

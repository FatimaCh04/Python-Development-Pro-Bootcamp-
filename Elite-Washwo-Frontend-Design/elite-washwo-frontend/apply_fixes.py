import re

content = open("src/main.jsx", "r", encoding="utf-8").read()

# 1. Add addProduct to imports
old_import = "  fetchSalesmanSettlement, fetchAuditLogs,\n  submitSale\n} from './lib/db';"
new_import = "  fetchSalesmanSettlement, fetchAuditLogs,\n  submitSale, addProduct\n} from './lib/db';"
if "addProduct" not in content:
    content = content.replace(old_import, new_import)
    print("Import added")
else:
    print("Import already present")

# 2. Replace ProductPage function entirely
old_product_page_start = "function ProductPage({ searchTerm = '' }) {"
old_product_page_end = "function SettlementPage"

idx_start = content.find(old_product_page_start)
idx_end = content.find(old_product_page_end)

if idx_start == -1 or idx_end == -1:
    print("ERROR: Could not find ProductPage")
    exit(1)

new_product_page = '''function ProductPage({ searchTerm = '' }) {
  const { role } = useAuth();
  const { data: products, loading: pl, reload } = useAsync(fetchProducts);
  const { data: movement, loading: ml } = useAsync(fetchProductMovement);
  const mv = movement || {};

  const [localSearch, setLocalSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const query = (localSearch || searchTerm).trim().toLowerCase();

  // Add Product form state
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', code: '', packagingName: '', unitCost: '', salesPrice: '' });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const handleAddProduct = async (e) => {
    e.preventDefault();
    if (!form.name || !form.code || !form.packagingName || !form.unitCost || !form.salesPrice) {
      setMsg('err:All fields are required.');
      return;
    }
    setSaving(true); setMsg('');
    try {
      await addProduct(form);
      setMsg('ok:Product added successfully.');
      setForm({ name: '', code: '', packagingName: '', unitCost: '', salesPrice: '' });
      setShowAdd(false);
      reload();
    } catch (e) {
      setMsg('err:' + e.message);
    } finally {
      setSaving(false);
    }
  };

  const canManage = role === 'Super_Admin' || role === 'Manager';

  const allPriceRows = (products || []).flatMap(p =>
    (p.product_packaging || []).map(pkg => {
      const price = pkg.product_prices?.[0];
      return {
        id: pkg.id,
        productName: p.name,
        productCode: p.code,
        packagingName: pkg.name,
        unitCost: price?.unit_cost,
        salesPrice: price?.sales_price
      };
    })
  );

  const filteredPrices = allPriceRows.filter(r => {
    if (!query) return true;
    return (
      r.productName.toLowerCase().includes(query) ||
      (r.productCode || '').toLowerCase().includes(query) ||
      r.packagingName.toLowerCase().includes(query)
    );
  });

  const paginatedPrices = filteredPrices.slice((page - 1) * pageSize, page * pageSize);
  const isFiltered = !!localSearch;

  return (
    <>
      <div className="grid g4" style={{marginBottom:20}}>
        <div className="tile teal"><div className="bar"/><div className="label">Production</div><div className="num">{fmtNum(mv.production)}</div></div>
        <div className="tile green"><div className="bar"/><div className="label">Salesman returns</div><div className="num">{fmtNum(mv.salesman_returns)}</div></div>
        <div className="tile amber"><div className="bar"/><div className="label">Damaged / adjustments</div><div className="num">{fmtNum(mv.damaged)}</div></div>
        <div className="tile red"><div className="bar"/><div className="label">Closing stock (warehouse)</div><div className="num">{fmtNum(mv.closing)}</div></div>
      </div>

      <div className="panel">
        <div className="section-head"><h2>Stock movement report</h2></div>
        {ml ? <Spinner/> : (
          <table>
            <tbody>
              <tr><td>Production</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.production)}</td></tr>
              <tr><td>Salesman issues (dispatched)</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.salesman_issues)}</td></tr>
              <tr><td>Salesman returns</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.salesman_returns)}</td></tr>
              <tr><td>Customer returns</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.customer_returns)}</td></tr>
              <tr><td>Damaged</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.damaged)}</td></tr>
              <tr><td>Adjustments</td><td className="num-cell" style={{textAlign:'right'}}>{fmtNum(mv.adjustments)}</td></tr>
              <tr><td><strong>Closing stock</strong></td><td className="num-cell" style={{textAlign:'right'}}><strong>{fmtNum(mv.closing)}</strong></td></tr>
            </tbody>
          </table>
        )}
      </div>

      <div className="panel" style={{marginTop:20}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,marginBottom:14}}>
          <div className="section-head" style={{margin:0}}><h2>Products &amp; pricing</h2></div>
          <div style={{display:'flex',gap:8,alignItems:'center'}}>
            <input
              type="text"
              placeholder="Search product or packaging..."
              value={localSearch}
              onChange={e => { setLocalSearch(e.target.value); setPage(1); }}
              style={{padding:'5px 10px',fontSize:12,border:'1px solid var(--line)',borderRadius:6,background:'var(--panel)',color:'var(--text)',outline:'none',width:200}}
            />
            {isFiltered && (
              <span className="link" onClick={() => { setLocalSearch(''); setPage(1); }} style={{color:'var(--red)',fontSize:12}}>Reset</span>
            )}
            {canManage && (
              <span className="link" onClick={() => setShowAdd(s => !s)}>{showAdd ? 'Cancel' : '+ Add Product'}</span>
            )}
          </div>
        </div>

        {canManage && showAdd && (
          <form onSubmit={handleAddProduct} style={{marginBottom:20,padding:16,background:'#FAFBF8',borderRadius:6,border:'1px solid var(--line)'}}>
            <div style={{fontWeight:600,fontSize:13,marginBottom:12}}>Add New Product</div>
            <Msg msg={msg} />
            <div className="form-grid">
              <div className="field">
                <label>Product Name *</label>
                <input value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} placeholder="e.g. Elite Wash" />
              </div>
              <div className="field">
                <label>Product Code *</label>
                <input value={form.code} onChange={e=>setForm(f=>({...f,code:e.target.value}))} placeholder="e.g. ELW-001" />
              </div>
              <div className="field">
                <label>Packaging / Variant *</label>
                <input value={form.packagingName} onChange={e=>setForm(f=>({...f,packagingName:e.target.value}))} placeholder="e.g. 1kg, 500g, Sachet" />
              </div>
              <div className="field">
                <label>Cost Price (Rs.) *</label>
                <input type="number" min="0" step="0.01" value={form.unitCost} onChange={e=>setForm(f=>({...f,unitCost:e.target.value}))} placeholder="e.g. 90" />
              </div>
              <div className="field">
                <label>Sales Price (Rs.) *</label>
                <input type="number" min="0" step="0.01" value={form.salesPrice} onChange={e=>setForm(f=>({...f,salesPrice:e.target.value}))} placeholder="e.g. 120" />
              </div>
            </div>
            <button type="submit" className="btn primary" style={{marginTop:12}} disabled={saving}>{saving ? 'Saving...' : 'Save Product'}</button>
          </form>
        )}

        {pl ? <Spinner/> : (
          <div>
            <table>
              <thead><tr><th>Product</th><th>Packaging</th><th>Cost price</th><th>Sales price</th></tr></thead>
              <tbody>
                {paginatedPrices.length===0 ? <Empty msg={isFiltered || query ? "No products found matching search criteria." : "No products found. Add your first product using the button above."}/> :
                  paginatedPrices.map(r => (
                    <tr key={r.id}>
                      <td>{r.productName}</td>
                      <td>{r.packagingName}</td>
                      <td className="num-cell">Rs. {fmtNum(r.unitCost)}</td>
                      <td className="num-cell">Rs. {fmtNum(r.salesPrice)}</td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
            <Pagination page={page} pageSize={pageSize} total={filteredPrices.length} onPageChange={setPage} />
          </div>
        )}
      </div>
    </>
  );
}

'''

content = content[:idx_start] + new_product_page + content[idx_end:]
print("ProductPage replaced, len:", len(content))

# 3. Fix SalesForm - improve to use products first then packaging
old_sales_form_start = "function SalesForm({ onCancel, onSuccess }) {"
old_sales_form_end = "function CustomersPage({ searchTerm = '' }) {"

idx_sf_start = content.find(old_sales_form_start)
idx_sf_end = content.find(old_sales_form_end)

if idx_sf_start == -1 or idx_sf_end == -1:
    print("ERROR: Could not find SalesForm")
    exit(1)

new_sales_form = '''function SalesForm({ onCancel, onSuccess }) {
  const { data: salesmen } = useAsync(fetchSalesmen);
  const { data: customers } = useAsync(fetchCustomers);
  const { data: products } = useAsync(fetchProducts);

  const [salesmanId, setSalesmanId] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [items, setItems] = useState([]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  // Item picker state
  const [selProductId, setSelProductId] = useState('');
  const [selPkgId, setSelPkgId] = useState('');
  const [selQty, setSelQty] = useState('');

  const selectedProduct = (products || []).find(p => p.id === selProductId);
  const availablePackagings = selectedProduct?.product_packaging || [];
  const selectedPkg = availablePackagings.find(pk => pk.id === selPkgId);
  const autoPrice = selectedPkg?.product_prices?.[0]?.sales_price || 0;

  const handleAddItem = () => {
    if (!selProductId || !selPkgId || !selQty || Number(selQty) < 1) {
      setMsg('err:Select a product, packaging, and enter a valid quantity.');
      return;
    }
    const productName = selectedProduct?.name || '';
    const pkgName = selectedPkg?.name || '';
    const price = Number(autoPrice);
    const qty = parseInt(selQty, 10);
    setItems([...items, {
      packagingId: selPkgId,
      name: productName + (pkgName ? ' — ' + pkgName : ''),
      price,
      quantity: qty
    }]);
    setSelProductId('');
    setSelPkgId('');
    setSelQty('');
    setMsg('');
  };

  const removeItem = (idx) => setItems(items.filter((_, i) => i !== idx));

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
    } catch (e) {
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
            {(salesmen||[]).length === 0
              ? <option disabled>No salesmen available</option>
              : (salesmen||[]).map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)
            }
          </select>
        </div>
        <div className="field">
          <label>Customer *</label>
          <select value={customerId} onChange={e=>setCustomerId(e.target.value)}>
            <option value="">-- Select Customer --</option>
            {(customers||[]).length === 0
              ? <option disabled>No customers available</option>
              : (customers||[]).map(c=><option key={c.id} value={c.id}>{c.name} ({c.code})</option>)
            }
          </select>
        </div>
      </div>

      <div style={{border:'1px solid var(--line)',padding:12,borderRadius:4,background:'#fff',marginBottom:16}}>
        <div style={{fontWeight:600,fontSize:13,marginBottom:10}}>+ Add Product</div>
        <div className="form-grid">
          <div className="field">
            <label>Product</label>
            <select value={selProductId} onChange={e=>{setSelProductId(e.target.value);setSelPkgId('');}}>
              <option value="">-- Select Product --</option>
              {(products||[]).length === 0
                ? <option disabled>No products available — add products in Products & Pricing</option>
                : (products||[]).map(p=><option key={p.id} value={p.id}>{p.name} ({p.code})</option>)
              }
            </select>
          </div>
          <div className="field">
            <label>Packaging / Variant</label>
            <select value={selPkgId} onChange={e=>setSelPkgId(e.target.value)} disabled={!selProductId}>
              <option value="">-- Select Packaging --</option>
              {availablePackagings.map(pk=>(
                <option key={pk.id} value={pk.id}>
                  {pk.name} (Rs. {pk.product_prices?.[0]?.sales_price || 0})
                </option>
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

        {selPkgId && (
          <div style={{marginTop:8,fontSize:12,color:'var(--text-dim)'}}>
            Price: Rs. {fmtNum(autoPrice)} per unit
            {selQty > 0 && <> &nbsp;|&nbsp; Amount: Rs. {fmtNum(Number(autoPrice) * Number(selQty))}</>}
          </div>
        )}
      </div>

      {items.length > 0 && (
        <div className="panel" style={{marginBottom:16,padding:12}}>
          <div style={{fontWeight:600,fontSize:13,marginBottom:10}}>Items Added</div>
          <table>
            <thead><tr><th>Product</th><th style={{textAlign:'center'}}>Qty</th><th style={{textAlign:'right'}}>Price</th><th style={{textAlign:'right'}}>Amount</th><th></th></tr></thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={i}>
                  <td>{item.name}</td>
                  <td style={{textAlign:'center'}}>{item.quantity}</td>
                  <td style={{textAlign:'right'}}>Rs. {fmtNum(item.price)}</td>
                  <td style={{textAlign:'right'}}>Rs. {fmtNum(item.price * item.quantity)}</td>
                  <td style={{textAlign:'center'}}><span className="link" style={{color:'var(--red)',fontSize:12}} onClick={()=>removeItem(i)}>Remove</span></td>
                </tr>
              ))}
              <tr>
                <td colSpan="3" style={{textAlign:'right',fontWeight:'bold',paddingTop:8}}>Total</td>
                <td style={{textAlign:'right',fontWeight:'bold',paddingTop:8,color:'var(--teal)'}}>Rs. {fmtNum(totalAmount)}</td>
                <td></td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <div className="btn-row">
        <button className="btn primary" onClick={handleSubmit} disabled={saving || items.length === 0}>
          {saving ? 'Saving...' : 'Submit Sale'}
        </button>
        <button className="btn" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

'''

content = content[:idx_sf_start] + new_sales_form + content[idx_sf_end:]
print("SalesForm replaced, len:", len(content))

# 4. Fix Salesman select placeholders (all remaining mojibake)
import re
content = re.sub(r'<option value="">[^<]*Select salesman[^<]*</option>', '<option value="">-- Select salesman --</option>', content)
content = re.sub(r'<option value="">[^<]*None[^<]*</option>', '<option value="">-- None --</option>', content)
content = re.sub(r'<option value="">[^<]*Select[^<]*</option>', '<option value="">-- Select --</option>', content)

open("src/main.jsx", "w", encoding="utf-8").write(content)
print("All done, final len:", len(content))

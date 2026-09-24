import re

content = open("src/main.jsx", "r", encoding="utf-8").read()

# Add imports
old_import = "  submitSale, addProduct\n} from './lib/db';"
new_import = "  submitSale, addProduct, updateProduct, deleteProduct\n} from './lib/db';"
if "updateProduct" not in content and "updateProduct" in new_import:
    content = content.replace(old_import, new_import)

# Replace the ProductPage function to include edit/delete features
old_product_page_start = "function ProductPage({ searchTerm = '' }) {"
old_product_page_end = "function SettlementPage({ searchTerm = '' })"

idx_start = content.find(old_product_page_start)
idx_end = content.find(old_product_page_end)
if idx_end == -1:
    idx_end = content.find("function SettlementPage")

new_product_page = '''function ProductPage({ searchTerm = '' }) {
  const { role } = useAuth();
  const { data: products, loading: pl, reload } = useAsync(fetchProducts);
  const { data: movement, loading: ml } = useAsync(fetchProductMovement);
  const mv = movement || {};

  const [localSearch, setLocalSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const query = (localSearch || searchTerm).trim().toLowerCase();

  // Add/Edit Product form state
  const [showAdd, setShowAdd] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [form, setForm] = useState({ name: '', code: '', packagingName: '', unitCost: '', salesPrice: '', pkgId: null, productId: null, priceId: null });
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
      if (editMode) {
        await updateProduct(form);
        setMsg('ok:Product updated successfully.');
      } else {
        await addProduct(form);
        setMsg('ok:Product added successfully.');
      }
      setForm({ name: '', code: '', packagingName: '', unitCost: '', salesPrice: '', pkgId: null, productId: null, priceId: null });
      setShowAdd(false);
      setEditMode(false);
      reload();
    } catch (e) {
      setMsg('err:' + e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (r) => {
    setForm({
      name: r.productName,
      code: r.productCode || '',
      packagingName: r.packagingName,
      unitCost: r.unitCost || '',
      salesPrice: r.salesPrice || '',
      pkgId: r.id,
      productId: r.productId,
      priceId: r.priceId
    });
    setEditMode(true);
    setShowAdd(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (r) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    setMsg('');
    try {
      await deleteProduct(r.id, r.productId);
      setMsg('ok:Product deleted successfully.');
      reload();
    } catch (e) {
      setMsg('err:' + e.message);
    }
  };

  const canManage = role === 'Super_Admin' || role === 'Manager';

  const allPriceRows = (products || []).flatMap(p =>
    (p.product_packaging || []).map(pkg => {
      const price = pkg.product_prices?.[0];
      return {
        id: pkg.id,
        productId: p.id,
        priceId: price?.id,
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
              <button className={showAdd ? 'btn ghost' : 'btn primary'} onClick={() => { 
                if(showAdd) { setShowAdd(false); setEditMode(false); setForm({ name: '', code: '', packagingName: '', unitCost: '', salesPrice: '', pkgId: null, productId: null, priceId: null }); }
                else { setShowAdd(true); } 
              }}>
                {showAdd ? 'Cancel' : '+ Add Product'}
              </button>
            )}
          </div>
        </div>

        {canManage && showAdd && (
          <form onSubmit={handleAddProduct} style={{marginBottom:20,padding:16,background:'#FAFBF8',borderRadius:6,border:'1px solid var(--line)'}}>
            <div style={{fontWeight:600,fontSize:13,marginBottom:12}}>{editMode ? 'Edit Product' : 'Add New Product'}</div>
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
            <button type="submit" className="btn primary" style={{marginTop:12}} disabled={saving}>{saving ? 'Saving...' : (editMode ? 'Update Product' : 'Save Product')}</button>
          </form>
        )}
        {!showAdd && <Msg msg={msg} />}

        {pl ? <Spinner/> : (
          <div>
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Packaging</th>
                  <th>Cost price</th>
                  <th>Sales price</th>
                  {canManage && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {paginatedPrices.length===0 ? <Empty msg={isFiltered || query ? "No products found matching search criteria." : "No products found. Add your first product using the button above."}/> :
                  paginatedPrices.map(r => (
                    <tr key={r.id}>
                      <td>{r.productName}</td>
                      <td>{r.packagingName}</td>
                      <td className="num-cell">Rs. {fmtNum(r.unitCost)}</td>
                      <td className="num-cell">Rs. {fmtNum(r.salesPrice)}</td>
                      {canManage && (
                        <td>
                          <span className="link" onClick={() => handleEdit(r)}>Edit</span>
                          <span className="link" onClick={() => handleDelete(r)} style={{color:'var(--red)', marginLeft: 8}}>Delete</span>
                        </td>
                      )}
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

content = content[:idx_start] + new_product_page + "\n" + content[idx_end:]

open("src/main.jsx", "w", encoding="utf-8").write(content)
print("ProductPage updated with edit/delete UI")

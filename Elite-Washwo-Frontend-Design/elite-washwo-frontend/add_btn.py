content = open('src/main.jsx', 'r', encoding='utf-8').read()
old = """<div className="panel-flat"><h3 style={{fontSize:14,marginBottom:6}}>Salesman statement (PDF)</h3><p style={{fontSize:12.5,color:'var(--text-dim)',marginBottom:14}}>Stock, sales, recovery, returns, damages, expenses.</p><button className="btn">Generate</button></div>"""
new = old + """\n        <div className="panel-flat"><h3 style={{fontSize:14,marginBottom:6}}>Print Sale Receipt</h3><p style={{fontSize:12.5,color:'var(--text-dim)',marginBottom:14}}>Test customer sale receipt layout.</p><button className="btn" onClick={() => import('./lib/exportUtils').then(m => m.printSaleReceipt({ billNo: 'ELW-9912', date: new Date().toLocaleDateString('en-PK'), customerName: 'Al-Madina Mart (Test)', totalAmount: 18450, items: [{ description: 'Elite Wash 1kg', quantity: 10, unit_price: 150 }, { description: 'Elite Wash 500g', quantity: 25, unit_price: 80 }, { description: 'Elite Wash 250g', quantity: 50, unit_price: 45 }] }))}>Print Receipt</button></div>"""
content = content.replace(old, new)
open('src/main.jsx', 'w', encoding='utf-8', newline='\n').write(content)
print("Added button")

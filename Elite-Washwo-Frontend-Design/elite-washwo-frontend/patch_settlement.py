import re

with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Add import for approveSettlement if not there (it's already imported? Let's check imports)
# Actually, I'll just replace the SettlementPage definition entirely.

idx_start = c.find('function SettlementPage({ searchTerm')
idx_end = c.find('function AuditPage({ searchTerm', idx_start)

new_settlement_page = """function SettlementPage({ searchTerm = '' }) {
  const { data: salesmen } = useAsync(fetchSalesmen);
  const [selectedId, setSelectedId] = useState('');
  const { data: settlement, loading: sl } = useAsync(() => selectedId ? fetchSalesmanSettlement(selectedId) : Promise.resolve(null), [selectedId]);
  
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const query = (searchTerm || '').trim().toLowerCase();
  const filteredSalesmen = (salesmen || []).filter(s => !query || (s.profiles?.full_name || '').toLowerCase().includes(query) || (s.code || '').toLowerCase().includes(query));
  
  const selected = (salesmen||[]).find(s=>s.id===selectedId);
  const sv = settlement||{};

  const handleApprove = async () => {
    if (!selectedId) return;
    setSaving(true);
    setMsg('');
    try {
      // Dynamically import or assume approveSettlement is available
      // It might not be imported in main.jsx, so let's import it at the top or use window logic
      const { approveSettlement } = await import('./lib/db.js');
      await approveSettlement(selectedId);
      setMsg('ok:Settlement approved successfully.');
    } catch(err) {
      setMsg('error:' + err.message);
    }
    setSaving(false);
  };

  return (
    <div className="panel">
      <div className="section-head"><h2>Distributor Settlement</h2></div>
      <div className="field" style={{marginBottom:20,maxWidth:300}}>
        <label>Select Distributor</label>
        <select value={selectedId} onChange={e => { setSelectedId(e.target.value); setMsg(''); }}>
          <option value="">-- Select --</option>
          {filteredSalesmen.map(s=><option key={s.id} value={s.id}>{s.profiles?.full_name||s.code}</option>)}
        </select>
      </div>

      {msg && (
        <div style={{ padding: '8px 12px', marginBottom: 14, borderRadius: 6, fontSize: 12,
          background: msg.startsWith('error') ? 'var(--red-soft)' : 'var(--green-soft)',
          color: msg.startsWith('error') ? 'var(--red)' : 'var(--green)' }}>
          {msg.replace(/^(ok|error):/, '')}
        </div>
      )}

      {selectedId && (sl ? <Spinner/> : (
        <>
          <div className="grid g3" style={{marginBottom:18}}>
            <div className="panel-flat"><div style={{fontSize:12,color:'var(--text-dim)'}}>Net sales</div><div className="num" style={{fontSize:20}}>Rs. {fmtNum(sv.netSales)}</div></div>
            <div className="panel-flat"><div style={{fontSize:12,color:'var(--text-dim)'}}>Recovery</div><div className="num" style={{fontSize:20}}>Rs. {fmtNum(sv.recovery)}</div></div>
            <div className="panel-flat"><div style={{fontSize:12,color:'var(--text-dim)'}}>Outstanding</div><div className="num" style={{fontSize:20}}>Rs. {fmtNum(sv.outstanding)}</div></div>
          </div>
          <table>
            <tbody>
              <tr><td>Sales (net)</td><td className="num-cell" style={{textAlign:'right'}}>+ Rs. {fmtNum(sv.netSales)}</td></tr>
              <tr><td>Recovery received</td><td className="num-cell" style={{textAlign:'right'}}>− Rs. {fmtNum(sv.recovery)}</td></tr>
              <tr><td>Reimbursement payable (approved expenses)</td><td className="num-cell" style={{textAlign:'right'}}>+ Rs. {fmtNum(sv.reimbursable)}</td></tr>
              <tr><td><strong>Net settlement position</strong></td><td className="num-cell" style={{textAlign:'right'}}>
                <strong style={{color:sv.net>0?'var(--red)':'var(--green)'}}>
                  {sv.net>0?`Rs. ${fmtNum(sv.net)} payable by ${selected?.profiles?.full_name||'salesman'}`:`Rs. ${fmtNum(Math.abs(sv.net||0))} payable to ${selected?.profiles?.full_name||'salesman'}`}
                </strong>
              </td></tr>
            </tbody>
          </table>
          <div className="btn-row" style={{marginTop:16}}>
            <button className="btn primary" onClick={handleApprove} disabled={saving}>
              {saving ? 'Approving...' : 'Approve settlement'}
            </button>
          </div>
        </>
      ))}

      {!selectedId && <div style={{padding:24,textAlign:'center',color:'var(--text-dim)',fontSize:13}}>Select a distributor above to view their settlement.</div>}
    </div>
  );
}
"""

c = c[:idx_start] + new_settlement_page + c[idx_end:]

with open('src/main.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('SettlementPage patched')

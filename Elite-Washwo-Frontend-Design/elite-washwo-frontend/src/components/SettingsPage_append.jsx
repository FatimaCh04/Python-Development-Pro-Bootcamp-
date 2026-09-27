
// ── Profile Section ──────────────────────────────────────────────────────
function ProfileSection() {
  const { user, role } = useAuth();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    if (!user) return;
    supabase.from('profiles').select('full_name, role, is_active').eq('id', user.id).single()
      .then(({ data }) => setProfile(data));
  }, [user]);

  const SRow = ({ label, value }) => (
    <div style={{ display: 'flex', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--line)', gap: 12 }}>
      <div style={{ width: 160, fontSize: 12, color: 'var(--text-dim)', fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 13, color: 'var(--ink)' }}>{value || '—'}</div>
    </div>
  );

  return (
    <div style={{ maxWidth: 500 }}>
      <h2 style={{ fontSize: 17, marginBottom: 4 }}>Profile</h2>
      <p style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 20 }}>Your account information. Role is read-only.</p>
      <div style={{ background: '#FAFBF8', border: '1px solid var(--line)', borderRadius: 8, padding: '0 16px' }}>
        <SRow label="Full Name" value={profile?.full_name} />
        <SRow label="Email" value={user?.email} />
        <SRow label="Role" value={
          <span className={`badge ${role === 'Super_Admin' ? 'teal' : role === 'Manager' ? 'amber' : 'gray'}`}>{role}</span>
        } />
        <SRow label="Status" value={
          <span className={`badge ${profile?.is_active ? 'green' : 'gray'}`}>{profile?.is_active ? 'Active' : 'Disabled'}</span>
        } />
      </div>
      <p style={{ fontSize: 11.5, color: 'var(--text-dim)', marginTop: 14 }}>
        To change your name or role, contact the Super Admin.
      </p>
    </div>
  );
}

// ── Change Password Section ───────────────────────────────────────────────
function ChangePasswordSection() {
  const [newPw, setNewPw]     = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving]   = useState(false);
  const [msg, setMsg]         = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPw !== confirm) { setMsg('error:Passwords do not match.'); return; }
    if (newPw.length < 6)  { setMsg('error:Password must be at least 6 characters.'); return; }
    setSaving(true); setMsg('');
    const { error } = await supabase.auth.updateUser({ password: newPw });
    if (error) setMsg('error:' + error.message);
    else { setMsg('ok:Password changed successfully.'); setNewPw(''); setConfirm(''); }
    setSaving(false);
  };

  return (
    <div style={{ maxWidth: 420 }}>
      <h2 style={{ fontSize: 17, marginBottom: 4 }}>Change Password</h2>
      <p style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 20 }}>Update your login password via Supabase Auth.</p>
      {msg && (
        <div style={{ padding: '8px 12px', marginBottom: 14, borderRadius: 6, fontSize: 12,
          background: msg.startsWith('error') ? 'var(--red-soft)' : 'var(--green-soft)',
          color: msg.startsWith('error') ? 'var(--red)' : 'var(--green)' }}>
          {msg.replace(/^(ok|error):/, '')}
        </div>
      )}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="field">
          <label>New Password *</label>
          <input type="password" minLength={6} required value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="Min. 6 characters" />
        </div>
        <div className="field">
          <label>Confirm New Password *</label>
          <input type="password" minLength={6} required value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="Re-enter password" />
        </div>
        <button type="submit" className="btn primary" disabled={saving} style={{ alignSelf: 'flex-start' }}>
          {saving ? 'Saving...' : 'Update Password'}
        </button>
      </form>
    </div>
  );
}

// ── Distributor Settings Section ─────────────────────────────────────────
function DistributorSettingsSection({ role }) {
  const isReadOnly = role === 'Salesman';
  const [distributors, setDistributors] = useState([]);
  const [search, setSearch]             = useState('');
  const [selected, setSelected]         = useState(null);
  const [form, setForm]                 = useState({});
  const [saving, setSaving]             = useState(false);
  const [msg, setMsg]                   = useState('');

  useEffect(() => {
    fetchDistributors().then(data => setDistributors(data || [])).catch(console.error);
  }, []);

  const filtered = distributors.filter(d => {
    const q = search.toLowerCase();
    return !q || (d.name || '').toLowerCase().includes(q) || (d.code || '').toLowerCase().includes(q)
      || (d.phone || '').includes(q) || (d.id_card || '').includes(q);
  });

  const selectDist = (d) => {
    setSelected(d);
    setForm({ code: d.code || '', name: d.name || '', id_card: d.id_card || '', phone: d.phone || '', commission: d.commission ?? '' });
    setMsg('');
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!selected) return;
    setSaving(true); setMsg('');
    try {
      await updateDistributor(selected.id, {
        code: form.code, name: form.name, id_card: form.id_card,
        phone: form.phone, commission: Number(form.commission)
      });
      setMsg('ok:Distributor updated successfully.');
      const fresh = await fetchDistributors();
      setDistributors(fresh || []);
      const updated = (fresh || []).find(d => d.id === selected.id);
      if (updated) setSelected(updated);
    } catch (err) {
      setMsg('error:' + err.message);
    }
    setSaving(false);
  };

  return (
    <div>
      <h2 style={{ fontSize: 17, marginBottom: 4 }}>Distributor Settings</h2>
      <p style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 20 }}>
        {isReadOnly ? 'View distributor details.' : 'Edit distributor details and individual commission.'}
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 20, alignItems: 'start' }}>
        {/* List */}
        <div style={{ border: '1px solid var(--line)', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--line)', background: '#F5F3ED' }}>
            <input
              type="text" placeholder="Search by name, code, phone..."
              value={search} onChange={e => setSearch(e.target.value)}
              style={{ width: '100%', border: 'none', background: 'transparent', fontSize: 12, outline: 'none', color: 'var(--ink)' }}
            />
          </div>
          <div style={{ maxHeight: 420, overflowY: 'auto' }}>
            {filtered.length === 0
              ? <div style={{ padding: 16, fontSize: 12, color: 'var(--text-dim)', textAlign: 'center' }}>No distributors found.</div>
              : filtered.map(d => (
                <div key={d.id} onClick={() => selectDist(d)}
                  style={{ padding: '10px 14px', cursor: 'pointer', borderBottom: '1px solid var(--line)',
                    background: selected?.id === d.id ? 'rgba(14,124,134,.08)' : 'var(--panel)',
                    borderLeft: selected?.id === d.id ? '3px solid var(--teal)' : '3px solid transparent' }}>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{d.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{d.code} · Commission: PKR {d.commission ?? 0}</div>
                </div>
              ))
            }
          </div>
        </div>

        {/* Editor */}
        <div>
          {!selected ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-dim)', fontSize: 13, border: '1px dashed var(--line)', borderRadius: 8 }}>
              Select a distributor from the list to view or edit.
            </div>
          ) : (
            <div style={{ border: '1px solid var(--line)', borderRadius: 8, padding: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 14 }}>{selected.name}</div>
              {msg && (
                <div style={{ padding: '8px 12px', marginBottom: 14, borderRadius: 6, fontSize: 12,
                  background: msg.startsWith('error') ? 'var(--red-soft)' : 'var(--green-soft)',
                  color: msg.startsWith('error') ? 'var(--red)' : 'var(--green)' }}>
                  {msg.replace(/^(ok|error):/, '')}
                </div>
              )}
              <form onSubmit={handleSave}>
                <div className="form-grid">
                  <div className="field"><label>Code</label>
                    <input value={form.code} onChange={e => setForm({...form, code: e.target.value})} disabled={isReadOnly} required /></div>
                  <div className="field"><label>Name</label>
                    <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} disabled={isReadOnly} required /></div>
                  <div className="field"><label>ID Card</label>
                    <input value={form.id_card} onChange={e => setForm({...form, id_card: e.target.value})} disabled={isReadOnly} /></div>
                  <div className="field"><label>Phone No.</label>
                    <input value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} disabled={isReadOnly} /></div>
                  <div className="field"><label>Commission (PKR per packet)</label>
                    <input type="number" min="0" step="0.01" value={form.commission} onChange={e => setForm({...form, commission: e.target.value})} disabled={isReadOnly} /></div>
                </div>
                {!isReadOnly && (
                  <button type="submit" className="btn primary" style={{ marginTop: 12 }} disabled={saving}>
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                )}
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Financial Settings Section (Super_Admin only) ─────────────────────────
function FinancialSettingsSection() {
  const [gs, setGs]       = useState(null);
  const [advBal, setAdv]  = useState('');
  const [welfBal, setWelf]= useState('');
  const [saving, setSaving]= useState(false);
  const [msg, setMsg]     = useState('');

  useEffect(() => {
    fetchGlobalSettings()
      .then(data => {
        setGs(data);
        setAdv(data?.advertisement_opening_balance ?? '');
        setWelf(data?.welfare_opening_balance ?? '');
      })
      .catch(console.error);
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true); setMsg('');
    try {
      await updateGlobalSettings({
        advertisement_opening_balance: Number(advBal),
        welfare_opening_balance: Number(welfBal)
      });
      setMsg('ok:Opening balances updated successfully.');
      setGs({ ...gs, advertisement_opening_balance: Number(advBal), welfare_opening_balance: Number(welfBal) });
    } catch (err) {
      setMsg('error:' + err.message);
    }
    setSaving(false);
  };

  if (!gs) return <div style={{ padding: 20, color: 'var(--text-dim)', fontSize: 13 }}>Loading...</div>;

  return (
    <div style={{ maxWidth: 480 }}>
      <h2 style={{ fontSize: 17, marginBottom: 4 }}>Financial Account Settings</h2>
      <p style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 6 }}>
        Set the <strong>opening balances</strong> for Advertisement and Welfare accounts.
      </p>
      <p style={{ fontSize: 11.5, color: 'var(--text-dim)', marginBottom: 20, padding: '8px 12px', background: '#FFF8E7', border: '1px solid #F0D78C', borderRadius: 6 }}>
        ⚠ These are opening/manual adjustment values only. The live balance is always calculated from transactions (sales allocations − expenses). Editing these values does not create or delete any transactions.
      </p>
      {msg && (
        <div style={{ padding: '8px 12px', marginBottom: 14, borderRadius: 6, fontSize: 12,
          background: msg.startsWith('error') ? 'var(--red-soft)' : 'var(--green-soft)',
          color: msg.startsWith('error') ? 'var(--red)' : 'var(--green)' }}>
          {msg.replace(/^(ok|error):/, '')}
        </div>
      )}
      <form onSubmit={handleSave}>
        <div style={{ background: '#FAFBF8', border: '1px solid var(--line)', borderRadius: 8, padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="field">
            <label>Advertisement Opening Balance (PKR)</label>
            <input type="number" min="0" step="0.01" value={advBal} onChange={e => setAdv(e.target.value)} required />
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
              Current live balance = Opening + (Sales pkts × 20) − Company/Office expenses
            </div>
          </div>
          <div className="field">
            <label>Welfare Opening Balance (PKR)</label>
            <input type="number" min="0" step="0.01" value={welfBal} onChange={e => setWelf(e.target.value)} required />
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
              Current live balance = Opening + (Sales pkts × 10) − Others expenses
            </div>
          </div>
        </div>
        <button type="submit" className="btn primary" style={{ marginTop: 14 }} disabled={saving}>
          {saving ? 'Saving...' : 'Save Opening Balances'}
        </button>
      </form>
    </div>
  );
}

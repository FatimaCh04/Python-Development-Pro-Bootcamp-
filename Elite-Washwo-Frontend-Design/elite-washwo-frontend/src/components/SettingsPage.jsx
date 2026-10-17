import React, { useState, useEffect } from 'react';
import PermissionManager from './PermissionManager';
import { supabase } from '../lib/supabase';
import { invokeCreateUser, fetchDistributors, updateDistributor, fetchGlobalSettings, updateGlobalSettings } from '../lib/db';
import { useAuth } from '../context/AuthContext';

export default function SettingsPage({ searchTerm = '' }) {
  const [activeTab, setActiveTab] = useState('staff');
  const { role } = useAuth();
  const isSuperAdmin = role === 'Super_Admin';

  const TABS = [
    { key: 'staff',        label: 'Staff Management' },
    { key: 'perms',        label: 'Permissions' },
    { key: 'profile',      label: 'Profile' },
    { key: 'password',     label: 'Change Password' },
    { key: 'distributors', label: 'Distributor Settings' },
    ...(isSuperAdmin ? [{ key: 'financial', label: 'Financial Accounts' }] : []),
  ];

  return (
    <div className="panel" style={{padding: 0}}>
      <div className="tabs" style={{padding: '16px 24px 0', flexWrap: 'wrap', gap: 2}}>
        {TABS.map(t => (
          <div key={t.key} className={`tab${activeTab===t.key?' active':''}`} onClick={()=>setActiveTab(t.key)}>{t.label}</div>
        ))}
      </div>
      <div style={{padding: 24}}>
        {activeTab === 'staff'        && <StaffManager globalSearch={searchTerm} />}
        {activeTab === 'perms'        && <PermissionManager />}
        {activeTab === 'profile'      && <ProfileSection />}
        {activeTab === 'password'     && <ChangePasswordSection />}
        {activeTab === 'distributors' && <DistributorSettingsSection role={role} />}
        {activeTab === 'financial'    && isSuperAdmin && <FinancialSettingsSection />}
      </div>
    </div>
  );
}

function StaffManager({ globalSearch = '' }) {
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [msg, setMsg] = useState('');
  
  // Search & Filter state
  const [localSearch, setLocalSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const [form, setForm] = useState({
    email: '', password: '', full_name: '', role: 'Manager', code: '', route: ''
  });
  const [saving, setSaving] = useState(false);

  const fetchStaff = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select(`
          id, full_name, role, is_active,
          salesmen(code, route)
        `)
        .order('created_at', { ascending: false });
      if (error) throw error;
      setStaff(data || []);
    } catch(e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchStaff(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    setSaving(true); setMsg('');
    try {
      await invokeCreateUser(form);
      setMsg('ok:User created successfully.');
      setForm({ email: '', password: '', full_name: '', role: 'Manager', code: '', route: '' });
      setShowAdd(false);
      fetchStaff();
    } catch(e) {
      setMsg('error:' + e.message);
    }
    setSaving(false);
  };

  const toggleStatus = async (id, currentStatus) => {
    try {
      await supabase.from('profiles').update({ is_active: !currentStatus }).eq('id', id);
      fetchStaff();
    } catch(e) { console.error(e); }
  };

  const query = (localSearch || globalSearch).trim().toLowerCase();

  const filteredStaff = staff.filter(s => {
    if (roleFilter !== 'All' && s.role !== roleFilter) return false;
    if (!query) return true;
    return (
      (s.full_name || '').toLowerCase().includes(query) ||
      (s.role || '').toLowerCase().includes(query) ||
      (s.salesmen?.[0]?.code || '').toLowerCase().includes(query) ||
      (s.salesmen?.[0]?.route || '').toLowerCase().includes(query)
    );
  });

  const paginatedStaff = filteredStaff.slice((page - 1) * pageSize, page * pageSize);
  const isFiltered = localSearch || roleFilter !== 'All';
  const resetFilters = () => { setLocalSearch(''); setRoleFilter('All'); setPage(1); };

  return (
    <div>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,marginBottom: 16}}>
        <div>
          <h2 style={{fontSize:18, margin:0}}>Staff Directory</h2>
          <p style={{fontSize:12.5,color:'var(--text-dim)',margin:0}}>Manage Manager accounts.</p>
        </div>
        <button className="btn primary" onClick={()=>setShowAdd(!showAdd)}>{showAdd ? 'Cancel' : 'Add Staff'}</button>
      </div>

      <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap',marginBottom:16}}>
        <input 
          type="text" 
          placeholder="Filter staff by name, code, route..." 
          value={localSearch} 
          onChange={e => { setLocalSearch(e.target.value); setPage(1); }} 
          style={{padding:'5px 10px',fontSize:12,border:'1px solid var(--line)',borderRadius:6,background:'var(--panel)',color:'var(--text)',outline:'none',width:220}}
        />
        <div className="chip-list" style={{gap:4}}>
          {['All', 'Manager'].map(r => (
            <div key={r} className={`chip${roleFilter===r?' active':''}`} onClick={() => { setRoleFilter(r); setPage(1); }} style={{padding:'4px 10px',fontSize:11}}>
              {r}
            </div>
          ))}
        </div>
        {isFiltered && (
          <span className="link" onClick={resetFilters} style={{color:'var(--red)',fontSize:12}}>Reset</span>
        )}
      </div>

      {msg && (
        <div style={{padding:'8px 12px', marginBottom:12, borderRadius:4, fontSize:12, 
          background: msg.startsWith('error')?'var(--red-soft)':'var(--green-soft)', 
          color: msg.startsWith('error')?'var(--red)':'var(--green)'}}>
          {msg.replace(/^(ok|error):/, '')}
        </div>
      )}

      {showAdd && (
        <form onSubmit={handleAdd} style={{marginBottom:20,padding:16,background:'#FAFBF8',borderRadius:6,border:'1px solid var(--line)'}}>
          <div className="form-grid">
            <div className="field">
              <label>Full Name *</label>
              <input required placeholder="e.g. Ali Raza" value={form.full_name} onChange={e=>setForm({...form, full_name: e.target.value})} />
            </div>
            <div className="field">
              <label>Email *</label>
              <input required type="email" placeholder="ali@washwo.com" value={form.email} onChange={e=>setForm({...form, email: e.target.value})} />
            </div>
            <div className="field">
              <label>Password *</label>
              <input required type="password" minLength="6" value={form.password} onChange={e=>setForm({...form, password: e.target.value})} />
            </div>
            <div className="field">
              <label>Role *</label>
              <select value={form.role} onChange={e=>setForm({...form, role: e.target.value})}>
                <option value="Manager">Manager</option>
              </select>
            </div>
          </div>
          <button type="submit" className="btn primary" style={{marginTop:12}} disabled={saving}>
            {saving ? 'Creating...' : 'Create Account'}
          </button>
        </form>
      )}

      {loading ? <div style={{textAlign:'center',padding:20,color:'var(--text-dim)'}}>Loading...</div> : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Role</th>
              <th>Assignment</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedStaff.length === 0 ? (
              <tr>
                <td colSpan="5" style={{textAlign:'center',color:'var(--text-dim)',padding:24,fontSize:12}}>
                  {isFiltered || query ? 'No staff found matching search criteria.' : 'No staff accounts yet.'}
                </td>
              </tr>
            ) : (
              paginatedStaff.map(s => (
                <tr key={s.id}>
                  <td><div style={{fontWeight:600}}>{s.full_name}</div></td>
                  <td><span className={`badge ${s.role==='Manager'?'teal':'amber'}`}>{s.role}</span></td>
                  <td>
                    {s.salesmen?.[0] ? (
                      <div style={{fontSize:11.5}}>
                        Code: {s.salesmen[0].code}<br/>
                        <span style={{color:'var(--text-dim)'}}>Route: {s.salesmen[0].route || 'N/A'}</span>
                      </div>
                    ) : '—'}
                  </td>
                  <td>
                    <span className={`badge ${s.is_active?'green':'gray'}`}>{s.is_active ? 'Active' : 'Disabled'}</span>
                  </td>
                  <td>
                    {s.role !== 'Super_Admin' && (
                      <span className="link" onClick={()=>toggleStatus(s.id, s.is_active)} style={{color: s.is_active ? 'var(--red)' : 'var(--green)'}}>
                        {s.is_active ? 'Disable' : 'Enable'}
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

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

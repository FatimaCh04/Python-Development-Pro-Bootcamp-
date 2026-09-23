import React, { useState, useEffect } from 'react';
import PermissionManager from './PermissionManager';
import { supabase } from '../lib/supabase';
import { invokeCreateUser } from '../lib/db';

export default function SettingsPage({ searchTerm = '' }) {
  const [activeTab, setActiveTab] = useState('staff');
  
  return (
    <div className="panel" style={{padding: 0}}>
      <div className="tabs" style={{padding: '16px 24px 0'}}>
        <div className={`tab${activeTab==='staff'?' active':''}`} onClick={()=>setActiveTab('staff')}>Staff Management</div>
        <div className={`tab${activeTab==='perms'?' active':''}`} onClick={()=>setActiveTab('perms')}>Permissions</div>
      </div>
      <div style={{padding: 24}}>
        {activeTab === 'staff' && <StaffManager globalSearch={searchTerm} />}
        {activeTab === 'perms' && <PermissionManager />}
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
    email: '', password: '', full_name: '', role: 'Salesman', code: '', route: ''
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
      if (form.role === 'Salesman' && !form.code) throw new Error('Salesman code is required.');
      await invokeCreateUser(form);
      setMsg('ok:User created successfully.');
      setForm({ email: '', password: '', full_name: '', role: 'Salesman', code: '', route: '' });
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
          <p style={{fontSize:12.5,color:'var(--text-dim)',margin:0}}>Manage Manager and Salesman accounts.</p>
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
          {['All', 'Manager', 'Salesman'].map(r => (
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
                <option value="Salesman">Salesman</option>
              </select>
            </div>
            {form.role === 'Salesman' && (
              <>
                <div className="field">
                  <label>Salesman Code *</label>
                  <input required placeholder="e.g. S-01" value={form.code} onChange={e=>setForm({...form, code: e.target.value})} />
                </div>
                <div className="field">
                  <label>Route</label>
                  <input placeholder="e.g. North Zone" value={form.route} onChange={e=>setForm({...form, route: e.target.value})} />
                </div>
              </>
            )}
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

import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

export default function PermissionManager() {
  const [managers, setManagers] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [selectedManager, setSelectedManager] = useState(null);
  const [managerPerms, setManagerPerms] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => { fetchInitialData(); }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [managersRes, permsRes] = await Promise.all([
        supabase.from('profiles').select('id, full_name, is_active').eq('role', 'Manager'),
        supabase.from('permissions').select('*').order('module')
      ]);
      if (managersRes.error) throw managersRes.error;
      if (permsRes.error) throw permsRes.error;
      setManagers(managersRes.data || []);
      setPermissions(permsRes.data || []);
    } catch (err) {
      console.error(err);
      setMessage('error:Error loading data.');
    } finally {
      setLoading(false);
    }
  };

  const selectManager = async (managerId) => {
    setSelectedManager(managerId);
    setMessage('');
    try {
      const { data, error } = await supabase
        .from('user_permissions').select('permission_id').eq('user_id', managerId);
      if (error) throw error;
      setManagerPerms(new Set(data.map(p => p.permission_id)));
    } catch (err) { console.error(err); }
  };

  const togglePermission = (permId) => {
    const next = new Set(managerPerms);
    if (next.has(permId)) next.delete(permId); else next.add(permId);
    setManagerPerms(next);
  };

  const savePermissions = async () => {
    if (!selectedManager) return;
    setSaving(true); setMessage('');
    try {
      await supabase.from('user_permissions').delete().eq('user_id', selectedManager);
      if (managerPerms.size > 0) {
        const inserts = Array.from(managerPerms).map(perm => ({ user_id: selectedManager, permission_id: perm }));
        const { error } = await supabase.from('user_permissions').insert(inserts);
        if (error) throw error;
      }
      setMessage('ok:Permissions saved successfully.');
    } catch (err) {
      console.error(err);
      setMessage('error:Error saving permissions.');
    } finally { setSaving(false); }
  };

  if (loading) return <div style={{padding:40,textAlign:'center',color:'var(--text-dim)',fontSize:13}}>Loading permissions…</div>;

  const groupedPerms = permissions.reduce((acc, p) => {
    acc[p.module] = acc[p.module] || [];
    acc[p.module].push(p);
    return acc;
  }, {});

  const msgIsError = message.startsWith('error:');
  const msgText = message.replace(/^(ok|error):/, '');

  return (
    <div>
      <div style={{padding:'20px 0 16px',borderBottom:'1px solid var(--line)',marginBottom:0}}>
        <div style={{fontSize:11,textTransform:'uppercase',letterSpacing:'.06em',color:'var(--text-dim)',fontWeight:600,marginBottom:4}}>System Administration</div>
        <h2 style={{fontSize:18,fontFamily:"'Space Grotesk',sans-serif",margin:'0 0 4px'}}>Role &amp; Permission Management</h2>
        <p style={{fontSize:12.5,color:'var(--text-dim)',margin:0}}>Assign explicit permissions to Managers. Super Admins have implicit full access.</p>
      </div>

      <div className="perm-layout">
        <div className="perm-manager-list">
          <div className="nav-group-label">Managers</div>
          {managers.length === 0 && <div style={{fontSize:12,color:'var(--text-dim)',padding:'8px 10px'}}>No managers found.</div>}
          {managers.map(m => (
            <div
              key={m.id}
              className={`nav-item${selectedManager === m.id ? ' active' : ''}`}
              onClick={() => selectManager(m.id)}
              style={{cursor:'pointer'}}
            >
              <div className="avatar" style={{width:28,height:28,fontSize:11,flexShrink:0}}>{m.full_name.substring(0,2).toUpperCase()}</div>
              <div>
                <div style={{fontSize:12.5,fontWeight:600}}>{m.full_name}</div>
                <div style={{fontSize:11,color:'var(--text-dim)',marginTop:1}}>{m.is_active ? 'Active' : 'Inactive'}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="perm-grid">
          {!selectedManager ? (
            <div className="perm-select-prompt">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" opacity="0.3"><circle cx="12" cy="8" r="4"/><path d="M6 20v-1a6 6 0 0112 0v1"/><path d="M19 11l2 2-5 5-3-3"/></svg>
              <p style={{fontSize:13,margin:0}}>Select a manager to configure permissions</p>
            </div>
          ) : (
            <>
              <div className="perm-grid-header">
                <div>
                  <strong style={{fontSize:14}}>Assigned Permissions</strong>
                  <span style={{fontSize:12,color:'var(--text-dim)',marginLeft:8}}>{managerPerms.size} granted</span>
                </div>
                <button className="btn primary" onClick={savePermissions} disabled={saving}>
                  {saving ? 'Saving…' : 'Save Changes'}
                </button>
              </div>

              {message && (
                <div className={`perm-message ${msgIsError ? 'err' : 'ok'}`}>{msgText}</div>
              )}

              <div className="perm-modules">
                {Object.entries(groupedPerms).map(([module, perms]) => (
                  <div key={module} className="perm-module">
                    <div className="perm-module-title">{module}</div>
                    <div className="perm-checks">
                      {perms.map(p => (
                        <label key={p.id} className={`perm-check${managerPerms.has(p.id) ? ' on' : ''}`}>
                          <input type="checkbox" checked={managerPerms.has(p.id)} onChange={() => togglePermission(p.id)} />
                          <div>
                            <b>{p.id}</b>
                            <span>{p.description}</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

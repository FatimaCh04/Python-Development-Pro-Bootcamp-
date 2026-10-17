import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchDistributors, addDistributor, updateDistributor } from '../lib/db';

export function Msg({ msg }) {
  if (!msg) return null;
  const isErr = msg.startsWith('err:');
  return (
    <div style={{
      padding: '8px 12px',
      marginBottom: 12,
      borderRadius: 4,
      fontSize: 12,
      background: isErr ? 'var(--red-soft)' : 'var(--green-soft)',
      color: isErr ? 'var(--red)' : 'var(--green)',
    }}>
      {msg.replace(/^(ok|err):/, '')}
    </div>
  );
}

export default function DistributorsPage({ searchTerm = '' }) {
  const { role } = useAuth();
  const [distributors, setDistributors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [msg, setMsg] = useState('');

  // Search & Filter state
  const [localSearch, setLocalSearch] = useState('');

  const [form, setForm] = useState({
    id: '', code: '', name: '', id_card: '', phone: '', commission: '0', is_active: true,
  });
  const [saving, setSaving] = useState(false);

  const canEdit = role === 'Super_Admin' || role === 'Manager';
  const canToggle = role === 'Super_Admin';

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchDistributors();
      setDistributors(data);
    } catch (e) {
      console.error(e);
      setMsg('err:Failed to load distributors.');
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const handleOpenAdd = () => {
    setMsg('');
    setForm({ id: '', code: '', name: '', id_card: '', phone: '', commission: '0', is_active: true });
    setShowAdd(true);
  };

  const handleOpenEdit = (d) => {
    setMsg('');
    setForm({
      id: d.id,
      code: d.code,
      name: d.name,
      id_card: d.id_card || '',
      phone: d.phone || '',
      commission: d.commission,
      is_active: d.is_active,
    });
    setShowAdd(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setMsg('');

    if (!form.code.trim() || !form.name.trim() || !form.id_card.trim() || !form.phone.trim()) {
      setMsg('err:Please fill all required fields.');
      return;
    }
    if (Number(form.commission) < 0) {
      setMsg('err:Commission cannot be negative.');
      return;
    }

    // Duplicate code check
    const isEdit = !!form.id;
    const originalCode = isEdit
      ? distributors.find((d) => d.id === form.id)?.code
      : null;
    const codeChanged = !isEdit || form.code.trim().toLowerCase() !== originalCode?.toLowerCase();

    if (codeChanged) {
      const duplicate = distributors.some(
        (d) => d.code.toLowerCase() === form.code.trim().toLowerCase() && d.id !== form.id
      );
      if (duplicate) {
        setMsg('err:Distributor code already exists.');
        return;
      }
    }

    setSaving(true);
    try {
      if (isEdit) {
        await updateDistributor(form.id, form);
        setMsg('ok:Distributor updated successfully.');
      } else {
        await addDistributor(form);
        setMsg('ok:Distributor added successfully.');
      }
      setShowAdd(false);
      loadData();
    } catch (err) {
      setMsg('err:' + (err.message || 'Database error occurred.'));
    }
    setSaving(false);
  };

  const handleToggleActive = async (d) => {
    setMsg('');
    try {
      await updateDistributor(d.id, { ...d, is_active: !d.is_active });
      setMsg(d.is_active ? 'ok:Distributor deactivated.' : 'ok:Distributor activated.');
      loadData();
    } catch (err) {
      setMsg('err:' + (err.message || 'Failed to update distributor status.'));
    }
  };

  const search = localSearch || searchTerm;
  const filtered = distributors.filter((d) => {
    if (!search) return true;
    const l = search.toLowerCase();
    return (
      d.code?.toLowerCase().includes(l) ||
      d.name?.toLowerCase().includes(l) ||
      d.phone?.toLowerCase().includes(l) ||
      d.id_card?.toLowerCase().includes(l)
    );
  });

  return (
    <div className="panel">
      {/* Info bar */}
      <div style={{
        padding: '8px 14px',
        marginBottom: 14,
        borderRadius: 5,
        fontSize: 12,
        background: 'var(--teal-soft, #e6f6f6)',
        color: 'var(--teal)',
        border: '1px solid var(--line)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
          <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        Distributor records are permanent. Use <strong style={{ marginLeft: 3, marginRight: 3 }}>Deactivate</strong> to remove from active workflows without losing historical data.
      </div>

      <div className="section-head">
        <div>
          <h2>Distributors</h2>
          <div style={{ fontSize: 12.5, color: 'var(--text-dim)', marginTop: 2 }}>
            Manage distributor information and commission details.
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <div className="search-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="7" /><path d="M21 21l-4-4" />
            </svg>
            <input
              type="text"
              placeholder="Search code, name, CNIC, phone..."
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              style={{ border: 'none', outline: 'none', background: 'transparent', fontSize: 13 }}
            />
          </div>
          {canEdit && !showAdd && (
            <button className="btn primary" onClick={handleOpenAdd}>+ Add Distributor</button>
          )}
        </div>
      </div>

      <Msg msg={msg} />

      {showAdd && (
        <form
          onSubmit={handleSave}
          style={{ marginBottom: 20, padding: 16, background: '#FAFBF8', borderRadius: 6, border: '1px solid var(--line)' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <h3 style={{ margin: 0, fontSize: 14 }}>{form.id ? 'Edit Distributor' : 'Add Distributor'}</h3>
            <span
              className="link"
              onClick={() => { setShowAdd(false); setMsg(''); }}
              style={{ color: 'var(--red)' }}
            >
              Cancel
            </span>
          </div>
          <div className="form-grid">
            <div className="field">
              <label>Code *</label>
              <input
                required
                placeholder="DST-01"
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Name *</label>
              <input
                required
                placeholder="Business Name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div className="field">
              <label>CNIC / ID Card *</label>
              <input
                required
                placeholder="35201-..."
                value={form.id_card}
                onChange={(e) => setForm({ ...form, id_card: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Phone *</label>
              <input
                required
                placeholder="0300..."
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Commission (PKR/packet) *</label>
              <input
                required
                type="number"
                min="0"
                step="0.01"
                value={form.commission}
                onChange={(e) => setForm({ ...form, commission: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Status</label>
              <select
                value={form.is_active ? 'true' : 'false'}
                onChange={(e) => setForm({ ...form, is_active: e.target.value === 'true' })}
              >
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>
          </div>
          <div className="btn-row" style={{ marginTop: 16 }}>
            <button className="btn primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
          </div>
        </form>
      )}

      {/* Count */}
      {!loading && (
        <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 8 }}>
          {filtered.length} of {distributors.length} distributor{distributors.length !== 1 ? 's' : ''}
        </div>
      )}

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)' }}>Loading distributors...</div>
      ) : filtered.length === 0 ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)' }}>
          No distributors found.
          {canEdit && (
            <span className="link" onClick={handleOpenAdd} style={{ marginLeft: 8 }}>Add Distributor</span>
          )}
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>CNIC / ID Card</th>
              <th>Phone</th>
              <th style={{ textAlign: 'right' }}>Commission (PKR/pkt)</th>
              <th>Status</th>
              {(canEdit || canToggle) && <th style={{ textAlign: 'right' }}>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {filtered.map((d) => (
              <tr key={d.id}>
                <td>{d.code}</td>
                <td>{d.name}</td>
                <td>{d.id_card}</td>
                <td>{d.phone}</td>
                <td className="num-cell" style={{ textAlign: 'right' }}>
                  Rs.&nbsp;{Number(d.commission).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td>
                  {d.is_active
                    ? <span className="badge green">Active</span>
                    : <span className="badge gray">Inactive</span>}
                </td>
                {(canEdit || canToggle) && (
                  <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {canEdit && (
                      <span className="link" onClick={() => handleOpenEdit(d)}>Edit</span>
                    )}
                    {canToggle && (
                      <span
                        className="link"
                        onClick={() => handleToggleActive(d)}
                        style={{ marginLeft: canEdit ? 12 : 0, color: d.is_active ? 'var(--red)' : 'var(--green)' }}
                      >
                        {d.is_active ? 'Deactivate' : 'Activate'}
                      </span>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

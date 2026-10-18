import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchPersons,
  createPerson,
  updatePerson,
  fetchPersonLedger,
  submitPersonEntry,
  approvePersonEntry,
  cancelPersonEntry
} from '../lib/db';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { formatPakistaniPhoneForWhatsApp, printPersonPaymentVoucher, sharePersonPaymentVoucherOnWhatsApp } from '../lib/exportUtils';

const CATEGORIES = [
  'All',
  'Labourer',
  'Helper',
  'Transporter',
  'Manufacturer',
  'Employee',
  'Service Provider',
  'Other'
];

const ENTRY_TYPES = [
  { key: 'Work_Earning',      label: 'Work Earning (Credit to Worker)' },
  { key: 'Payment',           label: 'Payment Disbursed (Debit / Settles Payable)' },
  { key: 'Advance',           label: 'Advance Given (Debit to Worker)' },
  { key: 'Commission_Earned', label: 'Commission Earned (Credit)' },
  { key: 'Commission_Paid',   label: 'Commission Paid Out (Debit)' },
  { key: 'Adjustment',        label: 'Balance Adjustment' }
];

const fmtNum = (n) => Number(n || 0).toLocaleString('en-PK');
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';
const todayISO = () => new Date().toISOString().split('T')[0];

function Msg({ msg }) {
  if (!msg) return null;
  const isErr = msg.startsWith('err:');
  return (
    <div style={{
      padding: '8px 14px', marginBottom: 14, borderRadius: 6, fontSize: 12.5,
      background: isErr ? 'var(--red-soft)' : 'var(--green-soft)',
      color: isErr ? 'var(--red)' : 'var(--green)',
      border: `1px solid ${isErr ? 'rgba(217,83,79,0.3)' : 'rgba(46,125,50,0.3)'}`
    }}>
      {msg.replace(/^(ok|err):/, '')}
    </div>
  );
}

export default function PaymentPage({ searchTerm = '' }) {
  const { role, hasPermission } = useAuth();
  const canManage = role === 'Super_Admin' || hasPermission('payments.create');
  const canApprove = role === 'Super_Admin' || hasPermission('payments.approve');

  const [activeTab, setActiveTab] = useState('directory');

  // Persons list state
  const [persons, setPersons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [catFilter, setCatFilter] = useState('All');
  const [personSearch, setPersonSearch] = useState('');

  // Add / Edit Person Modal
  const [showPersonModal, setShowPersonModal] = useState(false);
  const [editingPerson, setEditingPerson] = useState(null);
  const [personForm, setPersonForm] = useState({
    code: '',
    name: '',
    category: 'Labourer',
    phone: '',
    cnic: '',
    address: '',
    default_rate: '',
    commission_rate: '',
    opening_payable_balance: '',
    opening_receivable_balance: '',
    notes: '',
    is_active: true
  });
  const [modalMsg, setModalMsg] = useState('');
  const [modalSaving, setModalSaving] = useState(false);

  // Work & Payment Entry State
  const [selectedPersonId, setSelectedPersonId] = useState('');
  const [entryType, setEntryType] = useState('Work_Earning');
  const [entryDesc, setEntryDesc] = useState('');
  const [entryQty, setEntryQty] = useState('');
  const [entryRate, setEntryRate] = useState('');
  const [entryAmt, setEntryAmt] = useState('');
  const [entryMethod, setEntryMethod] = useState('Cash');
  const [entryAccount, setEntryAccount] = useState('');
  const [entryTid, setEntryTid] = useState('');
  const [createExpense, setCreateExpense] = useState(true);
  const [entryMsg, setEntryMsg] = useState('');
  const [entrySaving, setEntrySaving] = useState(false);

  // Ledger View State
  const [ledgerPersonId, setLedgerPersonId] = useState('');
  const [ledgerDateFrom, setLedgerDateFrom] = useState('');
  const [ledgerDateTo, setLedgerDateTo] = useState('');
  const [ledgerData, setLedgerData] = useState({ entries: [], summary: {}, person: null });
  const [ledgerLoading, setLedgerLoading] = useState(false);
  const [sharingEntryId, setSharingEntryId] = useState(null);
  const [shareModal, setShareModal] = useState(null);

  // Load Persons
  const loadPersons = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPersons({ category: catFilter !== 'All' ? catFilter : undefined });
      setPersons(data || []);
      if (data && data.length > 0 && !selectedPersonId) {
        setSelectedPersonId(data[0].id);
      }
      if (data && data.length > 0 && !ledgerPersonId) {
        setLedgerPersonId(data[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [catFilter, selectedPersonId, ledgerPersonId]);

  useEffect(() => {
    loadPersons();
  }, [loadPersons]);

  // Load Ledger
  const loadLedger = useCallback(async () => {
    if (!ledgerPersonId) return;
    setLedgerLoading(true);
    try {
      const res = await fetchPersonLedger(
        ledgerPersonId,
        ledgerDateFrom ? ledgerDateFrom + 'T00:00:00.000Z' : undefined,
        ledgerDateTo ? ledgerDateTo + 'T23:59:59.999Z' : undefined
      );
      setLedgerData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLedgerLoading(false);
    }
  }, [ledgerPersonId, ledgerDateFrom, ledgerDateTo]);

  useEffect(() => {
    if (activeTab === 'ledger' && ledgerPersonId) {
      loadLedger();
    }
  }, [activeTab, ledgerPersonId, loadLedger]);

  // Open Add Person Modal
  const handleOpenAdd = () => {
    setEditingPerson(null);
    setPersonForm({
      code: `PER-${String(persons.length + 1).padStart(3, '0')}`,
      name: '',
      category: 'Labourer',
      phone: '',
      cnic: '',
      address: '',
      default_rate: '',
      commission_rate: '',
      opening_payable_balance: '',
      opening_receivable_balance: '',
      notes: '',
      is_active: true
    });
    setModalMsg('');
    setShowPersonModal(true);
  };

  // Open Edit Person Modal
  const handleOpenEdit = (p) => {
    setEditingPerson(p);
    setPersonForm({
      code: p.code,
      name: p.name,
      category: p.category,
      phone: p.phone || '',
      cnic: p.cnic || '',
      address: p.address || '',
      default_rate: p.default_rate || '',
      commission_rate: p.commission_rate || '',
      opening_payable_balance: p.opening_payable_balance || '',
      opening_receivable_balance: p.opening_receivable_balance || '',
      notes: p.notes || '',
      is_active: p.is_active !== false
    });
    setModalMsg('');
    setShowPersonModal(true);
  };

  // Save Person (Create or Update)
  const handleSavePerson = async (e) => {
    e.preventDefault();
    if (!personForm.code || !personForm.name) {
      setModalMsg('err:Code and Name are required.');
      return;
    }
    setModalSaving(true);
    setModalMsg('');
    try {
      if (editingPerson) {
        await updatePerson(editingPerson.id, personForm);
        setModalMsg('ok:Person profile updated.');
      } else {
        await createPerson(personForm);
        setModalMsg('ok:Person registered successfully.');
      }
      setTimeout(() => {
        setShowPersonModal(false);
        loadPersons();
      }, 500);
    } catch (err) {
      setModalMsg('err:' + err.message);
    } finally {
      setModalSaving(false);
    }
  };

  // Handle Work/Payment Entry Calculation
  useEffect(() => {
    if (entryType === 'Work_Earning') {
      const q = Number(entryQty || 0);
      const r = Number(entryRate || 0);
      if (q > 0 && r > 0) {
        setEntryAmt(String(q * r));
      }
    }
  }, [entryQty, entryRate, entryType]);

  // Submit Work or Payment Entry
  const handleSubmitEntry = async (e) => {
    e.preventDefault();
    if (!selectedPersonId) { setEntryMsg('err:Please select a worker/person.'); return; }
    if (!entryDesc) { setEntryMsg('err:Please provide a description of the work or payment.'); return; }
    const amt = Number(entryAmt);
    if (!amt || amt <= 0) { setEntryMsg('err:Please enter a valid amount.'); return; }

    setEntrySaving(true);
    setEntryMsg('');
    try {
      await submitPersonEntry({
        personId: selectedPersonId,
        entryType,
        description: entryDesc,
        quantity: entryQty,
        rate: entryRate,
        amount: amt,
        paymentMethod: entryMethod,
        accountDetail: entryAccount,
        tid: entryTid,
        createExpense
      });
      setEntryMsg('ok:Transaction recorded successfully in ledger.');
      setEntryDesc('');
      setEntryQty('');
      setEntryRate('');
      setEntryAmt('');
      setEntryTid('');
      setEntryAccount('');
      if (ledgerPersonId === selectedPersonId) {
        loadLedger();
      }
    } catch (err) {
      setEntryMsg('err:' + err.message);
    } finally {
      setEntrySaving(false);
    }
  };

  const handleApproveEntry = async (entryId) => {
    try {
      setLedgerLoading(true);
      await approvePersonEntry(entryId);
      await loadLedger();
    } catch (err) {
      alert('Error approving entry: ' + err.message);
      setLedgerLoading(false);
    }
  };

  const handleCancelEntry = async (entryId) => {
    const reason = window.prompt('Enter reason for cancellation:');
    if (reason === null) return;
    try {
      setLedgerLoading(true);
      await cancelPersonEntry(entryId, reason);
      await loadLedger();
    } catch (err) {
      alert('Error cancelling entry: ' + err.message);
      setLedgerLoading(false);
    }
  };

  // Print Person Ledger
  const handlePrintLedger = () => {
    const { person, entries, summary } = ledgerData;
    if (!person) return;

    const win = window.open('', '_blank');
    if (!win) { alert('Please allow popups to print statements.'); return; }

    const rowsHtml = (entries || []).map((e, idx) => `
      <tr style="border-bottom:1px solid #e5e7eb;">
        <td style="padding:8px 10px;font-size:11px;">${idx + 1}</td>
        <td style="padding:8px 10px;font-size:11px;">${fmtDate(e.entry_date)}</td>
        <td style="padding:8px 10px;font-size:11px;">${e.reference_number}</td>
        <td style="padding:8px 10px;font-size:11px;font-weight:600;">${e.entry_type.replace(/_/g, ' ')}</td>
        <td style="padding:8px 10px;font-size:11px;">${e.description}</td>
        <td style="padding:8px 10px;font-size:11px;text-align:right;color:#d9534f;">${e.debit > 0 ? 'Rs. ' + fmtNum(e.debit) : '—'}</td>
        <td style="padding:8px 10px;font-size:11px;text-align:right;color:#2e7d32;">${e.credit > 0 ? 'Rs. ' + fmtNum(e.credit) : '—'}</td>
        <td style="padding:8px 10px;font-size:11px;text-align:right;font-weight:bold;">Rs. ${fmtNum(e.balance)}</td>
      </tr>
    `).join('');

    const html = `<!DOCTYPE html>
<html>
<head>
  <title>Statement - ${person.name}</title>
  <style>
    @page { size: A4 portrait; margin: 12mm; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1f2937; margin: 0; padding: 20px; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0e7c86; padding-bottom: 12px; margin-bottom: 16px; }
    .logo { font-size: 20px; font-weight: 700; color: #0e7c86; }
    .title { font-size: 16px; font-weight: 700; }
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
    .kpi { background: #f5f3ed; border: 1px solid #e0ddd5; border-radius: 6px; padding: 10px; }
    .kpi-lbl { font-size: 10px; color: #6b7280; text-transform: uppercase; font-weight: 600; }
    .kpi-num { font-size: 15px; font-weight: 700; color: #111827; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; margin-top: 14px; }
    th { text-align: left; padding: 8px 10px; border-bottom: 2px solid #d1d5db; font-size: 11px; font-weight: 600; background: #f9fafb; }
    .sig { display: flex; justify-content: space-between; margin-top: 40px; padding-top: 20px; }
    .sig-line { width: 180px; border-top: 1px solid #9ca3af; text-align: center; font-size: 11px; color: #4b5563; padding-top: 6px; }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <div class="logo">ELITE WASH</div>
      <div style="font-size:11px;color:#6b7280;">Surf Stock &amp; Ledger Control System</div>
    </div>
    <div style="text-align:right;">
      <div class="title">WORKER &amp; SERVICE PROVIDER STATEMENT</div>
      <div style="font-size:11px;color:#4b5563;">Date: ${new Date().toLocaleDateString('en-PK')}</div>
    </div>
  </div>

  <div style="margin-bottom:16px;background:#FAFBF8;border:1px solid #E5E7EB;border-radius:6px;padding:12px;">
    <strong>${person.name}</strong> (${person.category}) &nbsp;|&nbsp; Code: <strong>${person.code}</strong> &nbsp;|&nbsp; Phone: ${person.phone || '—'} &nbsp;|&nbsp; CNIC: ${person.cnic || '—'}
  </div>

  <div class="kpi-grid">
    <div class="kpi"><div class="kpi-lbl">Opening Balance</div><div class="kpi-num">Rs. ${fmtNum(summary.openingBalance)}</div></div>
    <div class="kpi"><div class="kpi-lbl">Work Earned</div><div class="kpi-num" style="color:#2e7d32;">Rs. ${fmtNum(summary.workEarned)}</div></div>
    <div class="kpi"><div class="kpi-lbl">Total Paid${summary.commissionPaid > 0 ? ' (incl. Rs. ' + fmtNum(summary.commissionPaid) + ' commission)' : ''}</div><div class="kpi-num" style="color:#d9534f;">Rs. ${fmtNum(summary.paid)}</div></div>
    <div class="kpi"><div class="kpi-lbl">Net Closing Position</div><div class="kpi-num" style="color:#0e7c86;">${summary.closingPayable > 0 ? 'Rs. ' + fmtNum(summary.closingPayable) + ' (Payable)' : 'Rs. ' + fmtNum(summary.closingReceivable) + ' (Advance)'}</div></div>
  </div>

  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Date</th>
        <th>Ref No</th>
        <th>Type</th>
        <th>Description</th>
        <th style="text-align:right;">Paid (Debit)</th>
        <th style="text-align:right;">Earned (Credit)</th>
        <th style="text-align:right;">Balance</th>
      </tr>
    </thead>
    <tbody>
      ${rowsHtml || '<tr><td colspan="8" style="text-align:center;padding:20px;">No entries found.</td></tr>'}
    </tbody>
  </table>

  <div class="sig">
    <div class="sig-line">Prepared By (Accounts)</div>
    <div class="sig-line">Worker / Party Signature</div>
    <div class="sig-line">Approved By (Manager)</div>
  </div>

  <script>window.onload = function() { window.print(); };</script>
</body>
</html>`;

    win.document.open();
    win.document.write(html);
    win.document.close();
  };

  // Export PDF via jsPDF
  const handleDownloadPdf = () => {
    const { person, entries, summary } = ledgerData;
    if (!person) return;

    const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' });

    doc.setFontSize(16);
    doc.setTextColor(14, 124, 134);
    doc.text('ELITE WASH', 40, 40);

    doc.setFontSize(9);
    doc.setTextColor(107, 114, 128);
    doc.text('Worker & Service Provider Financial Ledger', 40, 52);

    doc.setFontSize(12);
    doc.setTextColor(17, 24, 39);
    doc.text(`${person.name} (${person.code})`, doc.internal.pageSize.getWidth() - 40, 40, { align: 'right' });

    doc.setFontSize(9);
    doc.text(`Category: ${person.category} | Generated: ${new Date().toLocaleDateString('en-PK')}`, doc.internal.pageSize.getWidth() - 40, 52, { align: 'right' });

    const rows = (entries || []).map((e, idx) => [
      idx + 1,
      fmtDate(e.entry_date),
      e.reference_number,
      e.entry_type.replace(/_/g, ' '),
      e.description,
      e.debit > 0 ? fmtNum(e.debit) : '—',
      e.credit > 0 ? fmtNum(e.credit) : '—',
      fmtNum(e.balance)
    ]);

    autoTable(doc, {
      startY: 70,
      head: [['#', 'Date', 'Ref No', 'Type', 'Description', 'Debit', 'Credit', 'Balance (PKR)']],
      body: rows,
      theme: 'grid',
      headStyles: { fillColor: [14, 124, 134], textColor: 255, fontSize: 8 },
      bodyStyles: { fontSize: 8, cellPadding: 4 },
      columnStyles: {
        5: { halign: 'right' },
        6: { halign: 'right' },
        7: { halign: 'right', fontStyle: 'bold' }
      }
    });

    const finalY = doc.lastAutoTable.finalY + 25;
    doc.setFontSize(9);
    doc.setTextColor(17, 24, 39);
    doc.text(`Opening: PKR ${fmtNum(summary.openingBalance)}  |  Earned: PKR ${fmtNum(summary.workEarned)}  |  Paid: PKR ${fmtNum(summary.paid)}  |  Closing: PKR ${fmtNum(summary.closingBalance)}`, 40, finalY);

    doc.save(`Statement_${person.code}_${todayISO()}.pdf`);
  };

  // WhatsApp Share
  const handleWhatsAppShare = () => {
    const { person, summary } = ledgerData;
    if (!person) return;
    const target = formatPakistaniPhoneForWhatsApp(person.phone);

    if (!target) {
      alert(`Cannot open WhatsApp: Worker ${person.name} has no valid registered phone number.`);
      return;
    }

    const text = `*ELITE WASH — Account Statement*
Worker: *${person.name}* (${person.code})
Category: ${person.category}
Date: ${new Date().toLocaleDateString('en-PK')}

• Opening Balance: PKR ${fmtNum(summary.openingBalance)}
• Work Earned: PKR ${fmtNum(summary.workEarned)}
• Paid / Advances: PKR ${fmtNum(summary.paid)}
• Commission Earned: PKR ${fmtNum(summary.commissionEarned)}
----------------------------------
*Net Closing Position: PKR ${fmtNum(summary.closingBalance)}*
(${summary.closingPayable > 0 ? 'Payable by Company' : 'Advance Balance with Worker'})

_Generated via Elite Wash ERP_`;

    const url = `https://wa.me/${target}?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
  };

  // ── Print Official Payment Voucher ────────────────────────────────────────
  const handlePrintVoucher = (entry) => {
    const person = ledgerData.person;
    if (!person) return;
    const voucherData = {
      voucherNo: entry.reference_number,
      date: entry.entry_date,
      beneficiaryName: person.name,
      beneficiaryCategory: person.category,
      beneficiaryCode: person.code,
      beneficiaryPhone: person.phone,
      beneficiaryCnic: person.cnic,
      amount: entry.debit > 0 ? entry.debit : (entry.credit > 0 ? entry.credit : entry.amount),
      paymentType: entry.entry_type,
      paymentMethod: entry.payment_method || 'Cash',
      accountDetail: entry.account_detail || '',
      tid: entry.tid || '',
      description: entry.description,
      runningBalance: entry.balance,
      status: entry.status || 'Approved'
    };
    printPersonPaymentVoucher(voucherData);
  };

  // ── Share Signed Voucher PDF on WhatsApp ──────────────────────────────────
  const handleWhatsAppVoucher = async (entry) => {
    const person = ledgerData.person;
    if (!person) return;

    let targetWindow = null;
    if (typeof window !== 'undefined') {
      targetWindow = window.open('about:blank', '_blank');
    }

    const formattedPhone = formatPakistaniPhoneForWhatsApp(person.phone);
    if (!formattedPhone) {
      if (targetWindow && !targetWindow.closed) {
        try { targetWindow.close(); } catch (_) {}
      }
      alert(`Cannot open WhatsApp: Beneficiary ${person.name} has no valid registered phone number.`);
      return;
    }

    setSharingEntryId(entry.id);
    const voucherData = {
      voucherNo: entry.reference_number,
      date: entry.entry_date,
      beneficiaryName: person.name,
      beneficiaryCategory: person.category,
      beneficiaryCode: person.code,
      beneficiaryPhone: person.phone,
      beneficiaryCnic: person.cnic,
      amount: entry.debit > 0 ? entry.debit : (entry.credit > 0 ? entry.credit : entry.amount),
      paymentType: entry.entry_type,
      paymentMethod: entry.payment_method || 'Cash',
      accountDetail: entry.account_detail || '',
      tid: entry.tid || '',
      description: entry.description,
      runningBalance: entry.balance,
      status: entry.status || 'Approved'
    };

    try {
      await sharePersonPaymentVoucherOnWhatsApp(voucherData, {
        targetWindow,
        beneficiary: person,
        onSuccess: (successMsg, details) => {
          if (details && details.mode === 'download_and_chat') {
            setShareModal({
              beneficiaryName: person.name,
              phone: formattedPhone,
              filename: details.filename,
              waUrl: details.waUrl,
              popupBlocked: details.popupBlocked
            });
          }
        },
        onError: (errMsg) => {
          if (targetWindow && !targetWindow.closed) {
            try { targetWindow.close(); } catch (_) {}
          }
          alert(errMsg);
        }
      });
    } catch (err) {
      if (targetWindow && !targetWindow.closed) {
        try { targetWindow.close(); } catch (_) {}
      }
      alert('Failed to generate or share voucher: ' + err.message);
    } finally {
      setSharingEntryId(null);
    }
  };

  // Filter persons in directory
  const filteredPersons = persons.filter(p => {
    const q = (personSearch || searchTerm).trim().toLowerCase();
    if (!q) return true;
    return (
      (p.name || '').toLowerCase().includes(q) ||
      (p.code || '').toLowerCase().includes(q) ||
      (p.phone || '').includes(q) ||
      (p.cnic || '').includes(q) ||
      (p.category || '').toLowerCase().includes(q)
    );
  });

  return (
    <div>
      {/* Tab Header */}
      <div className="panel" style={{ padding: 0, marginBottom: 20 }}>
        <div className="tabs" style={{ padding: '16px 24px 0', margin: 0 }}>
          <div
            className={`tab${activeTab === 'directory' ? ' active' : ''}`}
            onClick={() => setActiveTab('directory')}
          >
            Worker &amp; Service Provider Directory
          </div>
          <div
            className={`tab${activeTab === 'entry' ? ' active' : ''}`}
            onClick={() => setActiveTab('entry')}
          >
            Work &amp; Payment Entry
          </div>
          <div
            className={`tab${activeTab === 'ledger' ? ' active' : ''}`}
            onClick={() => setActiveTab('ledger')}
          >
            Date-Wise Person Ledger
          </div>
        </div>
      </div>

      {/* TAB 1: PERSON DIRECTORY */}
      {activeTab === 'directory' && (
        <div className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
            <div className="section-head" style={{ margin: 0 }}>
              <h2>Persons &amp; Service Providers</h2>
              <p style={{ fontSize: 12, color: 'var(--text-dim)', margin: 0 }}>Labourers, helpers, transporters, manufacturers &amp; service providers</p>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="text"
                placeholder="Search name, code, phone..."
                value={personSearch}
                onChange={e => setPersonSearch(e.target.value)}
                style={{ padding: '5px 10px', fontSize: 12, border: '1px solid var(--line)', borderRadius: 6, width: 190 }}
              />
              <select
                value={catFilter}
                onChange={e => setCatFilter(e.target.value)}
                style={{ padding: '5px 8px', fontSize: 12, border: '1px solid var(--line)', borderRadius: 6 }}
              >
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              {canManage && (
                <button className="btn primary" onClick={handleOpenAdd}>
                  + Add Person
                </button>
              )}
            </div>
          </div>

          {loading ? (
            <div style={{ padding: 30, textAlign: 'center', color: 'var(--text-dim)' }}>Loading directory...</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Contact</th>
                  <th>Default Rate</th>
                  <th>Opening Payable</th>
                  <th>Opening Advance</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredPersons.length === 0 ? (
                  <tr>
                    <td colSpan={9} style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>
                      No persons registered yet. Click &quot;+ Add Person&quot; to register workers.
                    </td>
                  </tr>
                ) : (
                  filteredPersons.map(p => (
                    <tr key={p.id}>
                      <td style={{ fontWeight: 600, fontSize: 11.5 }}>{p.code}</td>
                      <td>
                        <div style={{ fontWeight: 600 }}>{p.name}</div>
                        {p.cnic && <div style={{ fontSize: 10.5, color: 'var(--text-dim)' }}>CNIC: {p.cnic}</div>}
                      </td>
                      <td>
                        <span className={`badge ${
                          p.category === 'Labourer' ? 'teal' :
                          p.category === 'Transporter' ? 'amber' :
                          p.category === 'Manufacturer' ? 'green' : 'gray'
                        }`}>
                          {p.category}
                        </span>
                      </td>
                      <td style={{ fontSize: 11.5 }}>{p.phone || '—'}</td>
                      <td style={{ fontSize: 11.5 }}>{p.default_rate > 0 ? `Rs. ${fmtNum(p.default_rate)}` : '—'}</td>
                      <td style={{ fontSize: 11.5, color: '#d9534f' }}>{p.opening_payable_balance > 0 ? `Rs. ${fmtNum(p.opening_payable_balance)}` : '0'}</td>
                      <td style={{ fontSize: 11.5, color: '#2e7d32' }}>{p.opening_receivable_balance > 0 ? `Rs. ${fmtNum(p.opening_receivable_balance)}` : '0'}</td>
                      <td>
                        <span className={`badge ${p.is_active ? 'green' : 'gray'}`}>
                          {p.is_active ? 'Active' : 'Disabled'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: 6 }}>
                          <button
                            className="btn ghost"
                            style={{ padding: '3px 8px', fontSize: 11 }}
                            onClick={() => {
                              setLedgerPersonId(p.id);
                              setActiveTab('ledger');
                            }}
                          >
                            Ledger
                          </button>
                          {canManage && (
                            <button
                              className="btn ghost"
                              style={{ padding: '3px 8px', fontSize: 11 }}
                              onClick={() => handleOpenEdit(p)}
                            >
                              Edit
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* TAB 2: WORK & PAYMENT ENTRY */}
      {activeTab === 'entry' && (
        <div className="panel" style={{ maxWidth: 640 }}>
          <div className="section-head">
            <h2>Record Work Earning or Payment</h2>
            <p style={{ fontSize: 12, color: 'var(--text-dim)', margin: 0 }}>Post piece-rate work, cash/bank payments, or advances into person ledger</p>
          </div>

          <Msg msg={entryMsg} />

          <form onSubmit={handleSubmitEntry}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="field">
                <label>Select Worker / Service Provider *</label>
                <select
                  value={selectedPersonId}
                  onChange={e => {
                    setSelectedPersonId(e.target.value);
                    const p = persons.find(x => x.id === e.target.value);
                    if (p && p.default_rate > 0) {
                      setEntryRate(String(p.default_rate));
                    }
                  }}
                  required
                >
                  <option value="">-- Choose Person --</option>
                  {persons.map(p => (
                    <option key={p.id} value={p.id}>{p.name} ({p.code} — {p.category})</option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label>Transaction Type *</label>
                <select value={entryType} onChange={e => setEntryType(e.target.value)}>
                  {ENTRY_TYPES.map(t => <option key={t.key} value={t.key}>{t.label}</option>)}
                </select>
              </div>

              {entryType === 'Work_Earning' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div className="field">
                    <label>Quantity / Packets / Trips</label>
                    <input
                      type="number"
                      min="0"
                      step="any"
                      placeholder="e.g. 500"
                      value={entryQty}
                      onChange={e => setEntryQty(e.target.value)}
                    />
                  </div>
                  <div className="field">
                    <label>Rate (PKR per unit)</label>
                    <input
                      type="number"
                      min="0"
                      step="any"
                      placeholder="e.g. 2.50"
                      value={entryRate}
                      onChange={e => setEntryRate(e.target.value)}
                    />
                  </div>
                </div>
              )}

              <div className="field">
                <label>Total Amount (PKR) *</label>
                <input
                  type="number"
                  min="0"
                  step="any"
                  placeholder="0.00"
                  value={entryAmt}
                  onChange={e => setEntryAmt(e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label>Description / Work Details *</label>
                <input
                  type="text"
                  placeholder="e.g. Packaged 500 1kg bags, Cartage Vehari trip, Advance for Eid"
                  value={entryDesc}
                  onChange={e => setEntryDesc(e.target.value)}
                  required
                />
              </div>

              {(entryType === 'Payment' || entryType === 'Advance' || entryType === 'Commission_Paid') && (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div className="field">
                      <label>Payment Method</label>
                      <select value={entryMethod} onChange={e => setEntryMethod(e.target.value)}>
                        <option value="Cash">Cash</option>
                        <option value="Bank">Bank Transfer</option>
                        <option value="Cheque">Cheque</option>
                      </select>
                    </div>
                    <div className="field">
                      <label>TID / Cheque #</label>
                      <input
                        type="text"
                        placeholder="Transaction ID / Cheque #"
                        value={entryTid}
                        onChange={e => setEntryTid(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="field">
                    <label>Account Detail</label>
                    <input
                      type="text"
                      placeholder="e.g. HBL Main Branch, Cash Drawer A"
                      value={entryAccount}
                      onChange={e => setEntryAccount(e.target.value)}
                    />
                  </div>
                </>
              )}

              <div style={{ padding: '8px 12px', background: '#F5F3ED', borderRadius: 6, fontSize: 12 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', margin: 0 }}>
                  <input
                    type="checkbox"
                    checked={createExpense}
                    onChange={e => setCreateExpense(e.target.checked)}
                  />
                  <span>Post simultaneously into Company Expenses (Reuses central expenses ledger)</span>
                </label>
              </div>

              <button
                type="submit"
                className="btn primary"
                disabled={entrySaving || !canManage}
                style={{ marginTop: 8 }}
              >
                {entrySaving ? 'Saving...' : 'Post Entry to Ledger'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TAB 3: DATE-WISE PERSON LEDGER */}
      {activeTab === 'ledger' && (
        <div>
          {/* Filter Bar */}
          <div className="panel" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ minWidth: 220 }}>
                  <label style={{ fontSize: 11, color: 'var(--text-dim)', display: 'block', marginBottom: 2 }}>Worker / Party</label>
                  <select
                    value={ledgerPersonId}
                    onChange={e => setLedgerPersonId(e.target.value)}
                    style={{ width: '100%', padding: '6px 8px', fontSize: 12 }}
                  >
                    <option value="">-- Select Person --</option>
                    {persons.map(p => (
                      <option key={p.id} value={p.id}>{p.name} ({p.code} — {p.category})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 11, color: 'var(--text-dim)', display: 'block', marginBottom: 2 }}>From Date</label>
                  <input
                    type="date"
                    value={ledgerDateFrom}
                    onChange={e => setLedgerDateFrom(e.target.value)}
                    style={{ padding: '5px 8px', fontSize: 12 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 11, color: 'var(--text-dim)', display: 'block', marginBottom: 2 }}>To Date</label>
                  <input
                    type="date"
                    value={ledgerDateTo}
                    onChange={e => setLedgerDateTo(e.target.value)}
                    style={{ padding: '5px 8px', fontSize: 12 }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button className="btn ghost" onClick={handlePrintLedger} disabled={!ledgerData.person}>
                  Print Statement
                </button>
                <button className="btn ghost" onClick={handleDownloadPdf} disabled={!ledgerData.person}>
                  PDF
                </button>
                <button className="btn primary" onClick={handleWhatsAppShare} disabled={!ledgerData.person}>
                  WhatsApp
                </button>
              </div>
            </div>
          </div>

          {/* KPI Summary Tiles */}
          {ledgerData.person && (
            <div className="grid g4" style={{ marginBottom: 16 }}>
              <div className="tile teal">
                <div className="bar" />
                <div className="label">Opening Position</div>
                <div className="num">Rs. {fmtNum(ledgerData.summary?.openingBalance)}</div>
              </div>
              <div className="tile green">
                <div className="bar" />
                <div className="label">Work Earned</div>
                <div className="num">Rs. {fmtNum(ledgerData.summary?.workEarned)}</div>
              </div>
              <div className="tile amber">
                <div className="bar" />
                <div className="label">Total Paid</div>
                <div className="num">Rs. {fmtNum(ledgerData.summary?.paid)}</div>
                {ledgerData.summary?.commissionPaid > 0 && (
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                    incl. Rs. {fmtNum(ledgerData.summary?.commissionPaid)} commission
                  </div>
                )}
              </div>
              <div className="tile red">
                <div className="bar" />
                <div className="label">
                  {ledgerData.summary?.closingPayable > 0 ? 'Closing Payable (Owed)' : 'Closing Advance'}
                </div>
                <div className="num">
                  Rs. {fmtNum(ledgerData.summary?.closingPayable > 0 ? ledgerData.summary?.closingPayable : ledgerData.summary?.closingReceivable)}
                </div>
              </div>
            </div>
          )}

          {/* Ledger Table */}
          <div className="panel">
            {ledgerLoading ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)' }}>Loading ledger...</div>
            ) : !ledgerData.person ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)' }}>Please select a person to display their date-wise ledger.</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Ref #</th>
                    <th>Type</th>
                    <th>Description</th>
                    <th style={{ textAlign: 'right' }}>Paid (Debit)</th>
                    <th style={{ textAlign: 'right' }}>Earned (Credit)</th>
                    <th style={{ textAlign: 'right' }}>Running Balance</th>
                    <th>Method / TID</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'center' }}>Voucher &amp; Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {ledgerData.entries.length === 0 ? (
                    <tr>
                      <td colSpan={10} style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>
                        No transactions recorded for this worker in the selected period.
                      </td>
                    </tr>
                  ) : (
                    ledgerData.entries.map(e => (
                      <tr key={e.id}>
                        <td style={{ fontSize: 11.5 }}>{fmtDate(e.entry_date)}</td>
                        <td style={{ fontSize: 11 }}>{e.reference_number}</td>
                        <td>
                          <span className={`badge ${
                            e.entry_type === 'Work_Earning' ? 'green' :
                            e.entry_type === 'Payment' ? 'amber' :
                            e.entry_type === 'Advance' ? 'teal' : 'gray'
                          }`}>
                            {e.entry_type.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td style={{ fontSize: 12 }}>
                          {e.description}
                          {e.quantity > 0 && e.rate > 0 && (
                            <span style={{ fontSize: 11, color: 'var(--text-dim)', marginLeft: 6 }}>
                              ({e.quantity} @ Rs {e.rate})
                            </span>
                          )}
                        </td>
                        <td style={{ textAlign: 'right', fontSize: 12, color: e.debit > 0 ? 'var(--red)' : 'inherit' }}>
                          {e.debit > 0 ? `Rs. ${fmtNum(e.debit)}` : '—'}
                        </td>
                        <td style={{ textAlign: 'right', fontSize: 12, color: e.credit > 0 ? 'var(--green)' : 'inherit' }}>
                          {e.credit > 0 ? `Rs. ${fmtNum(e.credit)}` : '—'}
                        </td>
                        <td style={{ textAlign: 'right', fontWeight: 600, fontSize: 12 }}>
                          Rs. {fmtNum(e.balance)}
                        </td>
                        <td style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                          {e.payment_method || '—'} {e.tid ? `(${e.tid})` : ''}
                        </td>
                        <td>
                          <span className={`badge ${
                            e.status === 'Approved' ? 'green' :
                            e.status === 'Pending' ? 'amber' : 'red'
                          }`}>
                            {e.status || 'Approved'}
                          </span>
                        </td>
                        <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                          <div style={{ display: 'flex', gap: 4, justifyContent: 'center', alignItems: 'center' }}>
                            <button
                              className="btn ghost"
                              style={{ padding: '2px 6px', fontSize: 11 }}
                              onClick={() => handlePrintVoucher(e)}
                              title="Print Official Payment / Work Voucher"
                            >
                              Voucher
                            </button>
                            <button
                              className="btn"
                              style={{
                                padding: '2px 6px',
                                fontSize: 11,
                                background: '#25d366',
                                color: '#fff',
                                border: 'none',
                                opacity: sharingEntryId === e.id ? 0.7 : 1,
                                cursor: sharingEntryId === e.id ? 'wait' : 'pointer'
                              }}
                              disabled={sharingEntryId === e.id}
                              onClick={() => handleWhatsAppVoucher(e)}
                              title="Share Signed Payment Voucher PDF on WhatsApp"
                            >
                              {sharingEntryId === e.id ? 'PDF...' : 'WA'}
                            </button>
                            {canApprove && e.status === 'Pending' && (
                              <>
                                <button
                                  className="btn"
                                  style={{ padding: '2px 6px', fontSize: 10.5, background: 'var(--green)', color: '#fff', border: 'none' }}
                                  onClick={() => handleApproveEntry(e.id)}
                                  title="Approve Entry"
                                >
                                  Approve
                                </button>
                                <button
                                  className="btn"
                                  style={{ padding: '2px 6px', fontSize: 10.5, background: 'var(--red)', color: '#fff', border: 'none' }}
                                  onClick={() => handleCancelEntry(e.id)}
                                  title="Cancel Entry"
                                >
                                  Cancel
                                </button>
                              </>
                            )}
                            {canApprove && e.status === 'Approved' && (
                              <button
                                className="btn ghost"
                                style={{ padding: '2px 6px', fontSize: 10.5, color: 'var(--red)' }}
                                onClick={() => handleCancelEntry(e.id)}
                                title="Reverse / Cancel"
                              >
                                Reverse
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* MODAL: ADD / EDIT PERSON */}
      {showPersonModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20
        }}>
          <div style={{
            background: 'var(--panel)', borderRadius: 8, width: '100%', maxWidth: 520,
            padding: 24, boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h3 style={{ margin: 0, fontSize: 16 }}>{editingPerson ? 'Edit Worker Profile' : 'Register New Worker / Service Provider'}</h3>
              <button className="btn ghost" onClick={() => setShowPersonModal(false)} style={{ padding: '2px 8px' }}>✕</button>
            </div>

            <Msg msg={modalMsg} />

            <form onSubmit={handleSavePerson}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, maxHeight: '60vh', overflowY: 'auto', paddingRight: 4 }}>
                <div className="field">
                  <label>Code *</label>
                  <input
                    value={personForm.code}
                    onChange={e => setPersonForm({ ...personForm, code: e.target.value })}
                    required
                  />
                </div>
                <div className="field">
                  <label>Category *</label>
                  <select
                    value={personForm.category}
                    onChange={e => setPersonForm({ ...personForm, category: e.target.value })}
                  >
                    {CATEGORIES.filter(c => c !== 'All').map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>Full Name *</label>
                  <input
                    value={personForm.name}
                    onChange={e => setPersonForm({ ...personForm, name: e.target.value })}
                    placeholder="e.g. Muhammad Rashid"
                    required
                  />
                </div>
                <div className="field">
                  <label>Phone Number</label>
                  <input
                    value={personForm.phone}
                    onChange={e => setPersonForm({ ...personForm, phone: e.target.value })}
                    placeholder="03xx-xxxxxxx"
                  />
                </div>
                <div className="field">
                  <label>CNIC</label>
                  <input
                    value={personForm.cnic}
                    onChange={e => setPersonForm({ ...personForm, cnic: e.target.value })}
                    placeholder="36601-xxxxxxx-x"
                  />
                </div>
                <div className="field">
                  <label>Default Rate (PKR / Unit)</label>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={personForm.default_rate}
                    onChange={e => setPersonForm({ ...personForm, default_rate: e.target.value })}
                    placeholder="e.g. 2.50"
                  />
                </div>
                <div className="field">
                  <label>Commission Rate (PKR)</label>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={personForm.commission_rate}
                    onChange={e => setPersonForm({ ...personForm, commission_rate: e.target.value })}
                    placeholder="e.g. 10.00"
                  />
                </div>
                <div className="field">
                  <label>Opening Payable (PKR)</label>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={personForm.opening_payable_balance}
                    onChange={e => setPersonForm({ ...personForm, opening_payable_balance: e.target.value })}
                    placeholder="Company owes them"
                  />
                </div>
                <div className="field">
                  <label>Opening Advance (PKR)</label>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={personForm.opening_receivable_balance}
                    onChange={e => setPersonForm({ ...personForm, opening_receivable_balance: e.target.value })}
                    placeholder="They owe company"
                  />
                </div>
                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>Address</label>
                  <input
                    value={personForm.address}
                    onChange={e => setPersonForm({ ...personForm, address: e.target.value })}
                    placeholder="Locality / Village / Station"
                  />
                </div>
                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>Notes</label>
                  <input
                    value={personForm.notes}
                    onChange={e => setPersonForm({ ...personForm, notes: e.target.value })}
                    placeholder="Special terms, vehicle no, etc."
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
                <button type="button" className="btn ghost" onClick={() => setShowPersonModal(false)}>Cancel</button>
                <button type="submit" className="btn primary" disabled={modalSaving}>
                  {modalSaving ? 'Saving...' : editingPerson ? 'Update Person' : 'Register Person'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── WHATSAPP SHARE INSTRUCTIONS MODAL ──────────────────────────── */}
      {shareModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="panel" style={{ width: 500, maxWidth: '92%', padding: 24, boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, borderBottom: '1px solid var(--line)', paddingBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#25d366', color: '#fff', display: 'grid', placeItems: 'center', fontWeight: 'bold' }}>✓</div>
                <div>
                  <h3 style={{ margin: 0, fontSize: 16 }}>Payment Voucher PDF Ready to Share</h3>
                  <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>{shareModal.beneficiaryName} &bull; +{shareModal.phone}</div>
                </div>
              </div>
              <button className="btn ghost" style={{ padding: '4px 8px' }} onClick={() => setShareModal(null)}>✕</button>
            </div>

            <div style={{ background: '#FAFBF8', border: '1px solid var(--line)', borderRadius: 6, padding: 14, fontSize: 13, lineHeight: 1.6, marginBottom: 16 }}>
              <div style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 18 }}>📄</span>
                <div>
                  <strong>Downloaded Payment Voucher:</strong>
                  <div style={{ color: 'var(--teal)', fontWeight: 600 }}>{shareModal.filename}</div>
                </div>
              </div>
              <div style={{ padding: '10px 12px', background: '#FFF8E7', border: '1px solid #F0D78C', borderRadius: 6, fontSize: 12.5, color: '#856404' }}>
                <strong>How to complete sending on WhatsApp:</strong>
                <ol style={{ margin: '6px 0 0 16px', padding: 0 }}>
                  <li>WhatsApp chat with <strong>{shareModal.beneficiaryName}</strong> (+{shareModal.phone}) opens in your browser.</li>
                  <li>In WhatsApp, click the <strong>attach icon (📎) &rarr; Document</strong>.</li>
                  <li>Select the downloaded <strong>{shareModal.filename}</strong> from your Downloads folder.</li>
                  <li>Click <strong>Send</strong> to deliver the signed voucher slip.</li>
                </ol>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
              <button
                className="btn primary"
                style={{ fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 6 }}
                onClick={() => window.open(shareModal.waUrl, '_blank')}
              >
                <span>💬</span> Open WhatsApp Chat
              </button>
              <button className="btn ghost" onClick={() => setShareModal(null)}>
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

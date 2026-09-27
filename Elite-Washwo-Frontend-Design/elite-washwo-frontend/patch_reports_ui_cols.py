with open('src/components/ReportsPage.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Update Recovery Table Headers
old_rec_th = "<thead><tr><th>Date</th><th>Distributor</th><th className=\"num-cell\">Amount</th><th>Account Detail</th><th>TID</th><th>Notes</th></tr></thead>"
new_rec_th = "<thead><tr><th>Date</th><th>Reference</th><th>Distributor</th><th className=\"num-cell\">Amount</th><th>Account Detail</th><th>TID</th><th>Notes</th><th>Status</th></tr></thead>"
c = c.replace(old_rec_th, new_rec_th)

# Update Recovery Table Rows
old_rec_td = """                        <td>{fmtDateTime(r.recovery_date)}</td>
                        <td>{r.distributors ? `${r.distributors.code} - ${r.distributors.name}` : '—'}</td>
                        <td className="num-cell" style={{ fontWeight: 600 }}>PKR {fmtNum(r.amount)}</td>"""
new_rec_td = """                        <td>{fmtDateTime(r.recovery_date)}</td>
                        <td style={{ fontFamily: 'monospace' }}>{r.reference_number || '—'}</td>
                        <td>{r.distributors ? `${r.distributors.code} - ${r.distributors.name}` : '—'}</td>
                        <td className="num-cell" style={{ fontWeight: 600 }}>PKR {fmtNum(r.amount)}</td>"""
c = c.replace(old_rec_td, new_rec_td)

# And add status to Recovery Table Rows
old_rec_td2 = "<td>{r.notes || '—'}</td>"
new_rec_td2 = "<td>{r.notes || '—'}</td>\n                        <td><span className=\"badge green\">{r.status || 'Approved'}</span></td>"
c = c.replace(old_rec_td2, new_rec_td2)


# Update Expense Table Headers
old_exp_th = "<thead><tr><th>Date</th><th>Type</th><th>Distributor</th><th>Head</th><th className=\"num-cell\">Amount</th><th>Account Detail</th><th>TID</th><th>Notes</th></tr></thead>"
new_exp_th = "<thead><tr><th>Date</th><th>Reference</th><th>Type</th><th>Distributor</th><th>Head</th><th className=\"num-cell\">Amount</th><th>Account Detail</th><th>TID</th><th>Notes</th><th>Status</th></tr></thead>"
c = c.replace(old_exp_th, new_exp_th)

# Update Expense Table Rows
old_exp_td = """                        <td>{fmtDateTime(e.expense_date)}</td>
                        <td>{e.category}</td>"""
new_exp_td = """                        <td>{fmtDateTime(e.expense_date)}</td>
                        <td style={{ fontFamily: 'monospace' }}>{e.reference_number || '—'}</td>
                        <td>{e.category}</td>"""
c = c.replace(old_exp_td, new_exp_td)

# And add status to Expense Table Rows
old_exp_td2 = "<td>{e.description || '—'}</td>"
new_exp_td2 = "<td>{e.description || '—'}</td>\n                        <td><span className=\"badge green\">{e.status || 'Approved'}</span></td>"
c = c.replace(old_exp_td2, new_exp_td2)

# Update colspans
c = c.replace('colSpan="6"', 'colSpan="8"')
c = c.replace('colSpan="8"', 'colSpan="10"')

with open('src/components/ReportsPage.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated ReportsPage.jsx tables')

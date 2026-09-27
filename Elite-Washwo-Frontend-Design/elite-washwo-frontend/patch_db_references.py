with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

# Add reference_number to expenses
c = c.replace(
    ".select('amount, expense_date, category, status, account_detail, tid, description, head, distributor_id, distributors(name, code)')",
    ".select('reference_number, amount, expense_date, category, status, account_detail, tid, description, head, distributor_id, distributors(name, code)')"
)

# Add reference_number to recoveries
c = c.replace(
    ".select('amount, recovery_date, status, account_detail, tid, notes, distributor_id, distributors(name, code)')",
    ".select('reference_number, amount, recovery_date, status, account_detail, tid, notes, distributor_id, distributors(name, code)')"
)

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated db.js to select reference_numbers')

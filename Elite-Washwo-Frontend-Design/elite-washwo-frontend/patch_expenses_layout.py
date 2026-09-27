with open('src/components/ExpensesPage.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    '<div className="grid g2" style={{ gridTemplateColumns: \'350px 1fr\', alignItems: \'start\' }}>',
    '<div style={{ display: \'flex\', flexDirection: \'column\', gap: 20 }}>'
)

with open('src/components/ExpensesPage.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated layout to stack Record Expense and Expense Ledger')

import re

content = open('src/main.jsx', 'r', encoding='utf-8-sig').read()

# Fix user reference in StockPage
old_stock = "function StockPage({ searchTerm = '' }) {\n  const { data: salesmen }   = useAsync(fetchSalesmen);\n  const { data: packagings } = useAsync(fetchPackagings);\n  const { role, hasPermission } = useAuth();"
new_stock = "function StockPage({ searchTerm = '' }) {\n  const { data: salesmen }   = useAsync(fetchSalesmen);\n  const { data: packagings } = useAsync(fetchPackagings);\n  const { role, user, hasPermission } = useAuth();"
content = content.replace(old_stock, new_stock)

# Fix user reference in ExpensesPage
old_exp = "function ExpensesPage({ searchTerm = '' }) {\n  const { data: salesmen } = useAsync(fetchSalesmen);\n  const { data: expenses, loading: el, reload } = useAsync(fetchExpenses);\n  const { data: summary } = useAsync(fetchExpenseSummary);\n  const { role, hasPermission } = useAuth();"
new_exp = "function ExpensesPage({ searchTerm = '' }) {\n  const { data: salesmen } = useAsync(fetchSalesmen);\n  const { data: expenses, loading: el, reload } = useAsync(fetchExpenses);\n  const { data: summary } = useAsync(fetchExpenseSummary);\n  const { role, user, hasPermission } = useAuth();"
content = content.replace(old_exp, new_exp)

# Extract Pagination
idx1 = content.find('function Pagination(')
if idx1 != -1:
    idx2 = content.find('  );\n}', idx1) + 6
    pagination_str = content[idx1:idx2]
    content = content[:idx1] + content[idx2:]
    
    idx3 = content.find('function StockPage(')
    content = content[:idx3] + pagination_str + '\n' + content[idx3:]

open('src/main.jsx', 'w', encoding='utf-8', newline='\n').write(content)
print("Fixed bugs")

with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

if 'import ReportsPage' not in c:
    c = c.replace("import ExpensesPage from './components/ExpensesPage';", "import ExpensesPage from './components/ExpensesPage';\nimport ReportsPage from './components/ReportsPage';")

with open('src/main.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Import added successfully")

with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Add import
if 'import ExpensesPage from' not in c:
    c = c.replace(
        "import OverviewPage from './components/OverviewPage';",
        "import OverviewPage from './components/OverviewPage';\nimport ExpensesPage from './components/ExpensesPage';"
    )

# Remove the inline ExpensesPage
match = re.search(r'function ExpensesPage\(.*?\{.*?(?=\n// ── Customers Page|\nfunction CustomersPage)', c, re.DOTALL)
if match:
    c = c.replace(match.group(0), '')
else:
    print('Regex failed to find inline ExpensesPage')

with open('src/main.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
print('main.jsx updated to use external ExpensesPage')

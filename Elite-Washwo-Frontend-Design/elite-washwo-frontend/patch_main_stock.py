with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Add import
if 'import StockPage from' not in c:
    c = c.replace(
        "import SalesPage from './components/SalesPage';",
        "import SalesPage from './components/SalesPage';\nimport StockPage from './components/StockPage';"
    )

# Remove the inline StockPage
match = re.search(r'function StockPage\(\{.*?(?=\n// ── Expenses Page|\nfunction ExpensesPage)', c, re.DOTALL)
if match:
    c = c.replace(match.group(0), '')
else:
    print('Regex failed to find inline StockPage')

with open('src/main.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
print('main.jsx updated to use external StockPage')

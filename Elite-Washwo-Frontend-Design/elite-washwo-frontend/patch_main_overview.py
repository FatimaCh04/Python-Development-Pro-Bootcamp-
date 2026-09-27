with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Add import
if 'import OverviewPage from' not in c:
    c = c.replace(
        "import StockPage from './components/StockPage';",
        "import StockPage from './components/StockPage';\nimport OverviewPage from './components/OverviewPage';"
    )

# Remove the inline OverviewPage
match = re.search(r'function OverviewPage\(.*?\{.*?(?=\n// ── Salesman Page|\nfunction SalesmanPage)', c, re.DOTALL)
if match:
    c = c.replace(match.group(0), '')
else:
    print('Regex failed to find inline OverviewPage')

with open('src/main.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
print('main.jsx updated to use external OverviewPage')

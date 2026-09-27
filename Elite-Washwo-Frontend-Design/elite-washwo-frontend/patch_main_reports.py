with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

import re

if 'import ReportsPage' not in c:
    c = c.replace("import AuditPage", "import ReportsPage from './components/ReportsPage';\nimport AuditPage")

c = re.sub(r'function ReportsPage\(\)\s*\{.*?\}\n*(?=function AuditPage)', '', c, flags=re.DOTALL)

with open('src/main.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('Patched main.jsx')

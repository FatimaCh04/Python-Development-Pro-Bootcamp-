import os

with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Add import
if 'DistributorsPage' not in c:
    c = c.replace("import SettingsPage from './components/SettingsPage';", "import SettingsPage from './components/SettingsPage';\nimport DistributorsPage from './components/DistributorsPage';")

# Add to NAV
if "key: 'distributors'" not in c:
    ops_idx = c.find("group: 'Operations'")
    insert_idx = c.find(']', ops_idx)
    nav_str = "\n      { key: 'distributors', label: 'Distributors', roles: ['Super_Admin', 'Manager', 'Salesman'], icon: <svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" strokeWidth=\"1.8\"><rect x=\"2\" y=\"7\" width=\"20\" height=\"14\" rx=\"2\" ry=\"2\"/><path d=\"M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16\"/></svg> },"
    c = c[:insert_idx] + nav_str + '\n    ' + c[insert_idx:]

# Add to Router case
if "case 'distributors':" not in c:
    c = c.replace("case 'customers':", "case 'distributors':\n        return <DistributorsPage searchTerm={globalSearch}/>;\n      case 'customers':")

# Add to PAGE_TITLES
if "distributors:" not in c:
    c = c.replace("customers: ['Customers', 'Directory, ledgers & customer returns'],", "customers: ['Customers', 'Directory, ledgers & customer returns'],\n  distributors: ['Distributors', 'Manage distributor information and commission details.'],")

with open('src/main.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
print('Updated main.jsx with DistributorsPage')

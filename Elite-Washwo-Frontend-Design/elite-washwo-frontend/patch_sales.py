with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add import
if 'SalesPage' not in c:
    c = c.replace(
        "import DistributorsPage from './components/DistributorsPage';",
        "import DistributorsPage from './components/DistributorsPage';\nimport SalesPage from './components/SalesPage';"
    )

# 2. Add to NAV — insert after distributors entry in Operations group
nav_dist_key = "{ key: 'distributors', label: 'Distributors',"
sales_nav = "\n      { key: 'sales', label: 'Sales', roles: ['Super_Admin', 'Manager'], icon: <svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" strokeWidth=\"1.8\"><path d=\"M6 2 3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z\"/><line x1=\"3\" y1=\"6\" x2=\"21\" y2=\"6\"/><path d=\"M16 10a4 4 0 01-8 0\"/></svg> },"
if "key: 'sales'" not in c and nav_dist_key in c:
    # insert after distributors nav item
    insert_after = nav_dist_key
    idx = c.find(insert_after)
    # find end of that line/entry (next comma at same level)
    end_idx = c.find('},', idx) + 2
    c = c[:end_idx] + sales_nav + c[end_idx:]

# 3. Add router case — before customers case
if "case 'sales':" not in c:
    c = c.replace(
        "case 'customers':",
        "case 'sales':\n        return <SalesPage searchTerm={globalSearch}/>;\n      case 'customers':"
    )

# 4. Add PAGE_TITLES entry
if "'sales':" not in c:
    c = c.replace(
        "distributors: ['Distributors', 'Manage distributor information and commission details.'],",
        "distributors: ['Distributors', 'Manage distributor information and commission details.'],\n  sales: ['Sales', 'Distributor sales, commission, advertisement and welfare accounts.'],"
    )

with open('src/main.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
print('main.jsx updated with SalesPage')

import re

def replace_in_file(path, replacements):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            c = f.read()
        for old, new in replacements:
            c = c.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print(f"Patched {path}")
    except Exception as e:
        print(f"Error patching {path}: {e}")

replace_in_file('src/components/BookingPage.jsx', [
    ('*Elite Washwo', '*Elite Wash'),
    ('<h2>Elite Washwo', '<h2>Elite Wash'),
    ('Elite Washwo ERP', 'Elite Wash ERP')
])

replace_in_file('src/components/Login.jsx', [
    ('<div className="brand-name">Elite Washwo</div>', '<div className="brand-name">Elite Wash</div>'),
    ('placeholder="you@elitewashwo.com"', 'placeholder="you@elitewash.com"')
])

replace_in_file('src/components/SalesPage.jsx', [
    ('*Elite Washwo', '*Elite Wash'),
    ('<h2>Elite Washwo', '<h2>Elite Wash'),
    ('Elite Washwo ERP', 'Elite Wash ERP')
])

replace_in_file('src/components/StockPage.jsx', [
    ('*Elite Washwo', '*Elite Wash'),
    ('<h2>Elite Washwo', '<h2>Elite Wash'),
    ('Elite Washwo ERP', 'Elite Wash ERP')
])

replace_in_file('src/lib/exportUtils.js', [
    ('Elite Washwo - Export', 'Elite Wash - Export'),
    ('- Elite Washwo</title>', '- Elite Wash</title>'),
    ('_Generated via Elite Washwo ERP_', '_Generated via Elite Wash ERP_')
])

replace_in_file('index.html', [
    ('<title>Elite Washwo', '<title>Elite Wash'),
    ('content="Elite Washwo', 'content="Elite Wash')
])

print("Branding cleanup complete")

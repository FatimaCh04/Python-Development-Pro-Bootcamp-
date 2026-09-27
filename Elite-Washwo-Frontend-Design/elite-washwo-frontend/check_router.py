with open('src/main.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

q = "case 'sales':"
idx = c.find(q)
if idx == -1:
    print("'sales' case NOT FOUND in router")
else:
    print("Found 'sales' case at", idx)
    print(c[idx:idx+300])

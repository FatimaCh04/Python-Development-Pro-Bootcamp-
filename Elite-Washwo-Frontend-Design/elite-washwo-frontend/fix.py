import re

content = open('src/main.jsx', 'r', encoding='utf-8-sig').read()

idx1 = content.find('function Pagination(')
if idx1 != -1:
    idx2 = content.find('  );\n}', idx1) + 6
    pagination_str = content[idx1:idx2]
    content = content[:idx1] + content[idx2:]
    
    idx3 = content.find('function StockPage(')
    content = content[:idx3] + pagination_str + '\n' + content[idx3:]
    
    open('src/main.jsx', 'w', encoding='utf-8', newline='\n').write(content)
    print('Fixed Pagination.')
else:
    print('Pagination not found.')

import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove any existing set_page_config
content = re.sub(r'st\.set_page_config\([^)]+\)', '', content, count=1)

# Insert it right after imports
parts = content.split('\n')
for i, line in enumerate(parts):
    if line.startswith('from datetime import datetime'):
        parts.insert(i + 1, '\nst.set_page_config(page_title="PDF Mail Merge Pro", layout="centered", initial_sidebar_state="collapsed")\n')
        break

with open('app.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(parts))

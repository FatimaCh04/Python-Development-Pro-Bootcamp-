import json

def extract_strings(obj):
    strings = []
    if isinstance(obj, str):
        strings.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            strings.extend(extract_strings(v))
    elif isinstance(obj, list):
        for item in obj:
            strings.extend(extract_strings(item))
    return strings

best_content = ''
path = r'C:\Users\premier\.gemini\antigravity\brain\71e3feb6-562c-4d46-ab4d-a06057729623\.system_generated\logs\transcript_full.jsonl'
with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
    for line in fp:
        try:
            data = json.loads(line)
            for s in extract_strings(data):
                if 'function AppRouter' in s and 'import React' in s:
                    if len(s) > len(best_content):
                        best_content = s
        except:
            pass

if best_content:
    print('Found content length:', len(best_content))
    # It might be wrapped in ```jsx
    if '```jsx\n' in best_content:
        best_content = best_content.split('```jsx\n')[1].split('\n```')[0]
        
    with open('src/main.jsx', 'w', encoding='utf-8') as out:
        out.write(best_content)
    print('Restored main.jsx')
else:
    print('Not found')

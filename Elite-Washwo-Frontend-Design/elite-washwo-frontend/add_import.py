import sys

content = open('src/main.jsx', 'r', encoding='utf-8').read()

old = "import Login from './components/Login';\nimport SettingsPage from './components/SettingsPage';"
new = "import Login from './components/Login';\nimport SettingsPage from './components/SettingsPage';\nimport BookingPage from './components/BookingPage';"

if old in content:
    content = content.replace(old, new, 1)
    open('src/main.jsx', 'w', encoding='utf-8').write(content)
    print('Done - import added')
else:
    print('Pattern not found')
    idx = content.find("import Login")
    print(repr(content[idx:idx+200]))

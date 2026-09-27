with open('src/components/SettingsPage.jsx', 'r', encoding='utf-8') as f:
    main = f.read()

with open('src/components/SettingsPage_append.jsx', 'r', encoding='utf-8') as f:
    append = f.read()

# Only append if not already there
if 'function ProfileSection' not in main:
    with open('src/components/SettingsPage.jsx', 'w', encoding='utf-8') as f:
        f.write(main.rstrip() + '\n' + append)
    print('Appended new sections to SettingsPage.jsx')
else:
    print('Already appended')

content = open('src/main.jsx', 'r', encoding='utf-8').read()

idx = content.find('<div className="sidebar-footer">')
end = content.find('</div>', content.find('Sign out', idx)) + len('</div>')
old_footer = content[idx:end+len('\n          </div>')]

print("Found footer block len:", len(old_footer))
print(repr(old_footer[:200]))

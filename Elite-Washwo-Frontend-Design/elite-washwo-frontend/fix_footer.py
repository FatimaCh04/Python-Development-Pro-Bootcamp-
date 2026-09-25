content = open('src/main.jsx', 'r', encoding='utf-8').read()

# Find the full sidebar-footer block
start = content.find('<div className="sidebar-footer">')
# Find the closing </div> that matches - go past Sign out button
sign_out_end = content.find('</button>', content.find('Sign out', start)) + len('</button>')
# Now find the closing </div> of sidebar-footer
footer_end = content.find('\n          </div>', sign_out_end) + len('\n          </div>')

old_footer = content[start:footer_end]
print("Old footer:")
print(repr(old_footer))

new_footer = '''<div className="sidebar-footer">
          <div style={{fontSize:11,color:'#5C6B80',marginBottom:6}}>Signed in as: <span style={{color:'#8CA0AB'}}>{displayName}</span></div>
          <button className="logout-btn" onClick={handleLogout}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            Sign out
          </button>
        </div>'''

content = content[:start] + new_footer + content[footer_end:]
open('src/main.jsx', 'w', encoding='utf-8').write(content)
print('Done - sidebar footer cleaned')

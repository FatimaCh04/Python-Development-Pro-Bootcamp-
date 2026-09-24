content = open("src/main.jsx", "r", encoding="utf-8").read()

old_footer = '''<div className="sidebar-footer">
          Elite Washwo ERP v1.0<br/>Signed in as: {displayName}
          <button className="logout-btn" onClick={handleLogout}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            Sign out
          </button>
        </div>'''

new_footer = '''<div className="sidebar-footer">
          <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:10,padding:'8px 0',borderBottom:'1px solid rgba(255,255,255,.08)'}}>
            <img src="/elitewash-logo.jpg" alt="EliteWash Logo" style={{width:36,height:36,borderRadius:6,objectFit:'cover',flexShrink:0}} />
            <div>
              <div style={{fontSize:12,fontWeight:600,color:'#fff'}}>Elite Washwo</div>
              <div style={{fontSize:10,color:'#5C6B80'}}>ERP v1.0</div>
            </div>
          </div>
          <div style={{fontSize:11,color:'#5C6B80',marginBottom:6}}>Signed in as: <span style={{color:'#8CA0AB'}}>{displayName}</span></div>
          <button className="logout-btn" onClick={handleLogout}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            Sign out
          </button>
        </div>'''

if old_footer in content:
    content = content.replace(old_footer, new_footer)
    open("src/main.jsx", "w", encoding="utf-8").write(content)
    print("Sidebar footer updated with logo")
else:
    # Try flexible match
    import re
    pattern = r'<div className="sidebar-footer">.*?</div>\s*</aside>'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print("Found via regex at:", match.start(), "-", match.end())
        print(repr(match.group()[:200]))
    else:
        print("NOT FOUND - searching manually")
        idx = content.find('sidebar-footer')
        print(repr(content[idx:idx+500]))

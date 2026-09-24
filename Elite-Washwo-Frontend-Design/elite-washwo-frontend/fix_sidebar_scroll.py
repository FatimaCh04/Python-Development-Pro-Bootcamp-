content = open("src/main.jsx", "r", encoding="utf-8").read()

# Find the nav section between brand and sidebar-footer and wrap it
old_nav = '''        {NAV.map(section => (
          <React.Fragment key={section.group}>
            <div className="nav-group-label">{section.group}</div>
            <ul className="nav">
              {section.items.map(item => (
                <li
                  key={item.key}
                  className={`nav-item${activePage === item.key ? ' active' : ''}`}
                  onClick={() => navigate(item.key)}
                >
                  {item.icon}
                  {item.label}
                </li>
              ))}
            </ul>
          </React.Fragment>
        ))}'''

new_nav = '''        <div className="sidebar-nav-scroll">
        {NAV.map(section => (
          <React.Fragment key={section.group}>
            <div className="nav-group-label">{section.group}</div>
            <ul className="nav">
              {section.items.map(item => (
                <li
                  key={item.key}
                  className={`nav-item${activePage === item.key ? ' active' : ''}`}
                  onClick={() => navigate(item.key)}
                >
                  {item.icon}
                  {item.label}
                </li>
              ))}
            </ul>
          </React.Fragment>
        ))}
        </div>'''

if old_nav in content:
    content = content.replace(old_nav, new_nav)
    open("src/main.jsx", "w", encoding="utf-8").write(content)
    print("Nav wrapped in sidebar-nav-scroll OK")
else:
    # Try to find what's actually there
    idx = content.find("NAV.map(section =>")
    print("NAV.map found at:", idx)
    print(repr(content[idx:idx+300]))

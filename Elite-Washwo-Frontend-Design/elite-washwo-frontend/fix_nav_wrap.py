content = open("src/main.jsx", "r", encoding="utf-8").read()

old = """{visibleNav.map(section => (
          <React.Fragment key={section.group}>
            <div className="nav-group-label">{section.group}</div>
            <ul className="nav">
              {section.items.map(item => (
                <li key={item.key} className={`nav-item${activePage===item.key?' active':''}`} onClick={() => navigate(item.key)}>
                  {item.icon}{item.label}
                </li>
              ))}
            </ul>
          </React.Fragment>
        ))}"""

new = """<div className="sidebar-nav-scroll">
        {visibleNav.map(section => (
          <React.Fragment key={section.group}>
            <div className="nav-group-label">{section.group}</div>
            <ul className="nav">
              {section.items.map(item => (
                <li key={item.key} className={`nav-item${activePage===item.key?' active':''}`} onClick={() => navigate(item.key)}>
                  {item.icon}{item.label}
                </li>
              ))}
            </ul>
          </React.Fragment>
        ))}
        </div>"""

if old in content:
    content = content.replace(old, new)
    open("src/main.jsx", "w", encoding="utf-8").write(content)
    print("Wrapped in sidebar-nav-scroll")
else:
    print("Pattern not found exactly")

with open('src/styles.css', 'a', encoding='utf-8') as f:
    f.write("""
/* Dashboard UI Refinement */
.dash-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:28px; flex-wrap:wrap; gap:16px; }
.dash-header h1 { font-size:24px; font-weight:700; color:var(--ink); margin:0 0 4px 0; font-family:'Space Grotesk',sans-serif; }
.dash-header p { font-size:13px; color:var(--text-dim); margin:0; }
.dash-date-control { display:flex; align-items:center; background:#fff; border:1px solid var(--line); border-radius:8px; padding:4px; box-shadow:0 2px 8px rgba(0,0,0,0.02); }
.dash-date-control input[type="date"] { border:none; outline:none; padding:6px 12px; font-family:inherit; font-size:13px; color:var(--ink); font-weight:500; background:transparent; cursor:pointer; }
.dash-date-control .btn-today { background:#FAFBF8; border:1px solid var(--line); border-radius:6px; padding:6px 12px; font-size:12px; font-weight:600; color:var(--text); cursor:pointer; transition:0.2s; margin-left:4px; }
.dash-date-control .btn-today:hover { background:var(--teal); color:#fff; border-color:var(--teal); }

.kpi-card { background:#fff; border:1px solid var(--line); border-radius:12px; padding:20px; box-shadow:0 4px 12px rgba(0,0,0,0.015); transition:transform 0.2s, box-shadow 0.2s; display:flex; flex-direction:column; justify-content:space-between; position:relative; overflow:hidden; }
.kpi-card:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(0,0,0,0.03); }
.kpi-card::before { content:''; position:absolute; top:0; left:0; width:100%; height:3px; background:var(--teal); opacity:0; transition:0.2s; }
.kpi-card:hover::before { opacity:1; }

.kpi-card.accent-teal::before { background:var(--teal); opacity:1; }
.kpi-card.accent-green::before { background:var(--green); opacity:1; }
.kpi-card.accent-amber::before { background:var(--amber); opacity:1; }

.kpi-icon { width:36px; height:36px; border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:16px; }
.kpi-icon.teal { background:rgba(14,124,134,0.08); color:var(--teal); }
.kpi-icon.green { background:rgba(47,158,99,0.08); color:var(--green); }
.kpi-icon.amber { background:rgba(224,147,46,0.08); color:var(--amber); }
.kpi-icon.red { background:rgba(193,72,60,0.08); color:var(--red); }

.kpi-label { font-size:13px; font-weight:600; color:var(--text-dim); margin-bottom:8px; text-transform:uppercase; letter-spacing:0.03em; }
.kpi-value-row { display:flex; align-items:baseline; gap:6px; margin-bottom:6px; }
.kpi-value { font-size:28px; font-weight:700; color:var(--ink); font-family:'Space Grotesk',sans-serif; }
.kpi-unit { font-size:14px; font-weight:600; color:var(--text-dim); }
.kpi-context { font-size:12px; color:var(--text-light); border-top:1px solid var(--line); padding-top:12px; margin-top:auto; }

.dash-section { margin-top:36px; }
.dash-section-header { margin-bottom:16px; }
.dash-section-header h2 { font-size:16px; font-weight:700; color:var(--ink); margin:0 0 4px 0; }
.dash-section-header p { font-size:13px; color:var(--text-dim); margin:0; }
""")
print('Added dashboard styles')

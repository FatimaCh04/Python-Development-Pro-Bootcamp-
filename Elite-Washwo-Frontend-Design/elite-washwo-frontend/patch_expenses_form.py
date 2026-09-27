with open('src/components/ExpensesPage.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    '<form onSubmit={handleSubmit} style={{ display: \'flex\', flexDirection: \'column\', gap: 14 }}>',
    '<form onSubmit={handleSubmit} className="form-grid">'
)

# And wrap the submit button in a container that spans all columns
c = c.replace(
    '<button type="submit" className="btn" disabled={saving}>',
    '<div style={{ gridColumn: \'1/-1\', marginTop: 16 }}><button type="submit" className="btn" disabled={saving}>'
)
c = c.replace(
    '</button>\n          </form>',
    '</button></div>\n          </form>'
)

# And for the distributor notes/notes text area, let's make it span all columns
c = c.replace(
    '<div className="field">\n              <label>Notes</label>',
    '<div className="field" style={{ gridColumn: \'1/-1\' }}>\n              <label>Notes</label>'
)

with open('src/components/ExpensesPage.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated form to use form-grid')

with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

additions = """
export async function fetchGlobalSettings() {
  const { data, error } = await supabase.from('global_settings').select('*').limit(1).single();
  if (error) throw error;
  return data;
}

export async function updateGlobalSettings(fields) {
  const { error } = await supabase.from('global_settings').update(fields).not('id', 'is', null);
  if (error) throw error;
}
"""

if 'export async function fetchGlobalSettings' not in c:
    c = c + additions
    with open('src/lib/db.js', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Added fetchGlobalSettings + updateGlobalSettings')
else:
    print('Already exist, skipping')

import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

bus_lines = [l for l in lines if l.get('type_id') == 'bus']
has_ar = re.compile(r'[\u0600-\u06FF]')

untranslated = {}
for b in bus_lines:
    for d in ['stops_aller', 'stops_retour']:
        for s in b.get(d, []):
            nar = s.get('name_ar', '')
            if not has_ar.search(nar):
                raw = s.get('name', '')
                if raw not in untranslated:
                    untranslated[raw] = {'lines': [], 'lat': s['lat'], 'lon': s['lon'], 'name_fr': s.get('name_fr', '')}
                untranslated[raw]['lines'].append(b.get('short_name'))

print(f"Total untranslated distinct stop names: {len(untranslated)}")
for k, v in sorted(untranslated.items(), key=lambda x: len(x[1]['lines']), reverse=True):
    print(f"'{k}': count={len(v['lines'])}, lines={v['lines'][:5]}, loc=({v['lat']}, {v['lon']})")

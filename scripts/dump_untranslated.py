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
                    untranslated[raw] = s.get('name_fr', raw)

with open('scripts/untranslated_stops.json', 'w', encoding='utf-8') as f:
    json.dump(untranslated, f, ensure_ascii=False, indent=2)

print(f"Dumped {len(untranslated)} untranslated stop names to scripts/untranslated_stops.json")

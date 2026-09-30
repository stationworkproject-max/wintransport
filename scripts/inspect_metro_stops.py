import json, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    lines = json.loads(re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', f.read(), re.DOTALL).group(1))

metros = [l for l in lines if l.get('type_id') == 'metro']
metro_stops = {}
for m in metros:
    for s in m.get('stops', []):
        metro_stops[s['name']] = (s.get('name_fr'), s.get('name_ar'))

for k, v in list(metro_stops.items())[:25]:
    print(f"'{k}' -> FR='{v[0]}' | AR='{v[1]}'")

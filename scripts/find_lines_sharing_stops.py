import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

keywords = ['TAOUFIK', 'CAMPUS', '14 JANVIER', 'SONED', 'FOYER BARDO']

lines_with_stops = {}
for l in lines:
    lid = l['id']
    sn = l.get('short_name', '')
    for d in ['stops_aller', 'stops_retour']:
        for s in l.get(d, []):
            n = s.get('name', '').upper()
            for kw in keywords:
                if kw in n:
                    if lid not in lines_with_stops:
                        lines_with_stops[lid] = {'short_name': sn, 'kws': set(), 'stops': []}
                    lines_with_stops[lid]['kws'].add(kw)
                    lines_with_stops[lid]['stops'].append((d, s.get('name'), (s['lat'], s['lon'])))

print(f"Total lines containing these stops: {len(lines_with_stops)}")
for lid, info in lines_with_stops.items():
    print(f"  {lid} ({info['short_name']}): keywords={list(info['kws'])}")

import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('buses.geojson', 'r', encoding='utf-8') as f:
    d = json.load(f)

keywords = ['taoufik', 'pasteur', 'dark', 'fayette', 'jaures', 'mutuelle', 'zouiten', 'soned', 'bouchoucha', 'bardo', 'campus']

results = []
for f in d['features']:
    p = f.get('properties', {})
    name = ((p.get('name') or '') + ' ' + (p.get('name:fr') or '') + ' ' + (p.get('name:ar') or '')).lower()
    for kw in keywords:
        if kw in name:
            coords = f['geometry']['coordinates']
            results.append((kw, coords[1], coords[0], p.get('name:fr') or p.get('name'), p.get('name:ar') or p.get('name')))
            break

results.sort(key=lambda x: (x[0], x[3] or ''))
for kw, lat, lon, fr, ar in results:
    print(f"[{kw.upper():10s}] [{lat:.5f}, {lon:.5f}] | FR: '{fr}' | AR: '{ar}'")

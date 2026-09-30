import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('buses.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

targets = ['CAMPUS', '14 JANVIER', 'FOYER BARDO', 'TAOUFIK', 'SONED', 'CAFÉ EL HAJ', 'CAFE EL HAJ', 'TOUTA', 'MUTUELLE', 'ZOUITEN', 'DROITS DE L\'HOMME', 'FAYETTE', 'PASTEUR']

found = {}
for f in data['features']:
    props = f.get('properties', {})
    name = props.get('name', '')
    coords = f.get('geometry', {}).get('coordinates', [])
    for t in targets:
        if t in name.upper() or t in (props.get('name:fr') or '').upper():
            if t not in found: found[t] = []
            found[t].append({
                'name': name,
                'name:ar': props.get('name:ar'),
                'coords': coords,
                'props': {k: v for k, v in props.items() if k.startswith('name') or k in ['highway', 'public_transport', 'bus']}
            })

for t, items in found.items():
    print(f"\n=== TARGET: {t} ({len(items)} found) ===")
    for it in items:
        print(f"  {it['name']} | AR: {it['name:ar']} | Coords: {it['coords']}")

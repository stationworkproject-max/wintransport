import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

light_rails = []
for f in data['features']:
    props = f.get('properties', {})
    rw = props.get('railway')
    if rw in ['light_rail', 'tram']:
        light_rails.append(f)

print(f"Total light_rail / tram features: {len(light_rails)}")

# Check their names and operators and refs
props_summary = {}
for f in light_rails:
    p = f.get('properties', {})
    key = (p.get('railway'), p.get('name'), p.get('ref'), p.get('operator'), p.get('line'))
    props_summary[key] = props_summary.get(key, 0) + 1

for k, count in sorted(props_summary.items(), key=lambda x: -x[1]):
    print(f"  count={count:3d} | railway={k[0]} | name={k[1]} | ref={k[2]} | operator={k[3]} | line={k[4]}")

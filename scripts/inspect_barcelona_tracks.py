import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('public/rail_network.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Features in public/rail_network.geojson: {len(data['features'])}")

# Check features around Barcelona Square
# lat: 36.794 to 36.798, lon: 10.178 to 10.183
barcelona_features = []
for f in data['features']:
    props = f.get('properties', {})
    geom = f.get('geometry', {})
    coords = geom.get('coordinates', [])
    t = geom.get('type')
    lines = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in lines:
        for p in line: # lon, lat
            if 36.7945 <= p[1] <= 36.798 and 10.178 <= p[0] <= 10.183:
                barcelona_features.append((f, props, line))
                break
        if len(barcelona_features) and barcelona_features[-1][0] is f:
            break

print(f"Features around Barcelona Square: {len(barcelona_features)}")
for f, props, line in barcelona_features:
    print(f"  id={f.get('id', props.get('@id'))} | railway={props.get('railway')} | name={props.get('name')} | ref={props.get('ref')} | service={props.get('service')} | pts={len(line)}")

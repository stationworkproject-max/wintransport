import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter heavy rail only: railway == 'rail'
heavy_rail_features = []
for f in data['features']:
    props = f.get('properties', {})
    if props.get('railway') == 'rail':
        heavy_rail_features.append(f)

print(f"Total features: {len(data['features'])}")
print(f"Total heavy rail (railway == 'rail'): {len(heavy_rail_features)}")
print(f"Excluded non-heavy-rail: {len(data['features']) - len(heavy_rail_features)}")

# Let's inspect heavy rail tracks around Tunis Ville (36.7948, 10.1803) and Saïda Manoubia (36.7870, 10.1654)
tunis_heavy = []
for f in heavy_rail_features:
    geom = f.get('geometry', {})
    coords = geom.get('coordinates', [])
    t = geom.get('type')
    lines = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in lines:
        for p in line:
            # lon, lat
            if 36.77 <= p[1] <= 36.82 and 10.15 <= p[0] <= 10.19:
                tunis_heavy.append(f)
                break
        if f in tunis_heavy:
            break

print(f"Heavy rail features in Tunis central corridor (36.77-36.82, 10.15-10.19): {len(tunis_heavy)}")
for i, f in enumerate(tunis_heavy[:25]):
    p = f.get('properties', {})
    print(f"  {i:2d}: id={f.get('id', p.get('@id'))} | name={p.get('name')} | operator={p.get('operator')} | usage={p.get('usage')} | service={p.get('service')} | line={p.get('line')}")

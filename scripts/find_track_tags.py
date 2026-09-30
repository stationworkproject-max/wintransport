import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

target = (36.785081, 10.168716)

found = []
for i, feat in enumerate(data['features']):
    geom = feat.get('geometry', {})
    coords = geom.get('coordinates', [])
    t = geom.get('type')
    lines = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in lines:
        for p in line:
            # p is [lon, lat]
            d = ((p[1]-target[0])**2 + (p[0]-target[1])**2)**0.5
            if d < 0.001: # ~100m
                found.append((feat['properties'], p, d))
                break

print(f"Features near {target}: {len(found)}")
for props, p, d in found:
    print(f"  Dist={d*111000:.1f}m | railway={props.get('railway')} | name={props.get('name')} | ref={props.get('ref')} | line={props.get('line')} | operator={props.get('operator')}")

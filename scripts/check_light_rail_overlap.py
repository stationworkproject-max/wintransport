import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    rail_data = json.load(f)

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

# Collect all line segments of light_rail and tram
light_rail_segments = []
for f in rail_data['features']:
    props = f.get('properties', {})
    if props.get('railway') in ['light_rail', 'tram']:
        geom = f.get('geometry', {})
        coords = geom.get('coordinates', [])
        t = geom.get('type')
        lines = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
        for line in lines:
            for p in line:
                light_rail_segments.append((p[1], p[0])) # lat, lon

print(f"Total light_rail points in rail.geojson: {len(light_rail_segments)}")

# Check overlap with train shapes
train_ids = [k for k in shapes if k.startswith('rfr_') or k.startswith('train_')]

for tid in sorted(train_ids):
    if '_' in tid and not tid.endswith('_0') and not tid.endswith('_1'):
        continue # skip variants
    pts = shapes[tid]
    overlap_count = 0
    for p in pts:
        # check distance to any light_rail point
        for lr in light_rail_segments:
            if abs(p[0] - lr[0]) < 0.0001 and abs(p[1] - lr[1]) < 0.0001:
                overlap_count += 1
                break
    if overlap_count > 0:
        print(f"Shape {tid:15s} has {overlap_count:3d} / {len(pts):3d} points overlapping with light_rail/tram!")

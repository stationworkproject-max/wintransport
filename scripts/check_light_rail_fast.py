import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    rail_data = json.load(f)

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

# Grid index for light_rail and tram
GRID = 0.002
grid = {}
for f in rail_data['features']:
    props = f.get('properties', {})
    if props.get('railway') in ['light_rail', 'tram']:
        geom = f.get('geometry', {})
        coords = geom.get('coordinates', [])
        t = geom.get('type')
        lines = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
        for line in lines:
            for p in line:
                lat, lon = p[1], p[0]
                cell = (int(lat / GRID), int(lon / GRID))
                if cell not in grid: grid[cell] = []
                grid[cell].append((lat, lon, props.get('name', props.get('ref', 'unnamed'))))

train_ids = [k for k in shapes if k.startswith('rfr_') or k.startswith('train_')]

for tid in sorted(train_ids):
    if '_' in tid and not tid.endswith('_0') and not tid.endswith('_1'):
        continue
    pts = shapes[tid]
    overlap_pts = []
    for p in pts:
        lat, lon = p[0], p[1]
        cell = (int(lat / GRID), int(lon / GRID))
        matched = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for lr_lat, lr_lon, lr_name in grid.get((cell[0] + dx, cell[1] + dy), []):
                    # within 8 meters (~0.00008 deg)
                    if abs(lat - lr_lat) < 0.00008 and abs(lon - lr_lon) < 0.00008:
                        overlap_pts.append((lat, lon, lr_name))
                        matched = True
                        break
                if matched: break
    if len(overlap_pts) > 0:
        names = set(x[2] for x in overlap_pts)
        print(f"Shape {tid:15s}: {len(overlap_pts):3d} / {len(pts):3d} pts match LIGHT RAIL ({names})")

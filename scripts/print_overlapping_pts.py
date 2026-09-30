import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    rail_data = json.load(f)

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

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
                grid[cell].append((lat, lon, props))

for tid in ['rfr_46', 'rfr_47']:
    pts = shapes[tid]
    print(f"\n=================== {tid} ===================")
    for idx, p in enumerate(pts):
        lat, lon = p[0], p[1]
        cell = (int(lat / GRID), int(lon / GRID))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for lr_lat, lr_lon, lr_props in grid.get((cell[0] + dx, cell[1] + dy), []):
                    if abs(lat - lr_lat) < 0.00008 and abs(lon - lr_lon) < 0.00008:
                        print(f"  pt {idx:3d} ({lat:.6f}, {lon:.6f}) matches light_rail: ref={lr_props.get('ref')}, name={lr_props.get('name')}")
                        break

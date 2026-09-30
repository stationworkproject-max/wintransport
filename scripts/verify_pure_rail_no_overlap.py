import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Import graph and routing from test_pure_rail_routing
import test_pure_rail_routing as pr

with open('rail.geojson', 'r', encoding='utf-8') as f:
    rw = json.load(f)

# Collect light_rail points
GRID = 0.002
grid = {}
for f in rw['features']:
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

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    st_text = f.read()

prefix = 'export const STATIC_LINES = '
idx = st_text.find(prefix)
lines = json.loads(st_text[idx + len(prefix):st_text.rfind(']') + 1])

for lid in ['rfr_46', 'rfr_47']:
    line = [l for l in lines if l['id'] == lid][0]
    stops = line['stops']
    full_path = []
    for i in range(len(stops) - 1):
        s1, s2 = stops[i], stops[i+1]
        n1, d1 = pr.find_nearest_node(s1['lat'], s1['lon'])
        n2, d2 = pr.find_nearest_node(s2['lat'], s2['lon'])
        path, dist = pr.route_track(n1, n2)
        if not full_path:
            full_path.extend(path)
        else:
            full_path.extend(path[1:])
    
    overlaps = []
    for p in full_path:
        lat, lon = p[0], p[1]
        cell = (int(lat / GRID), int(lon / GRID))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for lr_lat, lr_lon, lr_props in grid.get((cell[0] + dx, cell[1] + dy), []):
                    if abs(lat - lr_lat) < 0.00008 and abs(lon - lr_lon) < 0.00008:
                        overlaps.append((p, lr_props.get('name'), lr_props.get('ref')))
    print(f"{lid}: Total path points: {len(full_path)}, Light rail overlaps: {len(overlaps)}")

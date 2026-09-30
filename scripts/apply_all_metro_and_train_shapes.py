import json
import math
import heapq
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

print("=== Step 1: Building light rail & tram graph from rail.geojson ===")
with open('rail.geojson', 'r', encoding='utf-8') as f:
    rw = json.load(f)

adj = {}
def add_edge(u, v, dist):
    if u not in adj: adj[u] = []
    if v not in adj: adj[v] = []
    adj[u].append((v, dist))
    adj[v].append((u, dist))

endpoints = []
for feat in rw['features']:
    props = feat.get('properties', {})
    if props.get('railway') not in ['light_rail', 'tram']:
        continue
    geom = feat.get('geometry')
    if not geom: continue
    coords = geom.get('coordinates', [])
    t = geom.get('type')
    coords_list = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in coords_list:
        if len(line) < 2: continue
        pts = [(round(p[1], 7), round(p[0], 7)) for p in line]
        endpoints.append(pts[0])
        endpoints.append(pts[-1])
        for i in range(len(pts) - 1):
            u, v = pts[i], pts[i+1]
            add_edge(u, v, haversine(u[0], u[1], v[0], v[1]))

GRID_SIZE = 0.005
grid = {}
for node in adj.keys():
    cell = (int(node[0] / GRID_SIZE), int(node[1] / GRID_SIZE))
    if cell not in grid: grid[cell] = []
    grid[cell].append(node)

def find_nearest_node(lat, lon, max_dist=1000):
    gx, gy = int(lat / GRID_SIZE), int(lon / GRID_SIZE)
    best_node, best_dist = None, float('inf')
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            for node in grid.get((gx + dx, gy + dy), []):
                d = haversine(lat, lon, node[0], node[1])
                if d < best_dist:
                    best_dist, best_node = d, node
    if best_dist <= max_dist:
        return best_node, best_dist
    for node in adj.keys():
        d = haversine(lat, lon, node[0], node[1])
        if d < best_dist:
            best_dist, best_node = d, node
    return best_node, best_dist

# Bridge endpoints within light rail (35m threshold)
for ep in endpoints:
    gx, gy = int(ep[0] / GRID_SIZE), int(ep[1] / GRID_SIZE)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for other in grid.get((gx + dx, gy + dy), []):
                if ep != other:
                    d = haversine(ep[0], ep[1], other[0], other[1])
                    if 0 < d <= 35.0:
                        add_edge(ep, other, d)

def route_track(start_node, end_node):
    if start_node == end_node:
        return [start_node], 0.0
    pq = [(0.0, start_node)]
    dist_map = {start_node: 0.0}
    prev = {}
    visited = set()
    while pq:
        cur_d, u = heapq.heappop(pq)
        if u == end_node:
            path = []
            curr = end_node
            while curr is not None:
                path.append(curr)
                curr = prev.get(curr)
            path.reverse()
            return path, cur_d
        if u in visited: continue
        visited.add(u)
        for v, weight in adj.get(u, []):
            if v in visited: continue
            new_d = cur_d + weight
            if new_d < dist_map.get(v, float('inf')):
                dist_map[v] = new_d
                prev[v] = u
                heapq.heappush(pq, (new_d, v))
    return None, float('inf')

print("=== Step 2: Loading staticTransit.js and transitShapes.json ===")
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
idx = text.find(prefix)
networks_part = text[:idx]
lines = json.loads(text[idx + len(prefix):text.rfind(']') + 1])

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

metro_ids = ['metro_50', 'metro_51', 'metro_52', 'metro_53', 'metro_54', 'metro_55', 'metro_56']

print("=== Step 3: Routing and updating Metro & TGM lines ===")
for mid in metro_ids:
    line = [l for l in lines if l['id'] == mid][0]
    stops = line['stops']
    snapped_stops = []
    graph_nodes = []
    for s in stops:
        s_copy = dict(s)
        n, d = find_nearest_node(s['lat'], s['lon'])
        s_copy['lat'] = round(n[0], 6)
        s_copy['lon'] = round(n[1], 6)
        snapped_stops.append(s_copy)
        graph_nodes.append(n)
        
    full_track = []
    total_dist = 0
    for i in range(len(snapped_stops) - 1):
        n1 = graph_nodes[i]
        n2 = graph_nodes[i+1]
        path, dist = route_track(n1, n2)
        assert path is not None, f"Failed leg {snapped_stops[i]['name']} -> {snapped_stops[i+1]['name']} on {mid}"
        total_dist += dist
        if not full_track:
            full_track.extend([[round(p[0], 6), round(p[1], 6)] for p in path])
        else:
            full_track.extend([[round(p[0], 6), round(p[1], 6)] for p in path[1:]])
            
    # Update line object
    line['stops'] = snapped_stops
    line['directions'] = [snapped_stops[-1]['name'], snapped_stops[0]['name']]
    
    rev_track = list(reversed(full_track))
    shapes[mid] = full_track
    shapes[f"{mid}_0"] = full_track
    shapes[f"{mid}_1"] = rev_track
    shapes[f"{mid}_aller"] = full_track
    shapes[f"{mid}_retour"] = rev_track
    
    print(f"Updated {mid} ({line['short_name']}): {len(snapped_stops)} stops | {len(full_track)} pts | {total_dist/1000:.2f}km | {snapped_stops[0]['name']} -> {snapped_stops[-1]['name']}")

# Save transitShapes.json
with open('src/data/transitShapes.json', 'w', encoding='utf-8') as f:
    json.dump(shapes, f, separators=(',', ':'))
print("Saved src/data/transitShapes.json.")

# Save staticTransit.js
new_static_content = networks_part + 'export const STATIC_LINES = ' + json.dumps(lines, indent=2, ensure_ascii=False) + ';\n'
with open('src/data/staticTransit.js', 'w', encoding='utf-8') as f:
    f.write(new_static_content)
print("Saved src/data/staticTransit.js.")

print("\n=== ALL METRO & TGM SHAPES SUCCESSFULLY APPLIED! ===")

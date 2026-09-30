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

with open('rail.geojson', 'r', encoding='utf-8') as f:
    rw = json.load(f)

# Build light rail & tram graph
adj = {}
def add_edge(u, v, dist):
    if u not in adj: adj[u] = []
    if v not in adj: adj[v] = []
    adj[u].append((v, dist))
    adj[v].append((u, dist))

endpoints = []
count = 0
for feat in rw['features']:
    props = feat.get('properties', {})
    if props.get('railway') not in ['light_rail', 'tram']:
        continue
    count += 1
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

print(f"Loaded {count} light_rail/tram features into graph with {len(adj)} nodes.")

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
bridges = 0
for ep in endpoints:
    gx, gy = int(ep[0] / GRID_SIZE), int(ep[1] / GRID_SIZE)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for other in grid.get((gx + dx, gy + dy), []):
                if ep != other:
                    d = haversine(ep[0], ep[1], other[0], other[1])
                    if 0 < d <= 35.0:
                        add_edge(ep, other, d)
                        bridges += 1
print(f"Added {bridges} endpoint bridges within light rail.")

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

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
idx = text.find(prefix)
lines = json.loads(text[idx + len(prefix):text.rfind(']') + 1])

for mid in ['metro_50', 'metro_51', 'metro_52', 'metro_53', 'metro_54', 'metro_55', 'metro_56']:
    line = [l for l in lines if l['id'] == mid][0]
    stops = line['stops']
    full_track = []
    total_dist = 0
    failed = False
    for i in range(len(stops) - 1):
        s1, s2 = stops[i], stops[i+1]
        n1, d1 = find_nearest_node(s1['lat'], s1['lon'])
        n2, d2 = find_nearest_node(s2['lat'], s2['lon'])
        path, dist = route_track(n1, n2)
        if path is None:
            print(f"  FAIL on {mid}: {s1['name']} -> {s2['name']} (snap: {d1:.0f}m, {d2:.0f}m)")
            failed = True
            break
        total_dist += dist
        if not full_track:
            full_track.extend(path)
        else:
            full_track.extend(path[1:])
    if not failed:
        crow = haversine(stops[0]['lat'], stops[0]['lon'], stops[-1]['lat'], stops[-1]['lon'])
        print(f"SUCCESS {mid} ({line['short_name']}): {len(stops)} stops, {len(full_track)} pts, {total_dist/1000:.2f}km [crow: {crow/1000:.2f}km]")

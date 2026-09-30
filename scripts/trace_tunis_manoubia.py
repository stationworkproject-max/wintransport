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

# Track feature id for every edge
adj = {}
edge_features = {}

for feat in rw['features']:
    props = feat.get('properties', {})
    if props.get('railway') != 'rail':
        continue
    fid = feat.get('id', props.get('@id'))
    geom = feat.get('geometry')
    if not geom: continue
    coords = geom.get('coordinates', [])
    t = geom.get('type')
    coords_list = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in coords_list:
        if len(line) < 2: continue
        pts = [(round(p[1], 7), round(p[0], 7)) for p in line]
        for i in range(len(pts) - 1):
            u, v = pts[i], pts[i+1]
            d = haversine(u[0], u[1], v[0], v[1])
            if u not in adj: adj[u] = []
            if v not in adj: adj[v] = []
            adj[u].append((v, d))
            adj[v].append((u, d))
            edge_features[(u, v)] = (fid, props)
            edge_features[(v, u)] = (fid, props)

# Grid index
GRID_SIZE = 0.005
grid = {}
for node in adj.keys():
    cell = (int(node[0] / GRID_SIZE), int(node[1] / GRID_SIZE))
    if cell not in grid: grid[cell] = []
    grid[cell].append(node)

# Bridging
for u in list(adj.keys()):
    gx, gy = int(u[0] / GRID_SIZE), int(u[1] / GRID_SIZE)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for v in grid.get((gx + dx, gy + dy), []):
                if u != v:
                    d = haversine(u[0], u[1], v[0], v[1])
                    if 0 < d <= 25.0: # Tight 25m bridging within heavy rail
                        adj[u].append((v, d))
                        adj[v].append((u, d))

def route(n1, n2):
    pq = [(0.0, n1)]
    dist_map = {n1: 0.0}
    prev = {}
    visited = set()
    while pq:
        cur_d, u = heapq.heappop(pq)
        if u == n2:
            path = []
            curr = n2
            while curr is not None:
                path.append(curr)
                curr = prev.get(curr)
            path.reverse()
            return path, cur_d
        if u in visited: continue
        visited.add(u)
        for v, w in adj.get(u, []):
            if v in visited: continue
            if cur_d + w < dist_map.get(v, float('inf')):
                dist_map[v] = cur_d + w
                prev[v] = u
                heapq.heappush(pq, (cur_d + w, v))
    return None, float('inf')

def find_nearest_node(lat, lon):
    gx, gy = int(lat / GRID_SIZE), int(lon / GRID_SIZE)
    best_node, best_dist = None, float('inf')
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            for node in grid.get((gx + dx, gy + dy), []):
                d = haversine(lat, lon, node[0], node[1])
                if d < best_dist:
                    best_dist, best_node = d, node
    return best_node, best_dist

n_tunis, _ = find_nearest_node(36.794876, 10.180366)
n_manoubia, _ = find_nearest_node(36.787072, 10.165471)

path, d = route(n_tunis, n_manoubia)
print(f"Tunis Ville -> Saïda Manoubia: {d:.0f}m ({len(path)} pts)")

# Check traversed features
features_traversed = []
for i in range(len(path) - 1):
    u, v = path[i], path[i+1]
    info = edge_features.get((u, v))
    if info:
        fid, props = info
        if not features_traversed or features_traversed[-1][0] != fid:
            features_traversed.append((fid, props))
    else:
        if not features_traversed or features_traversed[-1][0] != 'BRIDGE':
            features_traversed.append(('BRIDGE', {}))

print(f"Features traversed ({len(features_traversed)}):")
for fid, props in features_traversed:
    print(f"  {fid:20s} | railway={props.get('railway')} | name={props.get('name')} | operator={props.get('operator')}")

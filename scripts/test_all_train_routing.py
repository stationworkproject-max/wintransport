import json
import csv
import math
import heapq
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# 1. Load railway tracks and build bridged graph
print("Loading railways.geojson...")
with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson', 'r', encoding='utf-8') as f:
    rw = json.load(f)

# Collect all track points
adj = {}
all_nodes = []

def add_edge(u, v, dist):
    if u not in adj: adj[u] = []
    if v not in adj: adj[v] = []
    adj[u].append((v, dist))
    adj[v].append((u, dist))

endpoints = []

for feat in rw['features']:
    geom = feat.get('geometry')
    if not geom: continue
    coords = geom.get('coordinates', [])
    if geom.get('type') == 'LineString':
        coords_list = [coords]
    elif geom.get('type') == 'MultiLineString':
        coords_list = coords
    else:
        continue

    for line in coords_list:
        if len(line) < 2: continue
        pts = [(round(p[1], 7), round(p[0], 7)) for p in line]
        endpoints.append(pts[0])
        endpoints.append(pts[-1])
        for i in range(len(pts) - 1):
            u = pts[i]
            v = pts[i+1]
            d = haversine(u[0], u[1], v[0], v[1])
            add_edge(u, v, d)

# Spatial grid for track nodes
GRID_SIZE = 0.005 # ~500m
grid = {}
for node in adj.keys():
    gx = int(node[0] / GRID_SIZE)
    gy = int(node[1] / GRID_SIZE)
    cell = (gx, gy)
    if cell not in grid: grid[cell] = []
    grid[cell].append(node)

def find_nearest_node(lat, lon, max_dist=10000):
    gx = int(lat / GRID_SIZE)
    gy = int(lon / GRID_SIZE)
    best_node = None
    best_dist = float('inf')
    # search surrounding cells
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            cell = (gx + dx, gy + dy)
            for node in grid.get(cell, []):
                d = haversine(lat, lon, node[0], node[1])
                if d < best_dist:
                    best_dist = d
                    best_node = node
    if best_dist <= max_dist:
        return best_node, best_dist
    # fallback to all nodes if not found
    for node in adj.keys():
        d = haversine(lat, lon, node[0], node[1])
        if d < best_dist:
            best_dist = d
            best_node = node
    return best_node, best_dist

# Bridge track endpoints within 35m
ep_grid = {}
for ep in endpoints:
    gx = int(ep[0] / 0.001)
    gy = int(ep[1] / 0.001)
    cell = (gx, gy)
    if cell not in ep_grid: ep_grid[cell] = []
    ep_grid[cell].append(ep)

bridged_count = 0
for ep in endpoints:
    gx = int(ep[0] / 0.001)
    gy = int(ep[1] / 0.001)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for other in ep_grid.get((gx + dx, gy + dy), []):
                if ep != other:
                    d = haversine(ep[0], ep[1], other[0], other[1])
                    if 0 < d <= 35.0:
                        add_edge(ep, other, d)
                        bridged_count += 1

print(f"Graph ready: {len(adj)} nodes, {bridged_count} bridged gaps.")

# 2. Dijkstra routing
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
        if u in visited:
            continue
        visited.add(u)
        
        for v, weight in adj.get(u, []):
            if v in visited:
                continue
            new_d = cur_d + weight
            if new_d < dist_map.get(v, float('inf')):
                dist_map[v] = new_d
                prev[v] = u
                heapq.heappush(pq, (new_d, v))
                
    return None, float('inf')

# 3. Load static lines
from parse_static_transit import static_lines
train_lines = [l for l in static_lines if l.get('type_id') == 'train' or l['id'].startswith('train_') or l['id'].startswith('rfr_')]

# Load stations.csv for station coordinate correction
csv_stations = []
with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\stations.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for r in reader:
        csv_stations.append({
            'name': r.get('name', ''),
            'name_fr': r.get('name_fr', ''),
            'lat': float(r['lat']),
            'lon': float(r['lon']),
        })

print(f"\nTesting routing for all {len(train_lines)} train lines...")
summary = []

for line in train_lines:
    lid = line['id']
    lname = line.get('long_name', '')
    stops = line.get('stops', [])
    if len(stops) < 2:
        print(f"Skipping {lid} (stops < 2)")
        continue
    
    print(f"\n--- Line {lid}: {lname} ({len(stops)} stops) ---")
    line_pts = []
    failed_legs = []
    total_dist = 0
    
    for i in range(len(stops) - 1):
        s1 = stops[i]
        s2 = stops[i+1]
        
        # Check if station coords need correction or snap
        n1, d1 = find_nearest_node(s1['lat'], s1['lon'])
        n2, d2 = find_nearest_node(s2['lat'], s2['lon'])
        
        direct = haversine(s1['lat'], s1['lon'], s2['lat'], s2['lon'])
        
        path, routed_d = route_track(n1, n2)
        if path is None:
            failed_legs.append((s1['name'], s2['name'], direct, d1, d2))
            print(f"  FAILED: {s1['name']} -> {s2['name']} (direct: {direct:.0f}m, snap1: {d1:.0f}m, snap2: {d2:.0f}m)")
        else:
            total_dist += routed_d
            ratio = routed_d / max(1.0, direct)
            if ratio > 2.5 and routed_d > 20000:
                print(f"  WARNING detour: {s1['name']} -> {s2['name']} (track: {routed_d/1000:.1f}km vs direct: {direct/1000:.1f}km, ratio={ratio:.2f})")
    
    success = (len(failed_legs) == 0)
    summary.append({
        'id': lid,
        'name': lname,
        'stops': len(stops),
        'success': success,
        'failed_count': len(failed_legs),
        'total_km': total_dist / 1000.0
    })

print("\n" + "="*60)
print("ROUTING SUMMARY:")
for s in summary:
    status = "OK" if s['success'] else f"FAILED ({s['failed_count']} legs)"
    print(f"  {s['id']:10s} : {status:15s} | {s['total_km']:6.1f} km | {s['name']}")

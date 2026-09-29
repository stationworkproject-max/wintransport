import json
import math
import heapq
from collections import defaultdict

def dist(p1, p2):
    return 6371000 * math.sqrt(math.radians(p2[0]-p1[0])**2 + (math.radians(p2[1]-p1[1])*math.cos(math.radians(p1[0])))**2)

rw = json.load(open(r"C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson", encoding='utf-8', errors='replace'))
features = rw['features']

graph = defaultdict(dict)
all_nodes = set()
endpoints = []

for f in features:
    coords = f.get('geometry', {}).get('coordinates', [])
    if len(coords) >= 2:
        endpoints.append((round(coords[0][1], 5), round(coords[0][0], 5)))
        endpoints.append((round(coords[-1][1], 5), round(coords[-1][0], 5)))
    for i in range(len(coords) - 1):
        u = (round(coords[i][1], 5), round(coords[i][0], 5))
        v = (round(coords[i+1][1], 5), round(coords[i+1][0], 5))
        if u != v:
            d = dist(u, v)
            if v not in graph[u] or d < graph[u][v]:
                graph[u][v] = d
                graph[v][u] = d
            all_nodes.add(u)
            all_nodes.add(v)

# Spatial grid index for endpoints
grid = defaultdict(list)
for ep in set(endpoints):
    # grid cell ~ 50m (0.0005 deg)
    cell = (int(ep[0] / 0.0005), int(ep[1] / 0.0005))
    grid[cell].append(ep)

bridged_edges = 0
for ep in set(endpoints):
    cell_x = int(ep[0] / 0.0005)
    cell_y = int(ep[1] / 0.0005)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            for other in grid.get((cell_x + dx, cell_y + dy), []):
                if ep != other:
                    d = dist(ep, other)
                    if d < 35: # bridge gap up to 35m
                        if other not in graph[ep] or d < graph[ep][other]:
                            graph[ep][other] = d
                            graph[other][ep] = d
                            bridged_edges += 1

print(f"Graph with bridged junctions: {len(all_nodes)} nodes, bridged {bridged_edges//2} junction gaps!")

def find_nearest_node(pt):
    best_node = None
    min_d = float('inf')
    for n in all_nodes:
        d = dist(pt, n)
        if d < min_d:
            min_d = d
            best_node = n
    return best_node, min_d

def dijkstra_path(start, target):
    dist_map = {start: 0}
    prev = {}
    pq = [(0, start)]
    visited = set()
    while pq:
        cur_d, u = heapq.heappop(pq)
        if u == target:
            path = []
            curr = target
            while curr in prev:
                path.append(curr)
                curr = prev[curr]
            path.append(start)
            path.reverse()
            return path, cur_d
        if u in visited: continue
        visited.add(u)
        for v, weight in graph[u].items():
            if v in visited: continue
            new_d = cur_d + weight
            if new_d < dist_map.get(v, float('inf')):
                dist_map[v] = new_d
                prev[v] = u
                heapq.heappush(pq, (new_d, v))
    return None, float('inf')

with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])

for lid in ['train_45', 'train_28']:
    l = [x for x in lines if x['id'] == lid][0]
    stops = l.get('stops', [])
    print(f"\n--- Testing {lid} ({l['short_name']} - {l['long_name']}) ---")
    full_track = []
    total_dist = 0
    for i in range(len(stops) - 1):
        s1 = (stops[i]['lat'], stops[i]['lon'])
        s2 = (stops[i+1]['lat'], stops[i+1]['lon'])
        n1, d1 = find_nearest_node(s1)
        n2, d2 = find_nearest_node(s2)
        path, leg_dist = dijkstra_path(n1, n2)
        if path:
            print(f"  Leg {stops[i]['name']} -> {stops[i+1]['name']}: OK ({len(path)} pts, {leg_dist:.0f}m)")
            total_dist += leg_dist
        else:
            print(f"  Leg {stops[i]['name']} -> {stops[i+1]['name']}: FAILED")
    print(f"  Total distance: {total_dist:.0f}m")

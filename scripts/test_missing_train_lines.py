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

for f in features:
    coords = f.get('geometry', {}).get('coordinates', [])
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
test_line_ids = ['train_42', 'train_43', 'train_39', 'train_28', 'train_29', 'train_30', 'train_45']

for lid in test_line_ids:
    l = [x for x in lines if x['id'] == lid][0]
    stops = l.get('stops', [])
    print(f"\n--- Testing {lid} ({l['short_name']} - {l['long_name']}) with {len(stops)} stops ---")
    
    full_track = []
    total_dist = 0
    all_legs_ok = True
    
    for i in range(len(stops) - 1):
        s1 = (stops[i]['lat'], stops[i]['lon'])
        s2 = (stops[i+1]['lat'], stops[i+1]['lon'])
        n1, d1 = find_nearest_node(s1)
        n2, d2 = find_nearest_node(s2)
        path, leg_dist = dijkstra_path(n1, n2)
        if path:
            print(f"  Leg {stops[i]['name']} -> {stops[i+1]['name']}: OK ({len(path)} pts, {leg_dist:.0f}m)")
            if full_track:
                full_track.extend(path[1:])
            else:
                full_track.extend(path)
            total_dist += leg_dist
        else:
            print(f"  Leg {stops[i]['name']} -> {stops[i+1]['name']}: NO PATH FOUND (n1 dist: {d1:.0f}m, n2 dist: {d2:.0f}m)")
            all_legs_ok = False
            
    print(f"  Result: {len(full_track)} total points, distance {total_dist:.0f}m, status: {'SUCCESS' if all_legs_ok else 'PARTIAL'}")

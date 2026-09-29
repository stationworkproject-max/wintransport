import json
import math
import heapq
from collections import defaultdict

def dist(p1, p2):
    return 6371000 * math.sqrt(math.radians(p2[0]-p1[0])**2 + (math.radians(p2[1]-p1[1])*math.cos(math.radians(p1[0])))**2)

print("Loading railways.geojson...")
rw = json.load(open(r"C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson", encoding='utf-8', errors='replace'))
features = rw['features']

# Build graph
graph = defaultdict(dict)
all_nodes = set()

for f in features:
    coords = f.get('geometry', {}).get('coordinates', [])
    for i in range(len(coords) - 1):
        # coords are [lon, lat]
        u = (round(coords[i][1], 5), round(coords[i][0], 5))
        v = (round(coords[i+1][1], 5), round(coords[i+1][0], 5))
        if u != v:
            d = dist(u, v)
            if v not in graph[u] or d < graph[u][v]:
                graph[u][v] = d
                graph[v][u] = d
            all_nodes.add(u)
            all_nodes.add(v)

print(f"Railway graph built: {len(all_nodes)} nodes, {sum(len(v) for v in graph.values())//2} edges.")

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
            # Reconstruct path
            path = []
            curr = target
            while curr in prev:
                path.append(curr)
                curr = prev[curr]
            path.append(start)
            path.reverse()
            return path, cur_d
            
        if u in visited:
            continue
        visited.add(u)
        
        for v, weight in graph[u].items():
            if v in visited:
                continue
            new_d = cur_d + weight
            if new_d < dist_map.get(v, float('inf')):
                dist_map[v] = new_d
                prev[v] = u
                heapq.heappush(pq, (new_d, v))
                
    return None, float('inf')

# Test on Line train_31: Metlaoui -> Redeyef
# Stations for train_31 from staticTransit.js:
with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])
t31 = [l for l in lines if l['id'] == 'train_31'][0]
print(f"\nLine {t31['id']}: {t31['long_name']}")
for s in t31['stops']:
    print(f"  Stop: {s['name']} ({s['lat']}, {s['lon']})")

full_track = []
total_track_len = 0

for i in range(len(t31['stops']) - 1):
    s1 = (t31['stops'][i]['lat'], t31['stops'][i]['lon'])
    s2 = (t31['stops'][i+1]['lat'], t31['stops'][i+1]['lon'])
    n1, d1 = find_nearest_node(s1)
    n2, d2 = find_nearest_node(s2)
    path, leg_dist = dijkstra_path(n1, n2)
    if path:
        print(f"Leg {t31['stops'][i]['name']} -> {t31['stops'][i+1]['name']}: found track of {len(path)} points ({leg_dist:.0f}m)")
        if full_track:
            full_track.extend(path[1:])
        else:
            full_track.extend(path)
        total_track_len += leg_dist
    else:
        print(f"ERROR: No track found between {t31['stops'][i]['name']} and {t31['stops'][i+1]['name']}")

print(f"\nTotal Track Generated: {len(full_track)} points, distance: {total_track_len:.0f}m")

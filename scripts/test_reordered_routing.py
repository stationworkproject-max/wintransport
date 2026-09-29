import json
import csv
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

# Load railways
with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson', 'r', encoding='utf-8') as f:
    rw = json.load(f)

adj = {}
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

def find_nearest_node(lat, lon, max_dist=10000):
    gx, gy = int(lat / GRID_SIZE), int(lon / GRID_SIZE)
    best_node, best_dist = None, float('inf')
    for dx in range(-3, 4):
        for dy in range(-3, 4):
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

for ep in endpoints:
    gx, gy = int(ep[0] / GRID_SIZE), int(ep[1] / GRID_SIZE)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for other in grid.get((gx + dx, gy + dy), []):
                if ep != other:
                    d = haversine(ep[0], ep[1], other[0], other[1])
                    if 0 < d <= 35.0:
                        add_edge(ep, other, d)

# Bridge Gargour gap
p_garg1 = (34.6164812, 10.6215235)
p_garg2 = (34.6201839, 10.6275809)
if p_garg1 in adj and p_garg2 in adj:
    add_edge(p_garg1, p_garg2, haversine(p_garg1[0], p_garg1[1], p_garg2[0], p_garg2[1]))

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

from parse_static_transit import static_lines

# Define helper to sort stops along a reference line
# For Ligne 1/5 (Tunis to south): decreasing latitude works perfectly
def reorder_line_stops(line):
    lid = line['id']
    stops = line['stops']
    
    if lid == 'train_18': # Tunis to Sfax
        # insert Turki, Parc Friguia, Sidi Bou Goubrine by latitude
        return sorted(stops, key=lambda s: s['lat'], reverse=True)
    elif lid == 'train_21': # Tunis to Gabes
        # insert Parc Friguia by latitude
        return sorted(stops, key=lambda s: s['lat'], reverse=True)
    elif lid == 'train_23': # Tunis to Sousse Voyageurs
        # Sidi Mtir, Ain Rahma, Parc Friguia by latitude
        # Note: Sousse Voyageurs is at 35.8304, Kalaa Sghira at 35.8220. 
        # Tunis -> Kalaa Kebira -> Kalaa Sghira -> Sousse Voyageurs
        # So we can keep Tunis -> ... -> Sousse Voyageurs, and insert the 3 before Enfida!
        names = [s['name'] for s in stops]
        main_stops = [s for s in stops if s['name'] not in ['Sidi Mtir', 'Ain Rahma', 'Parc Friguia']]
        # insert them in proper place (between Bir Bourekba and Enfida)
        # Bir Bourekba -> Sidi Mtir -> Bouficha -> Ain Rahma -> Parc Friguia -> Enfida
        res = []
        for s in main_stops:
            res.append(s)
            if s['name'] == 'Bir Bourekba':
                res.append([x for x in stops if x['name'] == 'Sidi Mtir'][0])
            elif s['name'] == 'Bouficha':
                res.append([x for x in stops if x['name'] == 'Ain Rahma'][0])
                res.append([x for x in stops if x['name'] == 'Parc Friguia'][0])
        return res
    elif lid == 'train_24': # Tunis to Tozeur
        # Borj Cedria (after Hammam Lif), Sidi Bou Goubrine (after MSaken), Sakiet Ezzit (after Sidi Salah)
        main_stops = [s for s in stops if s['name'] not in ['Borj Cedria', 'Sidi Bou Goubrine', 'Sakiet Ezzit']]
        res = []
        for s in main_stops:
            res.append(s)
            if s['name'] == 'Hammam Lif':
                res.append([x for x in stops if x['name'] == 'Borj Cedria'][0])
            elif s['name'] == 'MSaken':
                res.append([x for x in stops if x['name'] == 'Sidi Bou Goubrine'][0])
            elif s['name'] == 'Sidi Salah':
                res.append([x for x in stops if x['name'] == 'Sakiet Ezzit'][0])
        return res
    elif lid in ('train_5', 'train_20'):
        # Western line Tunis -> Gaafour -> Dahmani -> Kalaa Khasba
        # Let's inspect sequence:
        # Tunis -> Djebal Jelloud -> Bir Kassa -> Nassen -> Khledia -> Oudna -> Cheylus -> Bir MCherga -> Depienne
        # -> El Ouja -> Pont Du Fahs -> Thibica -> Tarf Echena -> Bou Arada -> Jelida -> El Aroussa -> Sidi Ayed -> Gaafour -> El Akhouat -> Le Krib -> Sidi Bou Rouis -> Trika -> Le Sers -> Oued Tessa -> Les Salines -> Les Zouarines -> Dahmani -> Ain Mesria -> Fej Etameur -> Gouraia -> Oued Sarrath -> Kalaa Khasba
        ref_order = [
            'Tunis Ville', 'Djebal Jelloud', 'Bir Kassa', 'Nassen', 'Khledia', 'Oudna', 'Cheylus',
            'Bir MCherga', 'Depienne', 'El Ouja', 'Pont Du Fahs', 'Thibica', 'Tarf Echena',
            'Bou Arada', 'Jelida', 'El Aroussa', 'Sidi Ayed', 'Gaafour', 'El Akhouat', 'Le Krib',
            'Sidi Bou Rouis', 'Trika', 'Le Sers', 'Oued Tessa', 'Les Salines', 'Les Zouarines',
            'Dahmani', 'Ain Mesria', 'Fej Etameur', 'Gouraia', 'Oued Sarrath', 'Kalaa Khasba'
        ]
        stop_dict = {s['name']: s for s in stops}
        res = [stop_dict[name] for name in ref_order if name in stop_dict]
        # Any remaining stops
        for s in stops:
            if s not in res:
                res.append(s)
        return res
    else:
        return stops

train_lines = [l for l in static_lines if l.get('type_id') == 'train' or l['id'].startswith('train_') or l['id'].startswith('rfr_')]

print("Testing routing with corrected stop order:")
for line in train_lines:
    lid = line['id']
    lname = line.get('long_name', '')
    stops = reorder_line_stops(line)
    
    total_dist = 0
    total_pts = 0
    failed = False
    
    for i in range(len(stops) - 1):
        s1, s2 = stops[i], stops[i+1]
        n1, d1 = find_nearest_node(s1['lat'], s1['lon'])
        n2, d2 = find_nearest_node(s2['lat'], s2['lon'])
        path, leg_dist = route_track(n1, n2)
        if path is None:
            failed = True
            break
        total_dist += leg_dist
        total_pts += len(path)
        
    status = "OK" if not failed else "FAILED"
    first_name = stops[0]['name']
    last_name = stops[-1]['name']
    print(f"  {lid:10s} : {status:6s} | {len(stops):2d} stops | {total_dist/1000:6.1f} km | {total_pts:5d} pts | {first_name} -> {last_name}")

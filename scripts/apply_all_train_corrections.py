import json
import math
import heapq
import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Step 1: Backup files
print("--- Step 1: Backing up staticTransit.js and transitShapes.json ---")
shutil.copyfile('src/data/staticTransit.js', 'src/data/staticTransit.js.bak')
shutil.copyfile('src/data/transitShapes.json', 'src/data/transitShapes.json.bak')
print("Backups created.")

# Step 2: Build Bridged Railway Graph
print("\n--- Step 2: Building bridged railway graph ---")
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

# Bridge endpoints to any node within 35m
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

print(f"Graph initialized with {len(adj)} nodes.")

# Dijkstra routing
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

# Step 3: Reorder Stops
def reorder_line_stops(line):
    lid = line['id']
    stops = line['stops']
    
    if lid == 'train_18': # Tunis to Sfax
        return sorted(stops, key=lambda s: s['lat'], reverse=True)
    elif lid == 'train_21': # Tunis to Gabes
        return sorted(stops, key=lambda s: s['lat'], reverse=True)
    elif lid == 'train_23': # Tunis to Sousse Voyageurs
        main_stops = [s for s in stops if s['name'] not in ['Sidi Mtir', 'Ain Rahma', 'Parc Friguia']]
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
    elif lid == 'train_17': # Tunis to Nabeul Voyageurs
        main_stops = [s for s in stops if s['name'] not in ['Megrine Ryad', 'Bir El Bey']]
        res = []
        for s in main_stops:
            res.append(s)
            if s['name'] == 'Djebal Jelloud':
                res.append([x for x in stops if x['name'] == 'Megrine Ryad'][0])
            elif s['name'] == 'Hammam Lif':
                res.append([x for x in stops if x['name'] == 'Bir El Bey'][0])
        return res
    elif lid == 'rfr_19': # Tunis to Erriadh
        main_stops = [s for s in stops if s['name'] != 'Lycee Technique Rades']
        res = []
        for s in main_stops:
            res.append(s)
            if s['name'] == 'Sidi Rezig':
                res.append([x for x in stops if x['name'] == 'Lycee Technique Rades'][0])
        return res
    elif lid in ('train_5', 'train_20'):
        ref_order = [
            'Tunis Ville', 'Djebal Jelloud', 'Bir Kassa', 'Nassen', 'Khledia', 'Oudna', 'Cheylus',
            'Bir MCherga', 'Depienne', 'El Ouja', 'Pont Du Fahs', 'Thibica', 'Tarf Echena',
            'Bou Arada', 'Jelida', 'El Aroussa', 'Sidi Ayed', 'Gaafour', 'El Akhouat', 'Le Krib',
            'Sidi Bou Rouis', 'Trika', 'Le Sers', 'Oued Tessa', 'Les Salines', 'Les Zouarines',
            'Dahmani', 'Ain Mesria', 'Fej Etameur', 'Gouraia', 'Oued Sarrath', 'Kalaa Khasba'
        ]
        stop_dict = {s['name']: s for s in stops}
        res = [stop_dict[name] for name in ref_order if name in stop_dict]
        for s in stops:
            if s not in res:
                res.append(s)
        return res
    else:
        return stops

# Step 4: Load staticTransit.js
print("\n--- Step 3: Loading staticTransit.js ---")
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    st_content = f.read()

prefix = 'export const STATIC_LINES = '
prefix_idx = st_content.find(prefix)
networks_part = st_content[:prefix_idx]
lines_json_str = st_content[prefix_idx + len(prefix):].strip()
if lines_json_str.endswith(';'):
    lines_json_str = lines_json_str[:-1].strip()

all_lines = json.loads(lines_json_str)
print(f"Loaded {len(all_lines)} lines from staticTransit.js.")

# Load existing shapes
with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    transit_shapes = json.load(f)
print(f"Loaded {len(transit_shapes)} existing shape keys.")

# Step 5: Process all train and RFR lines
print("\n--- Step 4: Routing and Updating Shapes ---")
train_ids = set()
updated_count = 0

for line in all_lines:
    lid = line['id']
    is_train = (line.get('type_id') == 'train' or lid.startswith('train_') or lid.startswith('rfr_'))
    if not is_train:
        continue
    train_ids.add(lid)
    
    ordered_stops = reorder_line_stops(line)
    
    snapped_stops = []
    graph_nodes = []
    for s in ordered_stops:
        s_copy = dict(s)
        n, d = find_nearest_node(s['lat'], s['lon'])
        s_copy['lat'] = round(n[0], 6)
        s_copy['lon'] = round(n[1], 6)
        snapped_stops.append(s_copy)
        graph_nodes.append(n)
        
    full_track = []
    total_dist = 0
    failed = False
    
    for i in range(len(snapped_stops) - 1):
        n1 = graph_nodes[i]
        n2 = graph_nodes[i+1]
        path, leg_dist = route_track(n1, n2)
        if path is None:
            print(f"ERROR: Failed leg {snapped_stops[i]['name']} -> {snapped_stops[i+1]['name']} on line {lid}")
            failed = True
            break
        total_dist += leg_dist
        if not full_track:
            full_track.extend([[round(p[0], 6), round(p[1], 6)] for p in path])
        else:
            full_track.extend([[round(p[0], 6), round(p[1], 6)] for p in path[1:]])
            
    if failed:
        print(f"CRITICAL: Failed to route {lid}!")
        continue
        
    # Update line object
    line['stops'] = snapped_stops
    # Terminus is last stop, departure is first stop
    line['directions'] = [snapped_stops[-1]['name'], snapped_stops[0]['name']]
    
    # Update shapes
    rev_track = list(reversed(full_track))
    transit_shapes[lid] = full_track
    transit_shapes[f"{lid}_0"] = full_track
    transit_shapes[f"{lid}_1"] = rev_track
    transit_shapes[f"{lid}_aller"] = full_track
    transit_shapes[f"{lid}_retour"] = rev_track
    
    updated_count += 1
    print(f"  {lid:10s} : OK | {len(snapped_stops):2d} stops | {total_dist/1000:6.1f} km | {len(full_track):5d} shape pts | {snapped_stops[0]['name']} -> {snapped_stops[-1]['name']}")

print(f"\nUpdated {updated_count} / {len(train_ids)} train lines.")

# Step 6: Save updated transitShapes.json
print("\n--- Step 5: Writing updated transitShapes.json ---")
with open('src/data/transitShapes.json', 'w', encoding='utf-8') as f:
    json.dump(transit_shapes, f, separators=(',', ':'))
print(f"Saved transitShapes.json with {len(transit_shapes)} keys.")

# Step 7: Save updated staticTransit.js
print("\n--- Step 6: Writing updated staticTransit.js ---")
new_static_content = networks_part + 'export const STATIC_LINES = ' + json.dumps(all_lines, indent=2, ensure_ascii=False) + ';\n'
with open('src/data/staticTransit.js', 'w', encoding='utf-8') as f:
    f.write(new_static_content)
print("Saved staticTransit.js.")

print("\n--- ALL CORRECTIONS APPLIED SUCCESSFULLY! ---")

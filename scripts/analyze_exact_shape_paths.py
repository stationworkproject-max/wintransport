import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r') as f:
    shapes = json.load(f)

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])

for bid, label in [('bus_846', '36B'), ('bus_847', '38B')]:
    l = [x for x in lines if x['id'] == bid][0]
    for dir_idx, dir_name in [(0, 'Aller'), (1, 'Retour')]:
        key = f"{bid}_{dir_idx}"
        pts = shapes[key]
        stops = l.get('stops_aller' if dir_idx == 0 else 'stops_retour', l['stops'])
        print(f"\n==================== {label} {dir_name} ({key}) ====================")
        print(f"Stops count: {len(stops)}, Shape points: {len(pts)}")
        # Check legs between stops
        # For each stop, find its closest point index in shape
        stop_indices = []
        for s in stops:
            min_d = float('inf')
            best_idx = 0
            for i, p in enumerate(pts):
                d = (s['lat'] - p[0])**2 + (s['lon'] - p[1])**2
                if d < min_d:
                    min_d = d
                    best_idx = i
            stop_indices.append(best_idx)
            
        print("Stop sequence on shape:")
        for idx in range(len(stops)):
            s = stops[idx]
            pt_idx = stop_indices[idx]
            print(f"  [{idx+1:2d}] pt #{pt_idx:3d} : {s['name'][:30]:30s} ({s['lat']:.5f}, {s['lon']:.5f})")
            if idx > 0:
                prev_pt_idx = stop_indices[idx-1]
                if pt_idx < prev_pt_idx:
                    print(f"      *** BACKTRACK DETECTED! pt #{pt_idx} < pt #{prev_pt_idx} ***")

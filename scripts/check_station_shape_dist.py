import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(p1, p2):
    R = 6371000
    phi1, phi2 = math.radians(p1[0]), math.radians(p2[0])
    dphi = math.radians(p2[0] - p1[0])
    dlambda = math.radians(p2[1] - p1[1])
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
lines_json = text[text.find(prefix) + len(prefix):].strip()
if lines_json.endswith(';'): lines_json = lines_json[:-1].strip()
lines = json.loads(lines_json)

with open('src/data/transitShapes.json', 'r') as f:
    shapes = json.load(f)

for bid, label in [('bus_846', '36B'), ('bus_847', '38B')]:
    l = [x for x in lines if x['id'] == bid][0]
    for dir_idx, dir_name, dir_key in [(0, 'Aller', f'{bid}_0'), (1, 'Retour', f'{bid}_1')]:
        stops = l.get('stops_aller', l.get('stops', [])) if dir_idx == 0 else l.get('stops_retour', [])
        shape_pts = shapes.get(dir_key, [])
        print(f"\n==================== {label} {dir_name} ({dir_key}): {len(stops)} stops, {len(shape_pts)} shape pts ====================")
        
        for idx, s in enumerate(stops):
            s_lat, s_lon = s['lat'], s['lon']
            # min dist to shape
            min_d = float('inf')
            nearest_idx = -1
            for p_idx, p in enumerate(shape_pts):
                d = haversine((s_lat, s_lon), p)
                if d < min_d:
                    min_d = d
                    nearest_idx = p_idx
            warn = " *** FAR FROM SHAPE ***" if min_d > 50 else ""
            print(f"  [{idx+1:2d}] {s['name'][:30]:30s} -> dist to shape: {min_d:5.1f}m (at shape pt #{nearest_idx}){warn}")

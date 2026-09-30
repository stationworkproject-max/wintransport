import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
idx = text.find(prefix)
lines = json.loads(text[idx + len(prefix):text.rfind(']') + 1])

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

rail_lines = [l for l in lines if l.get('type_id') in ['rfr', 'metro', 'tgm', 'train']]

print(f"Total rail lines to check: {len(rail_lines)}\n")

for line in rail_lines:
    lid = line['id']
    stops = line.get('stops', [])
    shape = shapes.get(lid, [])
    
    if len(shape) == 0:
        print(f"ERROR: {lid} ({line.get('short_name')}) has NO shape in transitShapes.json!")
        continue
        
    start_stop = stops[0] if len(stops) else None
    end_stop = stops[-1] if len(stops) else None
    
    start_dist = haversine(start_stop['lat'], start_stop['lon'], shape[0][0], shape[0][1]) if start_stop else 0
    end_dist = haversine(end_stop['lat'], end_stop['lon'], shape[-1][0], shape[-1][1]) if end_stop else 0
    
    # Calculate shape length
    shape_len = 0
    for i in range(len(shape) - 1):
        shape_len += haversine(shape[i][0], shape[i][1], shape[i+1][0], shape[i+1][1])
        
    # Check max distance between any stop and nearest point on shape
    max_stop_gap = 0
    worst_stop = None
    for s in stops:
        min_d = min(haversine(s['lat'], s['lon'], p[0], p[1]) for p in shape)
        if min_d > max_stop_gap:
            max_stop_gap = min_d
            worst_stop = s['name']
            
    status = "OK" if max_stop_gap < 50 else f"GAP {max_stop_gap:.0f}m ({worst_stop})"
    print(f"{lid:12s} | {line.get('type_id'):5s} | {line.get('short_name'):5s} | {len(stops):2d} stops | {len(shape):4d} pts | {shape_len/1000:6.1f}km | start_gap={start_dist:.0f}m, end_gap={end_dist:.0f}m | {status}")

import json
import math
import sys

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def min_dist_to_shape(stop_lat, stop_lon, shape):
    if not shape: return float('inf')
    return min(haversine(stop_lat, stop_lon, p[0], p[1]) for p in shape)

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

with open('public/studio_data.js', 'r', encoding='utf-8') as f:
    raw = f.read().strip()

idx = raw.find('{')
last_idx = raw.rfind('}')
raw = raw[idx : last_idx + 1]
studio_data = json.loads(raw)

print(f"Total lines in studio_data: {len(studio_data.get('lines', []))}")

bus_lines = [l for l in studio_data.get('lines', []) if l.get('type_id') == 'bus']
print(f"Total bus lines: {len(bus_lines)}")

worst_mismatches = []
for line in bus_lines:
    lid = line['id']
    stops = line.get('stops', [])
    shape = shapes.get(lid, []) or shapes.get(f"{lid}_0", [])
    if not shape or not stops:
        continue
    
    # Check distances of all stops to shape
    dists = [min_dist_to_shape(s['lat'], s['lon'], shape) for s in stops]
    max_d = max(dists)
    avg_d = sum(dists) / len(dists)
    
    stop_lats = [s['lat'] for s in stops]
    stop_lons = [s['lon'] for s in stops]
    shape_lats = [p[0] for p in shape]
    shape_lons = [p[1] for p in shape]
    
    center_stop = (sum(stop_lats)/len(stop_lats), sum(stop_lons)/len(stop_lons))
    center_shape = (sum(shape_lats)/len(shape_lats), sum(shape_lons)/len(shape_lons))
    center_dist = haversine(center_stop[0], center_stop[1], center_shape[0], center_shape[1])
    
    worst_mismatches.append((line['short_name'], lid, line.get('long_name', ''), max_d, avg_d, center_dist, len(stops), len(shape)))

worst_mismatches.sort(key=lambda x: x[5], reverse=True)
print("\n--- Top 30 Bus Lines with Largest Center Separation between Stops & Shape ---")
for item in worst_mismatches[:30]:
    print(f"Bus {item[0]} ({item[1]}): Center offset = {item[5]:.0f}m ({item[5]/1000:.1f}km) | Max stop dist = {item[3]:.0f}m | Avg dist = {item[4]:.0f}m | Stops={item[6]}, ShapePts={item[7]}")

import json
import math
from collections import defaultdict

def get_distance(p1, p2):
    R = 6371000
    dLat = math.radians(p2[0] - p1[0])
    dLon = math.radians(p2[1] - p1[1])
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(p1[0])) * math.cos(math.radians(p2[0])) * math.sin(dLon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
feat = data['features']
line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]
num_key = [k for k in feat[0]['properties'] if 'station' in k.lower() and 'nom' not in k.lower()][0]
name_key = [k for k in feat[0]['properties'] if 'nom' in k.lower()][0]

lines = defaultdict(list)
for f in feat:
    p = f['properties']
    raw_l = str(p[line_key]).strip()
    geom = f['geometry']
    coords = (geom['coordinates'][1], geom['coordinates'][0]) if geom else (p.get('Latitude'), p.get('Longitude'))
    lines[raw_l].append({
        'num': p[num_key],
        'name': p[name_key],
        'lat': coords[0],
        'lon': coords[1]
    })

print(f"Total lines in GeoJSON: {len(lines)}")

outlier_lines = []
for l_name, stops in lines.items():
    stops.sort(key=lambda s: s['num'] if s['num'] is not None else 0)
    if len(stops) < 3:
        continue
    
    anomalies = []
    for i in range(1, len(stops) - 1):
        prev_s = stops[i-1]
        curr_s = stops[i]
        next_s = stops[i+1]
        
        d_prev_curr = get_distance((prev_s['lat'], prev_s['lon']), (curr_s['lat'], curr_s['lon']))
        d_curr_next = get_distance((curr_s['lat'], curr_s['lon']), (next_s['lat'], next_s['lon']))
        d_prev_next = get_distance((prev_s['lat'], prev_s['lon']), (next_s['lat'], next_s['lon']))
        
        # Outlier: curr is > 2km from both prev and next, but prev and next are close (< 1.5km)
        if d_prev_curr > 2000 and d_curr_next > 2000 and d_prev_next < 1500:
            anomalies.append({
                'idx': i + 1,
                'stop': curr_s['name'],
                'd_prev': round(d_prev_curr),
                'd_next': round(d_curr_next),
                'd_direct': round(d_prev_next)
            })
            
    if anomalies:
        outlier_lines.append((l_name, len(stops), anomalies))

print(f"Lines with outlier jumps (>2km detour while direct <1.5km): {len(outlier_lines)}")
for l_name, count, anoms in outlier_lines:
    print(f"\nLine {l_name} ({count} stops):")
    for a in anoms:
        print(f"  Stop {a['idx']}: {a['stop']} (jump {a['d_prev']}m, direct {a['d_direct']}m)")

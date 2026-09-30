import json
import re
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. Load buses.geojson
with open('buses.geojson', 'r', encoding='utf-8') as f:
    buses_geo = json.load(f)

geo_points = []
for f in buses_geo['features']:
    coords = f.get('geometry', {}).get('coordinates', [])
    if len(coords) >= 2:
        geo_points.append({
            'lon': coords[0],
            'lat': coords[1],
            'props': f.get('properties', {})
        })

print(f"Total features in buses.geojson: {len(geo_points)}")

# 2. Load staticTransit.js
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))
bus_lines = [l for l in lines if l.get('type_id') == 'bus']

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Unique stops by rounded coords (lat, lon)
unique_stops = {}
for bl in bus_lines:
    for g in ['stops_aller', 'stops_retour']:
        for s in bl.get(g, []):
            key = (round(s['lat'], 5), round(s['lon'], 5))
            if key not in unique_stops:
                unique_stops[key] = {
                    'name': s.get('name', ''),
                    'lat': s['lat'],
                    'lon': s['lon'],
                    'count': 0
                }
            unique_stops[key]['count'] += 1

print(f"Unique stop positions in staticTransit: {len(unique_stops)}")

dists = []
matched_30 = 0
matched_50 = 0
matched_100 = 0
matched_200 = 0

sample_matches = []
unmatched = []

for key, s in unique_stops.items():
    best_d = float('inf')
    best_p = None
    for gp in geo_points:
        d = haversine(s['lat'], s['lon'], gp['lat'], gp['lon'])
        if d < best_d:
            best_d = d
            best_p = gp
    dists.append(best_d)
    if best_d <= 30:
        matched_30 += 1
    if best_d <= 50:
        matched_50 += 1
    if best_d <= 100:
        matched_100 += 1
    if best_d <= 200:
        matched_200 += 1

    if best_d <= 50:
        sample_matches.append((s, best_p, best_d))
    else:
        unmatched.append((s, best_p, best_d))

total = len(unique_stops)
print(f"Within 30m:  {matched_30} / {total} ({matched_30/total*100:.1f}%)")
print(f"Within 50m:  {matched_50} / {total} ({matched_50/total*100:.1f}%)")
print(f"Within 100m: {matched_100} / {total} ({matched_100/total*100:.1f}%)")
print(f"Within 200m: {matched_200} / {total} ({matched_200/total*100:.1f}%)")

print("\n--- SAMPLE MATCHES (<= 50m) ---")
for s, bg, d in sample_matches[:10]:
    p = bg['props']
    print(f"Static: '{s['name']}' ({s['lat']:.5f}, {s['lon']:.5f})")
    print(f"  GeoJSON ({d:.1f}m): name='{p.get('name')}', ar='{p.get('name:ar')}', fr='{p.get('name:fr')}'")

print("\n--- SAMPLE UNMATCHED (> 50m) ---")
for s, bg, d in unmatched[:10]:
    p = bg['props']
    print(f"Static: '{s['name']}' ({s['lat']:.5f}, {s['lon']:.5f}) -> closest {d:.1f}m: name='{p.get('name')}', ar='{p.get('name:ar')}', fr='{p.get('name:fr')}'")

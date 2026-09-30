import json
import re
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load buses.geojson
with open('buses.geojson', 'r', encoding='utf-8') as f:
    buses_geo = json.load(f)

print(f"buses.geojson features: {len(buses_geo['features'])}")

# Extract sample properties from buses.geojson
sample_features = buses_geo['features'][:5]
for idx, f in enumerate(sample_features):
    print(f"Feature {idx}: {f['properties']}")

# Extract all stops from staticTransit.js
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
if not m:
    print("Could not parse STATIC_LINES")
    exit(1)

lines = json.loads(m.group(1))
bus_lines = [l for l in lines if l.get('type_id') == 'bus']
print(f"Total bus lines in staticTransit: {len(bus_lines)}")

# Collect all unique bus stops in staticTransit
static_stops = {}
for line in bus_lines:
    line_id = line['id']
    short_name = line.get('short_name', '')
    for stop_group in ['stops', 'stops_aller', 'stops_retour']:
        for s in line.get(stop_group, []):
            sid = s.get('id') or s.get('stop_id')
            if sid not in static_stops:
                static_stops[sid] = {
                    'name': s.get('name'),
                    'lat': s.get('lat'),
                    'lon': s.get('lon'),
                    'lines': set()
                }
            static_stops[sid]['lines'].add(short_name)

print(f"Total unique bus stops in staticTransit: {len(static_stops)}")

# Function to calculate distance in meters
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000 # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Spatial match between static_stops and buses.geojson
matched_within_30m = 0
matched_within_50m = 0
matched_within_100m = 0
matched_within_200m = 0

geo_points = []
for f in buses_geo['features']:
    coords = f.get('geometry', {}).get('coordinates', [])
    if len(coords) >= 2:
        geo_points.append({
            'lon': coords[0],
            'lat': coords[1],
            'props': f.get('properties', {})
        })

print(f"Valid geo points in buses.geojson: {len(geo_points)}")

matches = []
for sid, s in static_stops.items():
    s_lat, s_lon = s['lat'], s['lon']
    best_dist = float('inf')
    best_geo = None
    for gp in geo_points:
        d = haversine(s_lat, s_lon, gp['lat'], gp['lon'])
        if d < best_dist:
            best_dist = d
            best_geo = gp
    if best_dist <= 30:
        matched_within_30m += 1
    if best_dist <= 50:
        matched_within_50m += 1
    if best_dist <= 100:
        matched_within_100m += 1
    if best_dist <= 200:
        matched_within_200m += 1
    if best_dist <= 100:
        matches.append((s, best_geo, best_dist))

print(f"Matched within 30m: {matched_within_30m} / {len(static_stops)} ({matched_within_30m/len(static_stops)*100:.1f}%)")
print(f"Matched within 50m: {matched_within_50m} / {len(static_stops)} ({matched_within_50m/len(static_stops)*100:.1f}%)")
print(f"Matched within 100m: {matched_within_100m} / {len(static_stops)} ({matched_within_100m/len(static_stops)*100:.1f}%)")
print(f"Matched within 200m: {matched_within_200m} / {len(static_stops)} ({matched_within_200m/len(static_stops)*100:.1f}%)")

print("\nSample 15 matches (within 100m):")
for s, bg, dist in matches[:15]:
    p = bg['props']
    print(f"Static: '{s['name']}' -> GeoJSON ({dist:.1f}m): name='{p.get('name')}', ar='{p.get('name:ar')}', fr='{p.get('name:fr')}'")

import csv
import math
import sys
from parse_static_transit import static_lines

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Load test_enhanced_routing's find_nearest_node
from test_enhanced_routing import find_nearest_node

# Load CSV stations
csv_stations = []
with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\stations.csv', 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        csv_stations.append({
            'name': row.get('name', ''),
            'name_fr': row.get('name_fr', ''),
            'lat': float(row['lat']),
            'lon': float(row['lon']),
        })

train_lines = [l for l in static_lines if l.get('type_id') == 'train' or l['id'].startswith('train_') or l['id'].startswith('rfr_')]

# Collect unique stops
stops_by_name = {}
for l in train_lines:
    for s in l.get('stops', []):
        name = s['name']
        if name not in stops_by_name:
            stops_by_name[name] = s

print(f"Total unique stops in train/rfr lines: {len(stops_by_name)}")

far_from_track = []
for name, s in stops_by_name.items():
    slat, slon = s['lat'], s['lon']
    node, d_track = find_nearest_node(slat, slon)
    if d_track > 50: # More than 50m from physical track
        # Find nearest in CSV
        nearest_csv = min(csv_stations, key=lambda cs: haversine(slat, slon, cs['lat'], cs['lon']))
        d_csv = haversine(slat, slon, nearest_csv['lat'], nearest_csv['lon'])
        _, csv_track_d = find_nearest_node(nearest_csv['lat'], nearest_csv['lon'])
        far_from_track.append((name, slat, slon, d_track, nearest_csv['name_fr'] or nearest_csv['name'], d_csv, csv_track_d, nearest_csv['lat'], nearest_csv['lon']))

far_from_track.sort(key=lambda x: x[3], reverse=True)
print(f"Stops more than 50m from track: {len(far_from_track)}")
for f in far_from_track:
    print(f"  '{f[0]}': d_track={f[3]:.1f}m | Nearest CSV '{f[4]}' ({f[5]:.1f}m away, csv_to_track={f[6]:.1f}m)")

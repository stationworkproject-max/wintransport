import csv
import math
from parse_static_transit import static_lines

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def normalize(name):
    if not name:
        return ""
    import unicodedata
    n = unicodedata.normalize('NFD', name)
    n = ''.join(c for c in n if unicodedata.category(c) != 'Mn')
    n = n.lower().replace('-', ' ').replace("'", ' ').replace('_', ' ')
    n = ' '.join(n.split())
    # remove common words like station, gare, voy, voyageurs
    n = n.replace('voyageurs', '').replace('voy', '').replace('gare', '').replace('station', '')
    return ' '.join(n.split())

# Load stations.csv
csv_stations = []
with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\stations.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_stations.append({
            'name': row.get('name', ''),
            'name_fr': row.get('name_fr', ''),
            'lat': float(row['lat']),
            'lon': float(row['lon']),
            'norm_name': normalize(row.get('name', '')),
            'norm_name_fr': normalize(row.get('name_fr', ''))
        })

print(f"Loaded {len(csv_stations)} stations from CSV.")

# Get all unique train stops from staticTransit.js
train_lines = [l for l in static_lines if l.get('type_id') == 'train' or l['id'].startswith('train_') or l['id'].startswith('rfr_')]
unique_stops = {}
for l in train_lines:
    for s in l.get('stops', []):
        sid = s.get('id')
        if sid not in unique_stops:
            unique_stops[sid] = s

print(f"Total unique train/rfr stops in staticTransit.js: {len(unique_stops)}")

# Match each stop
matched = 0
unmatched = []
large_diff = []

for sid, s in unique_stops.items():
    sname = s.get('name', '')
    snorm = normalize(sname)
    slat = float(s['lat'])
    slon = float(s['lon'])
    
    # Try exact normalized name match
    candidates = []
    for cs in csv_stations:
        if snorm and (snorm == cs['norm_name'] or snorm == cs['norm_name_fr']):
            d = haversine(slat, slon, cs['lat'], cs['lon'])
            candidates.append((d, cs))
    
    # If not found, try partial match or nearest within 5km
    if not candidates:
        for cs in csv_stations:
            if snorm and (snorm in cs['norm_name'] or cs['norm_name'] in snorm or snorm in cs['norm_name_fr'] or cs['norm_name_fr'] in snorm):
                d = haversine(slat, slon, cs['lat'], cs['lon'])
                candidates.append((d, cs))
    
    # Sort by distance
    candidates.sort(key=lambda x: x[0])
    if candidates and candidates[0][0] < 15000: # within 15km
        best_d, best_cs = candidates[0]
        matched += 1
        if best_d > 100: # more than 100m difference!
            large_diff.append((sname, best_cs['name_fr'] or best_cs['name'], best_d, slat, slon, best_cs['lat'], best_cs['lon']))
    else:
        # Check nearest station in CSV regardless of name
        nearest = min(csv_stations, key=lambda cs: haversine(slat, slon, cs['lat'], cs['lon']))
        nd = haversine(slat, slon, nearest['lat'], nearest['lon'])
        unmatched.append((sname, slat, slon, nearest['name_fr'] or nearest['name'], nd))

print(f"Matched {matched} / {len(unique_stops)} stops.")
print(f"Stops with > 100m coordinate shift: {len(large_diff)}")
for m in large_diff[:25]:
    print(f"  '{m[0]}' vs '{m[1]}': shift = {m[2]:.1f}m")

print(f"\nUnmatched stops ({len(unmatched)}):")
for u in unmatched[:20]:
    print(f"  '{u[0]}' (nearest in CSV: '{u[3]}' at {u[4]:.1f}m)")

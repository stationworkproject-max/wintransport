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

with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson', 'r', encoding='utf-8') as f:
    rw = json.load(f)

feat = rw['features'][616]
coords = feat['geometry']['coordinates']

# Stations:
# Fej Etameur: (35.87816, 8.70781)
# Gouraia: (35.85844, 8.68463)
# Ain Mesria: (35.91219, 8.73932)

print(f"Feat #616 total points: {len(coords)}")
for name, lat, lon in [('Ain Mesria', 35.91219, 8.73932), ('Fej Etameur', 35.87816, 8.70781), ('Gouraia', 35.85844, 8.68463)]:
    min_d = float('inf')
    best_p = None
    for p in coords:
        d = haversine(lat, lon, p[1], p[0])
        if d < min_d:
            min_d = d
            best_p = p
    print(f"  Station {name}: min distance to feat #616 = {min_d:.1f}m at ({best_p[1]}, {best_p[0]})")

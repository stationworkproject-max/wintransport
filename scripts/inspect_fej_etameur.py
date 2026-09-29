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

# Fej Etameur station: (35.87816, 8.70781)
# Dahmani station: (35.94518, 8.82870)
# Ain Mesria station: (35.91219, 8.73932)
# Gouraia station: (35.85844, 8.68463)
# Jerissa station: (35.85025, 8.65281)

# Let's inspect tracks between Dahmani (35.945, 8.828) and Fej Etameur (35.878, 8.708)
print("Looking for tracks around Dahmani - Fej Etameur:")
for idx, feat in enumerate(rw['features']):
    geom = feat.get('geometry', {})
    coords = geom.get('coordinates', [])
    t = geom.get('type')
    coords_list = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in coords_list:
        p_start = (line[0][1], line[0][0])
        p_end = (line[-1][1], line[-1][0])
        for p in [p_start, p_end]:
            if 35.85 <= p[0] <= 35.97 and 8.65 <= p[1] <= 8.85:
                print(f"feat #{idx:3d}: pts={len(line):3d}, start=({p_start[0]:.5f}, {p_start[1]:.5f}), end=({p_end[0]:.5f}, {p_end[1]:.5f}) | {feat.get('properties', {}).get('name')}")
                break

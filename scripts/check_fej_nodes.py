import json
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson', 'r', encoding='utf-8') as f:
    rw = json.load(f)

# Station Fej Etameur
slat, slon = 35.87816, 8.70781

# Find nearest points across all features
pts = []
for idx, feat in enumerate(rw['features']):
    coords = feat['geometry']['coordinates']
    t = feat['geometry']['type']
    coords_list = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in coords_list:
        for p in line:
            d = haversine(slat, slon, p[1], p[0])
            if d < 50:
                pts.append((d, p[1], p[0], idx))

pts.sort(key=lambda x: x[0])
print("Points within 50m of Fej Etameur:")
for d, lat, lon, fidx in pts:
    print(f"  d={d:.1f}m: ({lat}, {lon}) in feat #{fidx}")

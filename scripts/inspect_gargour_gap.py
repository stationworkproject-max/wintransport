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

p1 = (34.6164812, 10.6215235)
p2 = (34.6201839, 10.6275809)
print(f"Gap between p1 and p2: {haversine(p1[0], p1[1], p2[0], p2[1]):.1f} meters")

# Are there any features near this area?
nearby = []
for idx, feat in enumerate(rw['features']):
    geom = feat.get('geometry', {})
    coords = geom.get('coordinates', [])
    t = geom.get('type')
    coords_list = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in coords_list:
        for p in line:
            if 34.610 <= p[1] <= 34.630 and 10.615 <= p[0] <= 10.635:
                nearby.append((idx, feat.get('properties'), len(line), line[0], line[-1]))
                break

print(f"Found {len(nearby)} features in box:")
for idx, props, npts, start, end in nearby:
    print(f"  feat #{idx}: pts={npts}, start=({start[1]:.5f}, {start[0]:.5f}), end=({end[1]:.5f}, {end[0]:.5f}) | {props.get('name')}")

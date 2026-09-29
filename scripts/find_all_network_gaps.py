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

# Collect all endpoints and track degree
endpoints = []
all_pts = []
degree = {}

for feat in rw['features']:
    coords = feat['geometry']['coordinates']
    t = feat['geometry']['type']
    coords_list = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in coords_list:
        if len(line) < 2: continue
        p0 = (round(line[0][1], 7), round(line[0][0], 7))
        p1 = (round(line[-1][1], 7), round(line[-1][0], 7))
        endpoints.append(p0)
        endpoints.append(p1)
        for p in [p0, p1]:
            degree[p] = degree.get(p, 0) + 1

# Endpoints with degree == 1 (dead ends in the raw file)
dead_ends = [ep for ep, deg in degree.items() if deg == 1]
print(f"Total dead-end endpoints (degree 1): {len(dead_ends)}")

# Find pairs of dead ends that are close to each other (< 1000m)
dead_end_pairs = []
for i in range(len(dead_ends)):
    for j in range(i + 1, len(dead_ends)):
        d = haversine(dead_ends[i][0], dead_ends[i][1], dead_ends[j][0], dead_ends[j][1])
        if 0 < d < 1200:
            dead_end_pairs.append((d, dead_ends[i], dead_ends[j]))

dead_end_pairs.sort(key=lambda x: x[0])
print(f"Found {len(dead_end_pairs)} dead-end pairs within 1200m:")
for d, u, v in dead_end_pairs[:30]:
    print(f"  Gap = {d:6.1f}m between {u} and {v}")

import json
import math
import heapq
from collections import defaultdict

def dist(p1, p2):
    return 6371000 * math.sqrt(math.radians(p2[0]-p1[0])**2 + (math.radians(p2[1]-p1[1])*math.cos(math.radians(p1[0])))**2)

rw = json.load(open(r"C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson", encoding='utf-8', errors='replace'))
features = rw['features']

# Collect all endpoints of railway LineStrings
endpoints = []
for f in features:
    coords = f.get('geometry', {}).get('coordinates', [])
    if len(coords) >= 2:
        endpoints.append((round(coords[0][1], 5), round(coords[0][0], 5)))
        endpoints.append((round(coords[-1][1], 5), round(coords[-1][0], 5)))

print(f"Total track endpoints: {len(endpoints)}")

# Check how many endpoints are close to each other (< 25m) but not identical
close_pairs = []
for i in range(len(endpoints)):
    for j in range(i + 1, min(i + 100, len(endpoints))):
        d = dist(endpoints[i], endpoints[j])
        if 0 < d < 25:
            close_pairs.append((endpoints[i], endpoints[j], d))

print(f"Found {len(close_pairs)} close endpoint pairs within 25m!")

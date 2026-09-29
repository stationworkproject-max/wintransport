import json

def haversine(lat1, lon1, lat2, lon2):
    import math
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

with open('src/data/transitShapes.json', 'r') as f:
    shapes = json.load(f)

for k in ['bus_846_0', 'bus_846_1', 'bus_847_0', 'bus_847_1']:
    pts = shapes.get(k, [])
    tot_d = 0
    for i in range(len(pts)-1):
        tot_d += haversine(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])
    print(f"Shape {k:15s}: {len(pts)} pts, total length = {tot_d:.0f}m")

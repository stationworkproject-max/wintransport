import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('scripts/generated_36b_38b_shapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

def haversine(c1, c2):
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def check_loops(pts, min_crow=40, min_along=400):
    pref = [0.0]
    for m in range(len(pts)-1):
        pref.append(pref[-1] + haversine(pts[m], pts[m+1]))
    loops = []
    for i in range(len(pts)):
        for j in range(i + 10, len(pts)):
            along = pref[j] - pref[i]
            if along < min_along:
                continue
            crow = haversine(pts[i], pts[j])
            if crow < min_crow:
                loops.append((i, j, crow, along, pts[i]))
    return loops

for k in ['bus_846_0', 'bus_846_1', 'bus_847_0', 'bus_847_1']:
    pts = shapes[k]
    loops = check_loops(pts)
    print(f"Shape {k}: {len(pts)} points, {len(loops)} loops detected.")
    if loops:
        # Group loops
        print(f"  First loop: Pts {loops[0][0]}->{loops[0][1]}: crow={loops[0][2]:.1f}m, along={loops[0][3]:.0f}m at {loops[0][4]}")

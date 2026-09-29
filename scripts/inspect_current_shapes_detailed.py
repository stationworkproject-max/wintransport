import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(p1, p2):
    R = 6371000
    phi1, phi2 = math.radians(p1[0]), math.radians(p2[0])
    dphi = math.radians(p2[0] - p1[0])
    dlambda = math.radians(p2[1] - p1[1])
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

with open('src/data/transitShapes.json', 'r') as f:
    shapes = json.load(f)

for k in ['bus_847_0', 'bus_847_1', 'bus_846_0', 'bus_846_1']:
    pts = shapes[k]
    print(f"\n=================== {k} ({len(pts)} pts) ===================")
    
    # Calculate cumulative distance
    cum_d = [0.0]
    for i in range(len(pts) - 1):
        cum_d.append(cum_d[-1] + haversine(pts[i], pts[i+1]))
    print(f"Total shape distance: {cum_d[-1]:.0f}m")
    
    # Check for sections where the shape backtracks or makes big loops
    # For every pair of points i and j where j > i + 10:
    # if geographic distance between pts[i] and pts[j] < 50m, but path distance along shape > 400m -> LOOP!
    loops = []
    for i in range(0, len(pts), 2):
        for j in range(i + 10, len(pts), 2):
            geo_d = haversine(pts[i], pts[j])
            path_d = cum_d[j] - cum_d[i]
            if geo_d < 60 and path_d > 400:
                loops.append((i, j, pts[i], pts[j], geo_d, path_d))
                break # record first occurrence for this i
                
    print(f"Detected {len(loops)} backtrack / loop sections:")
    # deduplicate overlapping loop reports
    last_j = -1
    for i, j, pi, pj, gd, pd in loops:
        if i > last_j:
            print(f"  Loop from pt #{i:3d} ({pi[0]:.5f}, {pi[1]:.5f}) to pt #{j:3d} ({pj[0]:.5f}, {pj[1]:.5f}): geo dist = {gd:.0f}m, path traveled = {pd:.0f}m (detour = {pd-gd:.0f}m)!")
            last_j = j

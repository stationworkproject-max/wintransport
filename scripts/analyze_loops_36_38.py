import json
import math

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

def haversine(c1, c2):
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def total_dist(pts):
    return sum(haversine(pts[i], pts[i+1]) for i in range(len(pts)-1))

for k in ['bus_846_0', 'bus_846_1', 'bus_847_0', 'bus_847_1']:
    pts = shapes[k]
    d = total_dist(pts)
    print(f"=== Shape {k}: {len(pts)} pts, total dist: {d:.0f}m ===")
    
    # Check for self-intersections or backtrack loops (where distance along path between i and j is large but Euclidean distance is very small)
    loops = []
    for i in range(len(pts)):
        for j in range(i + 10, len(pts)):
            crow = haversine(pts[i], pts[j])
            along = sum(haversine(pts[m], pts[m+1]) for m in range(i, j))
            if crow < 50 and along > 400:
                loops.append((i, j, crow, along, pts[i]))
    # Filter overlapping loop reports
    unique_loops = []
    last_j = -1
    for loop in sorted(loops, key=lambda x: -x[3]):
        if loop[0] > last_j or last_j == -1:
            unique_loops.append(loop)
            last_j = loop[1]
    print(f"Detected {len(unique_loops)} major loops:")
    for i, j, crow, along, pt in unique_loops[:5]:
        print(f"  Pts {i}->{j}: crow={crow:.1f}m, along={along:.0f}m at ({pt[0]:.6f}, {pt[1]:.6f})")

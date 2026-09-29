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

def bearing(p1, p2):
    y = math.sin(math.radians(p2[1] - p1[1])) * math.cos(math.radians(p2[0]))
    x = math.cos(math.radians(p1[0])) * math.sin(math.radians(p2[0])) - \
        math.sin(math.radians(p1[0])) * math.cos(math.radians(p2[0])) * math.cos(math.radians(p2[1] - p1[1]))
    return (math.degrees(math.atan2(y, x)) + 360) % 360

with open('src/data/transitShapes.json', 'r') as f:
    shapes = json.load(f)

for shape_key in ['bus_847_0', 'bus_847_1', 'bus_846_0', 'bus_846_1']:
    pts = shapes[shape_key]
    print(f"\n=================== Inspecting {shape_key} ({len(pts)} pts) ===================")
    
    # Check for self-intersections or hairpin turns (bearing difference > 140 deg within short distance)
    uturns = []
    for i in range(1, len(pts) - 1):
        p_prev = pts[i-1]
        p_curr = pts[i]
        p_next = pts[i+1]
        
        d1 = haversine(p_prev, p_curr)
        d2 = haversine(p_curr, p_next)
        
        if d1 > 5 and d2 > 5:
            b1 = bearing(p_prev, p_curr)
            b2 = bearing(p_curr, p_next)
            diff = abs(b1 - b2)
            if diff > 180: diff = 360 - diff
            if diff > 130:
                uturns.append((i, p_curr, diff, d1+d2))
                
    print(f"Found {len(uturns)} sharp U-turns / reversals in {shape_key}:")
    for idx, p, angle, span in uturns[:15]:
        print(f"  pt #{idx:3d} at ({p[0]:.6f}, {p[1]:.6f}): turn angle = {angle:.1f} deg")

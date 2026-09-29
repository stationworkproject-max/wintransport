import urllib.request
import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(c1, c2):
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def check_loops_fast(pts, min_crow=50, min_along=400):
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

# Let's inspect task-1276 result when done or check directly

import urllib.request
import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Test RX at Azzouz Rebai interchange ramp entry: (36.8375, 10.1625)
stops = [
    ("9. Mutuelleville", 36.833778, 10.167208),
    ("10. RX (Rebai ramp)", 36.8375, 10.1625),
    ("11. SONED", 36.835931, 10.160730),
]

coords = ";".join([f"{s[2]},{s[1]}" for s in stops])
url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'T'})) as resp:
    d = json.loads(resp.read())
    r = d['routes'][0]
    print(f"Total: {r['distance']:.0f}m")
    for i, leg in enumerate(r['legs']):
        print(f"\n  Leg {i+1}: {leg['distance']:.0f}m")
        for s in leg['steps']:
            mod = f" ({s['maneuver'].get('modifier')})" if s['maneuver'].get('modifier') else ""
            print(f"    {s['maneuver']['type']}{mod} on '{s.get('name')}' ({s['distance']:.0f}m)")
    uturns = [s for leg in r['legs'] for s in leg['steps'] if 'uturn' in str(s.get('maneuver'))]
    print(f"\nU-turns: {len(uturns)}")

# Now test full 38B Aller with this RX coordinate
stops_38b_aller = [
    ("1", 36.800384, 10.190388),
    ("2", 36.801618, 10.183899),
    ("3", 36.805500, 10.181998),
    ("4", 36.806911, 10.181536),
    ("5", 36.810562, 10.180724),
    ("6", 36.818357, 10.179579),
    ("7", 36.823094, 10.177674),
    ("8", 36.829621, 10.170550),
    ("9", 36.833778, 10.167208),
    ("10", 36.8375, 10.1625),       # RX at Rebai ramp
    ("11", 36.835931, 10.160730),    # SONED westbound
    ("12", 36.832431, 10.154153),    # Clinique Taoufik westbound
    ("13", 36.830720, 10.150380),
    ("14", 36.832833, 10.148073),
    ("15", 36.836543, 10.144694),
    ("16", 36.835397, 10.138117),
    ("17", 36.836190, 10.132044),
    ("18", 36.836859, 10.129029),
]

coords2 = ";".join([f"{s[2]},{s[1]}" for s in stops_38b_aller])
url2 = f"https://router.project-osrm.org/route/v1/driving/{coords2}?overview=full&geometries=geojson"
with urllib.request.urlopen(urllib.request.Request(url2, headers={'User-Agent': 'T'})) as resp:
    d = json.loads(resp.read())
    r = d['routes'][0]
    pts = [[round(p[1], 5), round(p[0], 5)] for p in r['geometry']['coordinates']]
    print(f"\n\nFull 38B Aller: {r['distance']:.0f}m, {len(pts)} pts")
    for i, leg in enumerate(r['legs']):
        s1, s2 = stops_38b_aller[i], stops_38b_aller[i+1]
        crow = 1000 * (((s1[1]-s2[1])*111)**2 + ((s1[2]-s2[2])*89)**2)**0.5
        ratio = leg['distance'] / max(1.0, crow)
        warn = " *** DETOUR ***" if ratio > 1.8 and leg['distance'] > 300 else ""
        print(f"  Leg {i+1:2d}->{i+2:2d}: {leg['distance']:5.0f}m [crow: {crow:4.0f}m, ratio: {ratio:.2f}]{warn}")

    # Check for loops in the shape
    def haversine(c1, c2):
        lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
        lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    pref = [0.0]
    for m in range(len(pts)-1):
        pref.append(pref[-1] + haversine(pts[m], pts[m+1]))
    loops = 0
    for i in range(len(pts)):
        for j in range(i + 10, len(pts)):
            along = pref[j] - pref[i]
            if along < 400: continue
            crow = haversine(pts[i], pts[j])
            if crow < 40:
                loops += 1
    print(f"  Loops detected: {loops}")

import json
import re
import math
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

b38b = next(l for l in lines if l['id'] == 'bus_847')

def osrm_route(points):
    coords_str = ";".join([f"{p[1]:.6f},{p[0]:.6f}" for p in points])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data.get('code') == 'Ok' and data.get('routes'):
                r = data['routes'][0]
                return r['distance'], [[round(c[1], 6), round(c[0], 6)] for c in r['geometry']['coordinates']]
    except Exception as e:
        print(f"Error: {e}")
    return None, None

aller_stops = list(b38b.get('stops_aller', []))
retour_stops = list(b38b.get('stops_retour', []))

# For Aller:
# Taoufik: (36.831696, 10.152933)
# SONED: (36.835594, 10.160092)
aller_coords = []
for s in aller_stops:
    n = s.get('name', '').upper()
    if 'TAOUFIK' in n:
        aller_coords.append((36.831696, 10.152933))
    elif 'SONED' in n:
        aller_coords.append((36.835594, 10.160092))
    else:
        aller_coords.append((s['lat'], s['lon']))

dist_a, pts_a = osrm_route(aller_coords)
print(f"NEW 38B Aller total distance: {dist_a}m, points: {len(pts_a) if pts_a else 0}")

# For Retour:
# Taoufik: (36.832198, 10.154312)
# SONED: (36.836019, 10.161154)
retour_coords = []
for s in retour_stops:
    n = s.get('name', '').upper()
    if 'TAOUFIK' in n:
        retour_coords.append((36.832198, 10.154312))
    elif 'SONED' in n:
        retour_coords.append((36.836019, 10.161154))
    else:
        retour_coords.append((s['lat'], s['lon']))

dist_r, pts_r = osrm_route(retour_coords)
print(f"NEW 38B Retour total distance: {dist_r}m, points: {len(pts_r) if pts_r else 0}")

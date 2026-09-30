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
        pass
    return None, None

def osrm_leg(p1, p2):
    url = f"https://router.project-osrm.org/route/v1/driving/{p1[1]:.6f},{p1[0]:.6f};{p2[1]:.6f},{p2[0]:.6f}?overview=false"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get('code') == 'Ok' and data.get('routes'):
                return data['routes'][0]['distance']
    except Exception as e:
        return None
    return None

aller_stops = b38b.get('stops_aller', [])
retour_stops = b38b.get('stops_retour', [])

print("=== 38B ALLER LEGS ===")
for i in range(len(aller_stops) - 1):
    s1, s2 = aller_stops[i], aller_stops[i+1]
    d = osrm_leg((s1['lat'], s1['lon']), (s2['lat'], s2['lon']))
    print(f"  {i+1}->{i+2}: {s1.get('name_fr')} -> {s2.get('name_fr')}: {d}m")

print("\n=== 38B RETOUR LEGS ===")
for i in range(len(retour_stops) - 1):
    s1, s2 = retour_stops[i], retour_stops[i+1]
    d = osrm_leg((s1['lat'], s1['lon']), (s2['lat'], s2['lon']))
    print(f"  {i+1}->{i+2}: {s1.get('name_fr')} -> {s2.get('name_fr')}: {d}m")

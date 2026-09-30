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

def haversine(p1, p2):
    R = 6371000
    phi1, phi2 = math.radians(p1[0]), math.radians(p2[0])
    dphi, dlambda = math.radians(p2[0] - p1[0]), math.radians(p2[1] - p1[1])
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def osrm_route(points):
    coords_str = ";".join([f"{p[1]:.6f},{p[0]:.6f}" for p in points])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI-Transit-Engine/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data.get('code') != 'Ok' or not data.get('routes'):
                return None
            r = data['routes'][0]
            pts = [[round(c[1], 6), round(c[0], 6)] for c in r['geometry']['coordinates']]
            dist = r['distance']
            return pts, dist
    except Exception as e:
        return None

# Let's inspect 36B Aller and Retour stops
b36b = next(l for l in lines if l['id'] == 'bus_846')

# Check Aller stops of 36B
aller = b36b.get('stops_aller', [])
retour = b36b.get('stops_retour', [])

print("36B Aller stop names:")
for i, s in enumerate(aller):
    print(f"  {i+1}: {s.get('name_fr')} ({s['lat']}, {s['lon']})")

print("\n36B Retour stop names:")
for i, s in enumerate(retour):
    print(f"  {i+1}: {s.get('name_fr')} ({s['lat']}, {s['lon']})")

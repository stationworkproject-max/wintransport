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

def haversine(p1, p2):
    R = 6371000
    phi1, phi2 = math.radians(p1[0]), math.radians(p2[0])
    dphi, dlambda = math.radians(p2[0] - p1[0]), math.radians(p2[1] - p1[1])
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

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

retour_stops = list(b38b.get('stops_retour', []))
for s in retour_stops:
    if 'TAOUFIK' in s.get('name', '').upper() or 'TAOUFIK' in s.get('name_fr', '').upper():
        s['lat'] = 36.832198
        s['lon'] = 10.154312

print("=== 38B RETOUR LEGS WITH FIXED TAOUFIK ===")
for i in range(len(retour_stops) - 1):
    s1, s2 = retour_stops[i], retour_stops[i+1]
    p1 = (s1['lat'], s1['lon'])
    p2 = (s2['lat'], s2['lon'])
    crow_d = haversine(p1, p2)
    d = osrm_leg(p1, p2)
    ratio = (d / crow_d) if (d and crow_d > 0) else 1.0
    flag = " *** DETOUR ***" if (d and d - crow_d > 800) else ""
    print(f"  [{i+1}->{i+2}] {s1.get('name_fr')} -> {s2.get('name_fr')}: crow={crow_d:.0f}m, road={d}m{flag}")

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

for bid in ['bus_846', 'bus_847']:
    line = next(l for l in lines if l['id'] == bid)
    print(f"\n=======================================================")
    print(f"DIAGNOSING LINE {line['short_name']} ({bid}): {line['long_name_fr']}")
    print(f"=======================================================")
    
    for dir_idx, gname in [(0, 'stops_aller'), (1, 'stops_retour')]:
        stops = line.get(gname, [])
        print(f"\n--- Direction {dir_idx} ({gname}) - {len(stops)} stops ---")
        for i in range(len(stops) - 1):
            s1 = stops[i]
            s2 = stops[i+1]
            p1 = (s1['lat'], s1['lon'])
            p2 = (s2['lat'], s2['lon'])
            crow_d = haversine(p1, p2)
            osrm_d = osrm_leg(p1, p2)
            ratio = (osrm_d / crow_d) if (osrm_d and crow_d > 0) else 1.0
            
            flag = ""
            if osrm_d and (osrm_d - crow_d > 1000 or ratio > 2.5):
                flag = f" [*** DETOUR: road={osrm_d:.0f}m, crow={crow_d:.0f}m, ratio={ratio:.1f}x ***]"
            
            print(f"  [{i+1} -> {i+2}] {s1.get('name_fr', s1.get('name'))} -> {s2.get('name_fr', s2.get('name'))}: crow={crow_d:.0f}m, road={osrm_d if osrm_d else 'N/A'}m{flag}")

import json
import re
import sys
import urllib.request
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. Load staticTransit.js
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

# 2. Load transitShapes.json
with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

# Backup transitShapes.json
with open('src/data/transitShapes.json.pre-bus-update.bak', 'w', encoding='utf-8') as f:
    json.dump(shapes, f)

def osrm_route(points):
    coords_str = ";".join([f"{p[1]:.6f},{p[0]:.6f}" for p in points])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI-Transit-Engine/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            if data.get('code') != 'Ok' or not data.get('routes'):
                return None
            r = data['routes'][0]
            # OSRM returns [lon, lat], Leaflet needs [lat, lon]
            pts = [[round(c[1], 6), round(c[0], 6)] for c in r['geometry']['coordinates']]
            return pts
    except Exception as e:
        print(f"  OSRM error: {e}")
        return None

target_bus_ids = ['bus_846', 'bus_847', 'bus_772', 'bus_703']

for bid in target_bus_ids:
    line = next((l for l in lines if l['id'] == bid), None)
    if not line:
        continue
    print(f"\nRouting {line['id']} ({line['short_name']} - {line['long_name_fr']}):")
    
    aller_stops = line.get('stops_aller', line.get('stops', []))
    retour_stops = line.get('stops_retour', [])
    
    # Aller (0)
    aller_coords = [(s['lat'], s['lon']) for s in aller_stops]
    pts_aller = osrm_route(aller_coords)
    if pts_aller:
        key_aller = f"{bid}_0"
        shapes[key_aller] = pts_aller
        shapes[bid] = pts_aller
        print(f"  Aller ({key_aller}): {len(pts_aller)} points saved")
    else:
        print(f"  Aller ({bid}_0) FAILED")
        
    time.sleep(0.5)
    
    # Retour (1)
    if retour_stops:
        retour_coords = [(s['lat'], s['lon']) for s in retour_stops]
        pts_retour = osrm_route(retour_coords)
        if pts_retour:
            key_retour = f"{bid}_1"
            shapes[key_retour] = pts_retour
            print(f"  Retour ({key_retour}): {len(pts_retour)} points saved")
        else:
            print(f"  Retour ({bid}_1) FAILED")
    time.sleep(0.5)

# Save updated transitShapes.json
with open('src/data/transitShapes.json', 'w', encoding='utf-8') as f:
    json.dump(shapes, f)

print("\nSuccessfully updated bus shapes in src/data/transitShapes.json!")

import json
import re
import math
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. Load test_directional_matcher logic
from test_directional_matcher import find_best_osm_stop, clean_direction_tag

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

def osrm_route(points):
    # points is list of (lat, lon)
    coords_str = ";".join([f"{p[1]:.6f},{p[0]:.6f}" for p in points])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI-Transit-Engine/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data.get('code') != 'Ok' or not data.get('routes'):
                return None, 0
            r = data['routes'][0]
            pts = [[c[1], c[0]] for c in r['geometry']['coordinates']]
            return pts, r['distance']
    except Exception as e:
        print("  OSRM error:", e)
        return None, 0

for lid in ['bus_846', 'bus_847', 'bus_772', 'bus_703']:
    line = next((l for l in lines if l['id'] == lid), None)
    print(f"\n==========================================")
    print(f"ROUTING DIRECTIONAL: {line['id']} - {line['short_name']}")
    print(f"==========================================")
    for dir_idx, gname, target_dir in [(0, 'stops_aller', 'aller'), (1, 'stops_retour', 'retour')]:
        stops = line.get(gname, [])
        corrected_coords = []
        print(f"\n-- {gname} ({target_dir}) --")
        for i, s in enumerate(stops):
            match = find_best_osm_stop(s['lat'], s['lon'], s['name'], target_dir)
            if match and match[0] <= 150:
                d, gs, score, sim = match
                lat, lon = gs['lat'], gs['lon']
                name_ar = gs['name_ar']
                name_fr = gs['name_fr']
                corrected_coords.append((lat, lon))
                print(f"[{i+1:02d}] {s['name']} -> ({lat:.5f}, {lon:.5f}) | FR: '{name_fr}' | AR: '{name_ar}'")
            else:
                lat, lon = s['lat'], s['lon']
                corrected_coords.append((lat, lon))
                print(f"[{i+1:02d}] {s['name']} -> kept orig ({lat:.5f}, {lon:.5f})")
                
        # Now route through OSRM
        pts, dist = osrm_route(corrected_coords)
        if pts:
            print(f"==> OSRM Route successful: {len(pts)} points, total distance: {dist:.0f}m")
        else:
            print("==> OSRM Route failed!")

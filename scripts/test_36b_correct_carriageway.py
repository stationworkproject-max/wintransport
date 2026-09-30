import json
import re
import math
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def osrm_route(points):
    coords_str = ";".join([f"{p[1]:.6f},{p[0]:.6f}" for p in points])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data.get('code') == 'Ok' and data.get('routes'):
                r = data['routes'][0]
                pts = [[round(c[1], 6), round(c[0], 6)] for c in r['geometry']['coordinates']]
                return pts, r['distance']
    except Exception as e:
        print(f"Error: {e}")
        return None, None
    return None, None

# Test 36B Aller with swapped Taoufik, Campus, 14 Janvier
# Also let's check Foyer Bardo 1 & 2
aller_pts = [
    (36.830000, 10.157500), # Terminus Min Affaires Etrangeres
    (36.831696, 10.152933), # Taoufik (Southbound)
    (36.825369, 10.143889), # Campus (Southbound)
    (36.823507, 10.141496), # 14 Janvier (Southbound)
    (36.818324, 10.141459), # Foyer Bardo 2 (Southbound)
    (36.814154, 10.146217), # Foyer Bardo 1
    (36.812835, 10.145171), # Cafe El Haj
    (36.808844, 10.137977), # Touta Bardo
]

pts_a, dist_a = osrm_route(aller_pts)
print(f"Test 36B Aller total distance: {dist_a}m, points: {len(pts_a) if pts_a else 0}")

# Test 36B Retour with opposite coordinates
retour_pts = [
    (36.808844, 10.137977), # Touta Bardo
    (36.812810, 10.144989), # Cafe El Haj
    (36.813941, 10.146199), # Foyer Bardo 1
    (36.818640, 10.141400), # Foyer Bardo 2
    (36.823507, 10.141813), # 14 Janvier (Northbound)
    (36.825112, 10.143985), # Campus (Northbound)
    (36.832198, 10.154312), # Taoufik (Northbound)
    (36.829562, 10.159038), # Terminus Min Affaires Etrangeres
]

pts_r, dist_r = osrm_route(retour_pts)
print(f"Test 36B Retour total distance: {dist_r}m, points: {len(pts_r) if pts_r else 0}")

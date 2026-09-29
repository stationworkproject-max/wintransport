import urllib.request
import json
import math

def dist(p1, p2):
    return 6371000 * math.sqrt(math.radians(p2[0]-p1[0])**2 + (math.radians(p2[1]-p1[1])*math.cos(math.radians(p1[0])))**2)

c6 = (36.83072, 10.15038)   # FACULTE DE DROIT
c7 = (36.832198, 10.154312) # CLINIQUE TAOUFIK ALLER
c8 = (36.834114, 10.16144)  # SONED
c9 = (36.834838, 10.164142) # RX
c10 = (36.833778, 10.167208) # MUNICIPALITE

# 1. Original route 6 -> 7 -> 8 -> 9 -> 10
pts_orig = [c6, c7, c8, c9, c10]
coords_str = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in pts_orig])
url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=false"
req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    print(f"Original Retour 6->10 distance: {data['routes'][0]['distance']:.0f}m")
    for i, leg in enumerate(data['routes'][0]['legs']):
        print(f"  Leg {i+6}->{i+7}: {leg['distance']:.0f}m")

# 2. What is the direct route from 6 (Faculte de Droit) to 10 (Municipalite)?
url_direct = f"https://router.project-osrm.org/route/v1/driving/{c6[1]},{c6[0]};{c10[1]},{c10[0]}?overview=full&geometries=geojson"
req_dir = urllib.request.Request(url_direct, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req_dir) as resp:
    data_dir = json.loads(resp.read())
    corridor = [(c[1], c[0]) for c in data_dir['routes'][0]['geometry']['coordinates']]
    print(f"\nDirect forward corridor 6->10 distance: {data_dir['routes'][0]['distance']:.0f}m")

# Snap 7, 8, 9 to this direct forward corridor!
snap_7 = min(corridor, key=lambda p: dist(p, c7))
snap_8 = min(corridor, key=lambda p: dist(p, c8))
snap_9 = min(corridor, key=lambda p: dist(p, c9))

print(f"Snap 7 (Clinique Taoufik): moved {dist(snap_7, c7):.1f}m to {snap_7}")
print(f"Snap 8 (SONED): moved {dist(snap_8, c8):.1f}m to {snap_8}")
print(f"Snap 9 (RX): moved {dist(snap_9, c9):.1f}m to {snap_9}")

# Test route with snapped stops:
pts_snapped = [c6, snap_7, snap_8, snap_9, c10]
coords_str_s = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in pts_snapped])
url_s = f"https://router.project-osrm.org/route/v1/driving/{coords_str_s}?overview=false"
req_s = urllib.request.Request(url_s, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req_s) as resp:
    data_s = json.loads(resp.read())
    print(f"\nTotal Retour distance with corridor-snapped stops: {data_s['routes'][0]['distance']:.0f}m")
    for i, leg in enumerate(data_s['routes'][0]['legs']):
        print(f"  Leg {i+6}->{i+7}: {leg['distance']:.0f}m")

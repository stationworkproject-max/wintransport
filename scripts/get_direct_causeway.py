import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Query OSRM between Tunis Marine (36.801, 10.192) and La Goulette (36.818, 10.302) along the direct causeway
p1 = (36.805, 10.220) # on the causeway
p2 = (36.816, 10.298) # near Le Bac / La Goulette

url = f"https://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

route = data['routes'][0]
pts = [[round(c[1], 6), round(c[0], 6)] for c in route['geometry']['coordinates']]
print(f"Direct Causeway Road has {len(pts)} points:")
for p in pts:
    if 10.280 <= p[1] <= 10.295:
        print(f"  lat={p[0]}, lon={p[1]}")

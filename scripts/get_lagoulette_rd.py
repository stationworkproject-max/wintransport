import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Query OSRM for La Goulette Rd
p_start = (36.8130, 10.2850)
p_end = (36.8145, 10.2930)

url = f"https://router.project-osrm.org/route/v1/driving/{p_start[1]},{p_start[0]};{p_end[1]},{p_end[0]}?overview=full&geometries=geojson"
req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

route = data['routes'][0]
pts = [[round(c[1], 6), round(c[0], 6)] for c in route['geometry']['coordinates']]
print(f"La Goulette Rd has {len(pts)} points:")
for p in pts:
    print(f"  lat={p[0]}, lon={p[1]}")

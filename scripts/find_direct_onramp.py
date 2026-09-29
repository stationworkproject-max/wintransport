import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p9 = (36.833778, 10.167208) # Mutuelleville
p11 = (36.836069, 10.160991) # SONED

# Let's route directly from p9 to p11
url = f"https://router.project-osrm.org/route/v1/driving/{p9[1]},{p9[0]};{p11[1]},{p11[0]}?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    r = data['routes'][0]
    print(f"Direct route p9 -> p11: {r['distance']:.0f}m")
    steps = r['legs'][0]['steps']
    for st in steps:
        mod = f" ({st['maneuver'].get('modifier')})" if st['maneuver'].get('modifier') else ""
        print(f"  {st['maneuver']['type']}{mod:15s} on '{st.get('name')}' ({st['distance']:.0f}m)")
    coords = r['geometry']['coordinates']

# Look at points along this direct route to find a natural position for Station 10 (RX)
# Midway between p9 and p11
print(f"\nTotal points on direct route: {len(coords)}")
for idx in [10, 20, 30, 40, 50, 60]:
    if idx < len(coords):
        pt = coords[idx]
        print(f"  Pt {idx}: ({pt[1]:.6f}, {pt[0]:.6f})")

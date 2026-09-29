import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p6 = (36.823507, 10.141813)
# Let's test points slightly north/left so it stays on Avenue Mohamed Bouazizi mainline
test_pts = [
    ("Mainline 1", 36.82535, 10.14410),
    ("Mainline 2", 36.82545, 10.14400),
    ("Mainline 3", 36.82555, 10.14390),
    ("Mainline 4", 36.82565, 10.14380),
    ("Mainline 5", 36.82520, 10.14380),
    ("Mainline 6", 36.82530, 10.14370),
]

p8 = (36.832198, 10.154312)

for name, lat, lon in test_pts:
    url = f"https://router.project-osrm.org/route/v1/driving/{p6[1]},{p6[0]};{lon},{lat};{p8[1]},{p8[0]}?overview=full&geometries=geojson&steps=true"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        data = json.loads(resp.read())
        r = data['routes'][0]
        legs = r['legs']
        steps2 = [f"{s['maneuver']['type']}({s.get('name')})" for s in legs[1]['steps'] if s['distance'] > 50]
        print(f"{name} ({lat}, {lon}) -> Leg 1: {legs[0]['distance']:.0f}m, Leg 2: {legs[1]['distance']:.0f}m | Total: {r['distance']:.0f}m | Steps in Leg 2: {steps2}")

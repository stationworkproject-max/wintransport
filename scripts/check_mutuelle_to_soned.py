import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_mutuelle = (36.833778, 10.167208)
p_soned = (36.835931, 10.160730)

# Check route from Mutuelleville directly to SONED
url_direct = f"https://router.project-osrm.org/route/v1/driving/{p_mutuelle[1]},{p_mutuelle[0]};{p_soned[1]},{p_soned[0]}?overview=full&steps=true"
req = urllib.request.Request(url_direct, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    route = data['routes'][0]
    print(f"Direct route Mutuelleville -> SONED: {route['distance']:.0f}m")
    for st in route['legs'][0]['steps']:
        name = st.get('name', 'unnamed')
        print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):12s} on '{name}' ({st['distance']:.0f}m)")

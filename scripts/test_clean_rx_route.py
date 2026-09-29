import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p9 = (36.833778, 10.167208)
p10 = (36.838500, 10.164200) # Southbound RX
p11 = (36.835931, 10.160730)

url = f"https://router.project-osrm.org/route/v1/driving/{p9[1]},{p9[0]};{p10[1]},{p10[0]};{p11[1]},{p11[0]}?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    route = data['routes'][0]
    print(f"Total distance: {route['distance']:.0f}m")
    for i, leg in enumerate(route['legs']):
        print(f"\n--- Leg {i+9}->{i+10} ({leg['distance']:.0f}m) ---")
        for st in leg['steps']:
            mod = f" ({st['maneuver'].get('modifier')})" if st['maneuver'].get('modifier') else ""
            print(f"  {st['maneuver']['type']}{mod:12s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

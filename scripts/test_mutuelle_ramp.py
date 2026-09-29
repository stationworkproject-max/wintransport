import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p9 = (36.833778, 10.167208)
p10 = (36.8380, 10.1644)
p11 = (36.836069, 10.160991)

url = f"https://router.project-osrm.org/route/v1/driving/{p9[1]},{p9[0]};{p10[1]},{p10[0]};{p11[1]},{p11[0]}?overview=full&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    r = data['routes'][0]
    legs = r['legs']
    print(f"Total distance: {r['distance']:.0f}m")
    for i, leg in enumerate(legs):
        print(f"Leg {i+1}: {leg['distance']:.0f}m")
        for s in leg['steps']:
            mod = f" ({s['maneuver'].get('modifier')})" if s['maneuver'].get('modifier') else ""
            print(f"    {s['maneuver']['type']}{mod:15s} on '{s.get('name')}' ({s['distance']:.0f}m)")

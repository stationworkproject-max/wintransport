import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p5 = (36.820024, 10.139791)
p6 = (36.823507, 10.141813)
p7 = (36.825112, 10.143985)

url = f"https://router.project-osrm.org/route/v1/driving/{p5[1]},{p5[0]};{p6[1]},{p6[0]};{p7[1]},{p7[0]}?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    r = data['routes'][0]
    print(f"Total: {r['distance']:.0f}m")
    for i, leg in enumerate(r['legs']):
        print(f"\nLeg {i+1}: ({leg['distance']:.0f}m)")
        for s in leg['steps']:
            print(f"  {s['maneuver']['type']} ({s['maneuver'].get('modifier', '')}) on '{s.get('name')}' ({s['distance']:.0f}m)")

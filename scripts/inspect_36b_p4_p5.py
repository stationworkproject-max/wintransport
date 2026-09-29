import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p4 = (36.823508, 10.141495)
p5 = (36.818349, 10.141493)

url = f"https://router.project-osrm.org/route/v1/driving/{p4[1]},{p4[0]};{p5[1]},{p5[0]}?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    r = data['routes'][0]
    print(f"Distance p4 -> p5: {r['distance']:.0f}m")
    for s in r['legs'][0]['steps']:
        print(f"  {s['maneuver']['type']} ({s['maneuver'].get('modifier', '')}) on '{s.get('name')}' ({s['distance']:.0f}m)")
    coords = r['geometry']['coordinates']
    print(f"Coordinates count: {len(coords)}")

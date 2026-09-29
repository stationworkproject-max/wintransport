import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p10 = (36.837944, 10.165321)
p11 = (36.835931, 10.160730)

url = f"https://router.project-osrm.org/route/v1/driving/{p10[1]},{p10[0]};{p11[1]},{p11[0]}?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    leg = data['routes'][0]['legs'][0]
    print(f"Distance: {leg['distance']:.0f}m")
    for st in leg['steps']:
        print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):10s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

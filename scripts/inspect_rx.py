import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

url = 'https://router.project-osrm.org/route/v1/driving/10.167208,36.833778;10.160730,36.835931?overview=full&geometries=geojson&steps=true'
resp = urllib.request.urlopen(url)
d = json.loads(resp.read())
print(f'Distance 9->11 direct: {d["routes"][0]["distance"]}m')
for s in d['routes'][0]['legs'][0]['steps']:
    print(f"  {s['maneuver']['type']} ({s['maneuver'].get('modifier', '')}) on {s.get('name')} ({s['distance']:.0f}m)")

coords = d['routes'][0]['geometry']['coordinates']
print("Points count:", len(coords))
for p in coords:
    print(f"  {p[1]:.6f}, {p[0]:.6f}")

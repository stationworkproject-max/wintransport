import urllib.request
import json

c10 = (36.838561, 10.166151) # RX
c11 = (36.835735, 10.160893) # SONED
c12 = (36.832491, 10.154094) # CLINIQUE TAOUFIK
c13 = (36.83072, 10.15038)   # FACULTE DE DROIT

# Let's inspect the route between 11 and 12
url = f"https://router.project-osrm.org/route/v1/driving/{c11[1]},{c11[0]};{c12[1]},{c12[0]}?overview=full&geometries=geojson&steps=true"
req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    route = data['routes'][0]
    print(f"Leg 11 -> 12 distance: {route['distance']:.0f}m")
    for s in route['legs'][0]['steps']:
        name = ''.join([c for c in s.get('name', '') if ord(c) < 128])
        print(f"  {s['maneuver']['type']} {s['maneuver'].get('modifier', '')} on '{name}' ({s['distance']:.0f}m)")

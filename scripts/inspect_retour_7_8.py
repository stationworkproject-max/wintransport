import urllib.request
import json

c6 = (36.83072, 10.15038)   # FACULTE DE DROIT
c7 = (36.832198, 10.154312) # CLINIQUE TAOUFIK ALLER
c8 = (36.834114, 10.16144)  # SONED
c9 = (36.834838, 10.164142) # RX

# Let's inspect leg 7 -> 8
url = f"https://router.project-osrm.org/route/v1/driving/{c7[1]},{c7[0]};{c8[1]},{c8[0]}?overview=full&geometries=geojson&steps=true"
req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    route = data['routes'][0]
    print(f"Leg 7 -> 8 distance: {route['distance']:.0f}m")
    for s in route['legs'][0]['steps']:
        name = ''.join([c for c in s.get('name', '') if ord(c) < 128])
        print(f"  {s['maneuver']['type']} {s['maneuver'].get('modifier', '')} on '{name}' ({s['distance']:.0f}m)")

# Also inspect c6 -> c7 -> c8 -> c9
url_all = f"https://router.project-osrm.org/route/v1/driving/{c6[1]},{c6[0]};{c7[1]},{c7[0]};{c8[1]},{c8[0]};{c9[1]},{c9[0]}?overview=false"
req_all = urllib.request.Request(url_all, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req_all) as resp:
    data = json.loads(resp.read())
    print(f"Total 6 -> 7 -> 8 -> 9 distance: {data['routes'][0]['distance']:.0f}m")
    for i, leg in enumerate(data['routes'][0]['legs']):
        print(f"  Leg {i+6}->{i+7}: {leg['distance']:.0f}m")

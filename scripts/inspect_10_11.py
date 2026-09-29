import urllib.request
import json

c10 = (36.838561, 10.166151)
c11 = (36.835836, 10.160809)

url = f"https://router.project-osrm.org/route/v1/driving/{c10[1]},{c10[0]};{c11[1]},{c11[0]}?overview=false&steps=true"
req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    print("Steps from 10 to 11:")
    for s in data['routes'][0]['legs'][0]['steps']:
        name = ''.join([c for c in s.get('name', '') if ord(c) < 128])
        print(f"  {s['maneuver']['type']} {s['maneuver'].get('modifier', '')} on '{name}' ({s['distance']:.0f}m)")

import urllib.request
import json

stops = [
    ("10 RX", 36.838561, 10.166151),
    ("11 SONED", 36.835735, 10.160893),
    ("12 CLINIQUE TAOUFIK", 36.832491, 10.154094),
    ("13 FACULTE DE DROIT", 36.83072, 10.15038)
]

for i in range(len(stops) - 1):
    s1, lat1, lon1 = stops[i]
    s2, lat2, lon2 = stops[i+1]
    url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false&steps=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test38B'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        r = data['routes'][0]
        print(f"\n=== Leg {s1} -> {s2}: Distance {r['distance']:.0f}m ===")
        for step in r['legs'][0]['steps']:
            name = ''.join([c for c in step.get('name', '') if ord(c) < 128])
            m = step['maneuver']
            print(f"  {m['type']} {m.get('modifier', '')} on '{name}' ({step['distance']:.0f}m)")

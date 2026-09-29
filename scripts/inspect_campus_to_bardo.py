import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p3 = (36.825369, 10.143889) # Campus
p4 = (36.823508, 10.141495) # 14 Janvier 2011
p5 = (36.818349, 10.141493) # Foyer Bardo 2

# Direct route 3 -> 5 without stop 4:
url_3_5 = f"https://router.project-osrm.org/route/v1/driving/{p3[1]},{p3[0]};{p5[1]},{p5[0]}?overview=full&steps=true"
with urllib.request.urlopen(urllib.request.Request(url_3_5, headers={'User-Agent': 'Test'})) as resp:
    d = json.loads(resp.read())
    print(f"Direct Campus -> Foyer Bardo 2 (without stop 4): {d['routes'][0]['distance']:.0f}m")
    for st in d['routes'][0]['legs'][0]['steps']:
        print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):10s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

# Route with stop 4:
url_3_4_5 = f"https://router.project-osrm.org/route/v1/driving/{p3[1]},{p3[0]};{p4[1]},{p4[0]};{p5[1]},{p5[0]}?overview=full&steps=true"
with urllib.request.urlopen(urllib.request.Request(url_3_4_5, headers={'User-Agent': 'Test'})) as resp:
    d = json.loads(resp.read())
    print(f"\nRoute Campus -> 14 Janvier -> Foyer Bardo 2: {d['routes'][0]['distance']:.0f}m")
    for i, leg in enumerate(d['routes'][0]['legs']):
        print(f"  Leg {i+1} ({leg['distance']:.0f}m):")
        for st in leg['steps']:
            print(f"    {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):10s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

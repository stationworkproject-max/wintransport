import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_mutuelle = (36.833778, 10.167208)
p_soned_west = (36.836069, 10.160991)

# What are the ways from p_mutuelle to p_soned_west?
# In Mutuelleville, Rue Jugurtha goes north towards RX interchange.
# Let's inspect the nodes along Rue Jugurtha as it approaches Bouazizi
coords = [
    ("Mutuelleville", 36.833778, 10.167208),
    ("Jugurtha mid", 36.8355, 10.1664),
    ("Jugurtha north", 36.8370, 10.1658),
    ("Interchange ramp", 36.8380, 10.1653),
]

for name, lat, lon in coords:
    url = f"https://router.project-osrm.org/route/v1/driving/{p_mutuelle[1]},{p_mutuelle[0]};{lon},{lat};{p_soned_west[1]},{p_soned_west[0]}?overview=full&steps=true"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        legs = r['legs']
        print(f"\n--- Via {name} ({lat}, {lon}) --- Total: {r['distance']:.0f}m")
        print(f"  Leg 1: {legs[0]['distance']:.0f}m, Leg 2: {legs[1]['distance']:.0f}m")
        uturns = [s for leg in legs for s in leg['steps'] if 'uturn' in str(s.get('maneuver'))]
        print(f"  U-turns: {len(uturns)}")
        for leg in legs:
            for s in leg['steps']:
                if s['distance'] > 100:
                    print(f"    {s['maneuver']['type']} on {s.get('name')} ({s['distance']:.0f}m)")

import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_mutuelle = (36.833778, 10.167208)
p_soned = (36.835931, 10.160730)

# Test various coordinates for Station 10 (RX) in Aller
test_coords = [
    ("Current RX Aller in staticTransit", 36.838100, 10.165200),
    ("RX at Jugurtha in front of Retour", 36.835544, 10.166400),
    ("RX near interchange ramp", 36.837500, 10.165200),
    ("RX at Rue Azzouz Rebai entrance", 36.838200, 10.164500),
]

for label, lat, lon in test_coords:
    url = f"https://router.project-osrm.org/route/v1/driving/{p_mutuelle[1]},{p_mutuelle[0]};{lon},{lat};{p_soned[1]},{p_soned[0]}?overview=full&geometries=geojson&steps=true"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        legs = r['legs']
        print(f"\n=== Testing {label} ({lat:.6f}, {lon:.6f}) ===")
        print(f"Total distance: {r['distance']:.0f}m | leg 9->10: {legs[0]['distance']:.0f}m, leg 10->11: {legs[1]['distance']:.0f}m")
        # Check if there is any U-turn step
        has_uturn = any(st['maneuver'].get('modifier') == 'uturn' for leg in legs for st in leg['steps'])
        print(f"Contains U-turn? {has_uturn}")
        for leg_idx, leg in enumerate(legs):
            print(f"  Leg {leg_idx+1}:")
            for st in leg['steps']:
                mod = f" ({st['maneuver'].get('modifier')})" if st['maneuver'].get('modifier') else ""
                print(f"    {st['maneuver']['type']}{mod:12s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

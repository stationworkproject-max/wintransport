import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

stops = [
    ("10. RX", 36.838100, 10.165200),
    ("11. SONED", 36.835932, 10.160730),
    ("12. CLINIQUE TAOUFIK", 36.832431, 10.154153),
    ("13. FACULTE DE DROIT", 36.830720, 10.150380),
]

for i in range(len(stops) - 1):
    s1 = stops[i]
    s2 = stops[i+1]
    url = f"https://router.project-osrm.org/route/v1/driving/{s1[2]},{s1[1]};{s2[2]},{s2[1]}?overview=full&geometries=geojson&steps=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        route = data['routes'][0]
        print(f"\n--- Leg {s1[0]} -> {s2[0]} (Distance: {route['distance']:.0f}m) ---")
        for st in route['legs'][0]['steps']:
            name = st.get('name', 'unnamed')
            print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):12s} on '{name}' ({st['distance']:.0f}m)")

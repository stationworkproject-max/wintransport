import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

stops_retour = [
    ("6. Faculte de Droit", 36.830720, 10.150160),
    ("7. Clinique Taoufik", 36.832311, 10.154201),
    ("8. SONED", 36.835544, 10.160251),
    ("9. RX", 36.835486, 10.166438),
    ("10. Municipalite Mutuelleville", 36.833770, 10.167180),
]

for i in range(len(stops_retour) - 1):
    s1 = stops_retour[i]
    s2 = stops_retour[i+1]
    url = f"https://router.project-osrm.org/route/v1/driving/{s1[2]},{s1[1]};{s2[2]},{s2[1]}?overview=full&geometries=geojson&steps=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        route = data['routes'][0]
        print(f"\n--- Leg {s1[0]} -> {s2[0]} (Distance: {route['distance']:.0f}m) ---")
        for st in route['legs'][0]['steps']:
            name = st.get('name', 'unnamed')
            print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):12s} on '{name}' ({st['distance']:.0f}m)")

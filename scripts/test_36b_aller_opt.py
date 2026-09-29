import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p2 = (36.832290, 10.153931) # Clinique Taoufik Westbound (Aller)

# Test different coordinates for Terminus Ministere Aller
test_p1 = [
    ("Current Terminus", 36.829562, 10.159038),
    ("Terminus at West exit roundabout", 36.83000, 10.15750),
    ("Terminus at West exit Avenue Ligue", 36.83020, 10.15700),
    ("Terminus at Avenue Ligue Arabes", 36.83050, 10.15650),
    ("Terminus near Bouazizi interchange", 36.83100, 10.15550),
]

for name, lat, lon in test_p1:
    url = f"https://router.project-osrm.org/route/v1/driving/{lon},{lat};{p2[1]},{p2[0]}?overview=full&geometries=geojson&steps=true"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        data = json.loads(resp.read())
        r = data['routes'][0]
        uturns = [s for s in r['legs'][0]['steps'] if 'uturn' in str(s.get('maneuver'))]
        roundabouts = [s for s in r['legs'][0]['steps'] if 'roundabout' in str(s.get('maneuver'))]
        print(f"{name} ({lat}, {lon}) -> Dist: {r['distance']:.0f}m, steps: {len(r['legs'][0]['steps'])}, U-turns: {len(uturns)}, Roundabouts: {len(roundabouts)}")

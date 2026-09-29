import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Let's test routing from various points along northbound Klibi to Bouazizi westbound
# Klibi starts at (36.8370, 10.1658) and goes north to (36.8400, 10.1615)
for lat in [36.8370, 36.8375, 36.8380, 36.8385, 36.8390]:
    lon = 10.1658 - (lat - 36.8370) * 1.4 # approximate line of Klibi
    url = f"https://router.project-osrm.org/route/v1/driving/{lon},{lat};10.160991,36.836069?overview=false&steps=true"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        uturns = [s for s in r['legs'][0]['steps'] if 'uturn' in str(s.get('maneuver'))]
        print(f"Start ({lat:.4f}, {lon:.4f}) -> Dist: {r['distance']:.0f}m, U-turns: {len(uturns)}")

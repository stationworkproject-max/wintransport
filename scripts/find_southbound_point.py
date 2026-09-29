import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p11 = (36.835931, 10.160730)

# Search coordinates across the median to find the southbound carriageway of Mohieddine Klibi / ramp
for lat in [36.8385, 36.8388, 36.8390]:
    for lon in [10.1640, 10.1642, 10.1645, 10.1648]:
        url = f"https://router.project-osrm.org/route/v1/driving/{lon},{lat};{p11[1]},{p11[0]}?overview=false"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
                d = json.loads(resp.read())
                dist = d['routes'][0]['distance']
                print(f"({lat:.4f}, {lon:.4f}) -> SONED: {dist:.0f}m")
        except:
            pass

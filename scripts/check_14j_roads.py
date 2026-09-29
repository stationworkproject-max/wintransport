import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_14j = (36.823508, 10.141495)

# Query nearest to 14 Janvier 2011
url = f"https://router.project-osrm.org/nearest/v1/driving/{p_14j[1]},{p_14j[0]}?number=6"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    print("Nearest road points to 14 Janvier 2011:")
    for wp in data.get('waypoints', []):
        w_lat, w_lon = wp['location'][1], wp['location'][0]
        print(f"  ({w_lat:.6f}, {w_lon:.6f}) - dist={wp['distance']:.1f}m - name='{wp.get('name')}'")

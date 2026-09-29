import urllib.request
import json

# Check nearest road to (36.80905, 10.14710)
lat, lon = 36.80905, 10.14710
url = f"https://router.project-osrm.org/nearest/v1/driving/{lon},{lat}?number=5"
req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI-Debug'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        for wp in data.get('waypoints', []):
            name = wp.get('name', 'unnamed').encode('ascii', 'replace').decode()
            print(f"Dist: {wp['distance']:.1f}m, Road: {name}, Coords: {wp['location']}")
except Exception as e:
    print(e)

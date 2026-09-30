import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Query OSRM nearest for points along Route X near SONED (36.836, 10.160)
# Let's search a grid of points to find where Route X is
soned_lat = 36.836053
soned_lon = 10.160626

print("Searching for Route X carriageways near SONED...")
for dlat in [-0.001, -0.0005, 0.0, 0.0005, 0.001]:
    for dlon in [-0.001, -0.0005, 0.0, 0.0005, 0.001]:
        lat = soned_lat + dlat
        lon = soned_lon + dlon
        url = f"https://router.project-osrm.org/nearest/v1/driving/{lon},{lat}?number=1"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                wp = data['waypoints'][0]
                if 'محمد البوعزيزي' in wp.get('name', ''):
                    print(f"  Found Route X at ({wp['location'][1]}, {wp['location'][0]}) - query ({lat:.5f}, {lon:.5f}) dist={wp['distance']:.1f}m")
        except:
            pass

import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_cur = (36.829562, 10.159038)
p_dest = (36.831657, 10.152977) # Clinique Taoufik

# Query nearest to p_cur
url_near = f"https://router.project-osrm.org/nearest/v1/driving/{p_cur[1]},{p_cur[0]}?number=5"
with urllib.request.urlopen(urllib.request.Request(url_near, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    print("Nearest road points to Terminus Affaires Etrangeres:")
    for wp in data.get('waypoints', []):
        w_lat, w_lon = wp['location'][1], wp['location'][0]
        # test route from this point to Clinique Taoufik
        url_r = f"https://router.project-osrm.org/route/v1/driving/{w_lon},{w_lat};{p_dest[1]},{p_dest[0]}?overview=false"
        with urllib.request.urlopen(urllib.request.Request(url_r, headers={'User-Agent': 'Test'})) as r_resp:
            r_data = json.loads(r_resp.read())
            dist = r_data['routes'][0]['distance']
            print(f"  ({w_lat:.6f}, {w_lon:.6f}) - dist_snap={wp['distance']:.1f}m - route to Taoufik: {dist:.0f}m ({wp.get('name')})")

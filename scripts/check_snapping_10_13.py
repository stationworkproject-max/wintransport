import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

stops_aller = [
    ("10. RX", 36.838100, 10.165200),
    ("11. SONED", 36.835932, 10.160730),
    ("12. CLINIQUE TAOUFIK", 36.832431, 10.154153),
    ("13. FACULTE DE DROIT", 36.830720, 10.150380),
]

for name, lat, lon in stops_aller:
    url = f"https://router.project-osrm.org/nearest/v1/driving/{lon},{lat}?number=3"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(f"\n{name} ({lat}, {lon}):")
        for wp in data.get('waypoints', []):
            st_name = ''.join([c for c in wp.get('name', '') if ord(c) < 128])
            print(f"  -> snapped to ({wp['location'][1]:.6f}, {wp['location'][0]:.6f}) on '{st_name}', dist = {wp['distance']:.1f}m")

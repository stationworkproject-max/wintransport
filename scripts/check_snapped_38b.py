import urllib.request
import json

pts = [
    ("10 RX", 36.838561, 10.166151),
    ("11 SONED", 36.835735, 10.160893),
    ("12 CLINIQUE TAOUFIK", 36.832491, 10.154094),
    ("13 FACULTE DE DROIT", 36.83072, 10.15038)
]

for name, lat, lon in pts:
    url = f"https://router.project-osrm.org/nearest/v1/driving/{lon},{lat}?number=3"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(f"\n--- {name} at ({lat}, {lon}) ---")
        for wp in data.get('waypoints', []):
            w_name = ''.join([c for c in wp.get('name', 'unnamed') if ord(c) < 128])
            print(f"  snapped to '{w_name}' dist={wp.get('distance'):.1f}m loc={wp.get('location')}")

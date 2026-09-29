import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p9 = (36.833778, 10.167208) # Mutuelleville
# Test different points along direct route
test_pts = [
    ("Pt 10 (Jugurtha)", 36.836675, 10.165930),
    ("Pt 15 (Jugurtha/Klibi)", 36.837743, 10.165452),
    ("Pt 18 (Klibi ramp start)", 36.838295, 10.165036),
    ("Pt 60 (Ramp merge)", 36.838018, 10.164095),
]
p11 = (36.836069, 10.160991) # SONED

for name, lat, lon in test_pts:
    url = f"https://router.project-osrm.org/route/v1/driving/{p9[1]},{p9[0]};{lon},{lat};{p11[1]},{p11[0]}?overview=false"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        legs = r['legs']
        print(f"{name}: Total {r['distance']:.0f}m | Leg 9->10: {legs[0]['distance']:.0f}m, Leg 10->11: {legs[1]['distance']:.0f}m")

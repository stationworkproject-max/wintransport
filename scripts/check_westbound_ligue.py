import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_taoufik = (36.831657, 10.152977)

# Check points along Avenue de la Ligue des Etats Arabes near the Ministry of Foreign Affairs
# (lat 36.8295 to 36.8305, lon 10.1580 to 10.1600)
for lat, lon in [
    (36.82970, 10.15850),
    (36.82980, 10.15800),
    (36.83000, 10.15750),
    (36.83050, 10.15700),
    (36.82944, 10.16082),
    (36.82886, 10.16612),
]:
    url = f"https://router.project-osrm.org/route/v1/driving/{lon},{lat};{p_taoufik[1]},{p_taoufik[0]}?overview=false"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"({lat:.5f}, {lon:.5f}) -> Taoufik: {r['distance']:.0f}m")

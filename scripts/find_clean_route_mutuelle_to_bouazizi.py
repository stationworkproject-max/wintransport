import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_mutuelle = (36.833778, 10.167208)
p_soned = (36.835931, 10.160730)

# Check various routes from around Mutuelleville to SONED
# Try different starting nodes near Mutuelleville
for name, lat, lon in [
    ("Jugurtha current", 36.833778, 10.167208),
    ("Rue Khaled Ibn Walid", 36.83312, 10.16746),
    ("Rue Azzouz Rebai", 36.83797, 10.16380),
    ("Rue Charles de Gaulle / Mutuelleville", 36.83400, 10.16500),
    ("Jugurtha north", 36.83600, 10.16620),
    ("Avenue Taoufik / Ligue", 36.82886, 10.16612),
]:
    url = f"https://router.project-osrm.org/route/v1/driving/{lon},{lat};{p_soned[1]},{p_soned[0]}?overview=false"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"{name:35s}: distance = {r['distance']:.0f}m")

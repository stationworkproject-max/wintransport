import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Look at points along Avenue Jugurtha heading north towards the interchange:
# (36.833778, 10.167208) is Mutuelleville
# (36.835486, 10.166438) is Jugurtha near bridge
# (36.837500, 10.165500) is Jugurtha ramp

for lat, lon, desc in [
    (36.835486, 10.166438, "Jugurtha RX retour"),
    (36.836500, 10.166000, "Jugurtha mid"),
    (36.837200, 10.165500, "Jugurtha interchange entry"),
    (36.837944, 10.165321, "Bouazizi merge westbound"),
]:
    url = f"https://router.project-osrm.org/route/v1/driving/10.167208,36.833778;{lon},{lat};10.160730,36.835931?overview=false"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            r = data['routes'][0]
            print(f"{desc:30s} -> Total dist: {r['distance']:.0f}m | leg1: {r['legs'][0]['distance']:.0f}m, leg2: {r['legs'][1]['distance']:.0f}m")
    except Exception as e:
        print(f"{desc}: error {e}")

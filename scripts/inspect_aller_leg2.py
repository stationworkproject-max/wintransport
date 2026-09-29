import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_taoufik = (36.831696, 10.152933)
# In 36B Aller, Campus was:
p_campus_aller = (36.825369, 10.143889) # Westbound Campus
# But earlier we tested with p_campus = (36.825350, 10.144100) which is Eastbound Campus!
# An Eastbound campus forces a car going Westbound to turn all the way around!
url = f"https://router.project-osrm.org/route/v1/driving/{p_taoufik[1]},{p_taoufik[0]};{p_campus_aller[1]},{p_campus_aller[0]}?overview=false&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    d = json.loads(resp.read())
    r = d['routes'][0]
    print(f"Dist from Taoufik to Campus Aller (Westbound): {r['distance']:.0f}m")
    for s in r['legs'][0]['steps']:
        mod = f" ({s['maneuver'].get('modifier')})" if s['maneuver'].get('modifier') else ""
        print(f"  {s['maneuver']['type']}{mod:15s} on '{s.get('name')}' ({s['distance']:.0f}m)")

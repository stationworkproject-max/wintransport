import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_pasteur = (36.823094, 10.177674)
p_zouiten = (36.829621, 10.170550)
p_mutuelle = (36.833778, 10.167208)
p_soned = (36.835931, 10.160730)

# Check route from p_mutuelle to p_soned:
# What if we route from p_mutuelle to Azzouz Rebai to Bouazizi?
# Azzouz Rebai is around (36.834, 10.164)
for pt_lat, pt_lon, name in [
    (36.833778, 10.167208, "p_mutuelle (Jugurtha)"),
    (36.8350, 10.1640, "Rue Azzouz Rebai"),
    (36.8360, 10.1630, "Rue Azzouz Rebai north"),
    (36.8375, 10.1625, "Rue Azzouz Rebai interchange"),
]:
    url = f"https://router.project-osrm.org/route/v1/driving/{pt_lon},{pt_lat};{p_soned[1]},{p_soned[0]}?overview=false&steps=true"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        uturns = [s for s in r['legs'][0]['steps'] if 'uturn' in str(s.get('maneuver'))]
        print(f"From {name}: Dist: {r['distance']:.0f}m, U-turns: {len(uturns)}")
        for s in r['legs'][0]['steps']:
            if s['distance'] > 50:
                print(f"    {s['maneuver']['type']} ({s['maneuver'].get('modifier', '')}) on '{s.get('name')}' ({s['distance']:.0f}m)")

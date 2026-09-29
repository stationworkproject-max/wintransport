import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p7 = (36.825112, 10.143985) # Campus in 36B Retour
p8 = (36.832198, 10.154312) # Clinique Taoufik in 36B Retour

url = f"https://router.project-osrm.org/route/v1/driving/{p7[1]},{p7[0]};{p8[1]},{p8[0]}?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    r = data['routes'][0]
    print(f"Distance p7 -> p8: {r['distance']:.0f}m")
    for s in r['legs'][0]['steps']:
        print(f"  {s['maneuver']['type']} ({s['maneuver'].get('modifier', '')}) on '{s.get('name')}' ({s['distance']:.0f}m)")

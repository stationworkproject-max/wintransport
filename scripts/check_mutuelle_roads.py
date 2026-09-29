import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_zouiten = (36.829621, 10.170550) # Station 8: Chedly Zouiten
p_mutuelle = (36.833778, 10.167208) # Station 9: Municipalite Mutuelleville
p_soned = (36.835931, 10.160730)

# Check route from Zouiten to Mutuelleville
url = f"https://router.project-osrm.org/route/v1/driving/{p_zouiten[1]},{p_zouiten[0]};{p_mutuelle[1]},{p_mutuelle[0]}?overview=full&steps=true"
req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    route = data['routes'][0]
    print(f"Zouiten -> Mutuelleville: {route['distance']:.0f}m")
    for st in route['legs'][0]['steps']:
        print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):12s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

# Check what roads connect around Mutuelleville (36.833778, 10.167208)
url_near = f"https://router.project-osrm.org/nearest/v1/driving/{p_mutuelle[1]},{p_mutuelle[0]}?number=6"
req_near = urllib.request.Request(url_near, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req_near) as resp:
    data = json.loads(resp.read())
    print("\nRoads near Mutuelleville:")
    for wp in data.get('waypoints', []):
        print(f"  ({wp['location'][1]:.6f}, {wp['location'][0]:.6f}) dist={wp['distance']:.1f}m name='{wp.get('name')}'")

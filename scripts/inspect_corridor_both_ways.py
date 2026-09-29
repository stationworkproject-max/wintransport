import urllib.request
import json

# Let's inspect the two directions between Faculte de Droit and Chedly Zouiten / Mutuelleville:
c_droit = (36.83072, 10.15038)
c_mutuelle = (36.833778, 10.167208)

# West to East (Retour): Droit -> Mutuelleville
url_we = f"https://router.project-osrm.org/route/v1/driving/{c_droit[1]},{c_droit[0]};{c_mutuelle[1]},{c_mutuelle[0]}?overview=full&geometries=geojson&steps=true"
req_we = urllib.request.Request(url_we, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req_we) as resp:
    data_we = json.loads(resp.read())
    r_we = data_we['routes'][0]
    print(f"=== RETOUR (Faculte de Droit -> Mutuelleville): {r_we['distance']:.0f}m ===")
    for s in r_we['legs'][0]['steps']:
        name = ''.join([c for c in s.get('name', '') if ord(c) < 128])
        print(f"  {s['maneuver']['type']} {s['maneuver'].get('modifier', '')} on '{name}' ({s['distance']:.0f}m)")

# East to West (Aller): Mutuelleville -> Faculte de Droit
url_ew = f"https://router.project-osrm.org/route/v1/driving/{c_mutuelle[1]},{c_mutuelle[0]};{c_droit[1]},{c_droit[0]}?overview=full&geometries=geojson&steps=true"
req_ew = urllib.request.Request(url_ew, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req_ew) as resp:
    data_ew = json.loads(resp.read())
    r_ew = data_ew['routes'][0]
    print(f"\n=== ALLER (Mutuelleville -> Faculte de Droit): {r_ew['distance']:.0f}m ===")
    for s in r_ew['legs'][0]['steps']:
        name = ''.join([c for c in s.get('name', '') if ord(c) < 128])
        print(f"  {s['maneuver']['type']} {s['maneuver'].get('modifier', '')} on '{name}' ({s['distance']:.0f}m)")

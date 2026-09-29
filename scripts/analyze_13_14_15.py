import urllib.request
import json

c13 = "10.14529,36.80390"
c14 = "10.14710,36.80905"
c15 = "10.13838,36.80689"

# Route 13 -> 14 -> 15
url = f"https://router.project-osrm.org/route/v1/driving/{c13};{c14};{c15}?overview=full&geometries=geojson&steps=true"
req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI-Debug'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        r = data['routes'][0]
        print(f"Total distance 13->14->15: {r['distance']:.1f} m")
        for leg_idx, leg in enumerate(r['legs']):
            print(f"--- Leg {leg_idx + 1} ({leg['distance']:.1f} m) ---")
            for step in leg['steps']:
                name = step.get('name', 'unnamed').encode('ascii', 'replace').decode()
                print(f"  {step['maneuver']['type']} {step['maneuver'].get('modifier', '')} on {name} ({step['distance']:.1f} m)")
except Exception as e:
    print("Error:", e)

# Now what if 13 -> 15 directly?
url_direct = f"https://router.project-osrm.org/route/v1/driving/{c13};{c15}?overview=full&geometries=geojson"
req_dir = urllib.request.Request(url_direct, headers={'User-Agent': 'WhereAmI-Debug'})
try:
    with urllib.request.urlopen(req_dir) as resp:
        data = json.loads(resp.read())
        r = data['routes'][0]
        print(f"\nDirect distance 13->15: {r['distance']:.1f} m")
except Exception as e:
    print("Error:", e)

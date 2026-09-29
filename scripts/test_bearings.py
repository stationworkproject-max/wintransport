import urllib.request
import json
import math

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return round(compass_bearing)

c13 = (36.80390, 10.14529)
c14 = (36.80905, 10.14710)
c15 = (36.80689, 10.13838)

b13 = calculate_bearing(c13[0], c13[1], c14[0], c14[1])
b14 = calculate_bearing(c13[0], c13[1], c15[0], c15[1])
b15 = calculate_bearing(c14[0], c14[1], c15[0], c15[1])

print(f"Bearings: b13={b13}, b14={b14}, b15={b15}")

coords_str = f"{c13[1]},{c13[0]};{c14[1]},{c14[0]};{c15[1]},{c15[0]}"
bearings_str = f"{b13},90;{b14},90;{b15},90"

url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson&bearings={bearings_str}"
req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI-Debug'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        r = data['routes'][0]
        print(f"Route with bearings: distance={r['distance']:.1f} m")
except Exception as e:
    print("Error with bearings:", e)

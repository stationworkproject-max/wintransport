import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Query OSRM nearest to find the two carriageways at different longitudes along Bouazizi
# Longitudes: 10.166 (RX), 10.160 (SONED), 10.154 (Clinique Taoufik), 10.150 (Faculte de Droit), 10.144 (Campus / 14 Janvier)

longitudes = [
    ("RX area", 10.1660, 36.8365),
    ("SONED area", 10.1608, 36.8359),
    ("Taoufik area", 10.1542, 36.8323),
    ("Droit area", 10.1503, 36.8307),
    ("Campus area", 10.1440, 36.8252),
    ("14 Janvier area", 10.1416, 36.8235),
]

# Let's route west from 10.166 to 10.141 along Bouazizi
west_url = "https://router.project-osrm.org/route/v1/driving/10.1660,36.8365;10.1416,36.8235?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(west_url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    r = data['routes'][0]
    print(f"Direct Westbound route: {r['distance']:.0f}m")
    coords_west = r['geometry']['coordinates']

# Let's route east from 10.141 to 10.166 along Bouazizi
east_url = "https://router.project-osrm.org/route/v1/driving/10.1416,36.8235;10.1660,36.8365?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(east_url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    r = data['routes'][0]
    print(f"Direct Eastbound route: {r['distance']:.0f}m")
    coords_east = r['geometry']['coordinates']

print(f"\nWestbound polyline points: {len(coords_west)}")
print(f"Eastbound polyline points: {len(coords_east)}")

# Function to find closest point on polyline to a target (lat, lon)
def closest_on_line(target_lat, target_lon, poly):
    best_dist = 1e9
    best_pt = None
    for p in poly:
        # p is [lon, lat]
        d = ((p[1]-target_lat)**2 + (p[0]-target_lon)**2)**0.5
        if d < best_dist:
            best_dist = d
            best_pt = p
    return best_pt[1], best_pt[0]

print("\n--- Projecting Stations to Westbound Carriageway (Aller) ---")
for name, lat, lon in [
    ("SONED", 36.836053, 10.160626),
    ("Clinique Taoufik", 36.832198, 10.154312),
    ("Faculte de Droit", 36.830720, 10.150380),
    ("Campus", 36.825369, 10.143889),
    ("14 Janvier", 36.823508, 10.141495)
]:
    clat, clon = closest_on_line(lat, lon, coords_west)
    print(f"  {name:20s}: ({clat:.6f}, {clon:.6f})")

print("\n--- Projecting Stations to Eastbound Carriageway (Retour) ---")
for name, lat, lon in [
    ("14 Janvier", 36.823508, 10.141495),
    ("Campus", 36.825369, 10.143889),
    ("Faculte de Droit", 36.830720, 10.150380),
    ("Clinique Taoufik", 36.832198, 10.154312),
    ("SONED", 36.836053, 10.160626),
]:
    clat, clon = closest_on_line(lat, lon, coords_east)
    print(f"  {name:20s}: ({clat:.6f}, {clon:.6f})")

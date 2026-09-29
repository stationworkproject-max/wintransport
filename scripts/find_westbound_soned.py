import urllib.request
import json

# Bearing from 10 (RX, 36.8385, 10.1661) to 12 (Taoufik, 36.8325, 10.1541)
# Delta lat is negative, delta lon is negative -> heading South-West (~240 degrees)!

# Let's query OSRM route from 10 to 12 directly (which goes along the westbound carriageway)
c10 = (36.838561, 10.166151)
c12 = (36.832491, 10.154094)

url = f"https://router.project-osrm.org/route/v1/driving/{c10[1]},{c10[0]};{c12[1]},{c12[0]}?overview=full&geometries=geojson"
req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    coords = [(c[1], c[0]) for c in data['routes'][0]['geometry']['coordinates']]
    print(f"Direct 10 -> 12 distance: {data['routes'][0]['distance']:.0f}m ({len(coords)} points)")
    
    # Let's find the point on this direct route that is closest to 11 (SONED, 36.835735, 10.160893)
    c11_orig = (36.835735, 10.160893)
    import math
    def dist(p1, p2):
        return 6371000 * math.sqrt(math.radians(p2[0]-p1[0])**2 + (math.radians(p2[1]-p1[1])*math.cos(math.radians(p1[0])))**2)
        
    closest_pt = min(coords, key=lambda p: dist(p, c11_orig))
    print(f"Original SONED: {c11_orig}")
    print(f"Closest point on direct 10->12 corridor: {closest_pt} (distance: {dist(closest_pt, c11_orig):.1f}m)")

# Now test routing 10 -> closest_pt -> 12 -> 13
c13 = (36.83072, 10.15038)
pts = [c10, closest_pt, c12, c13]
coords_str = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in pts])
url2 = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=false"
req2 = urllib.request.Request(url2, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req2) as resp2:
    data2 = json.loads(resp2.read())
    print(f"\nTotal distance with corridor-snapped SONED: {data2['routes'][0]['distance']:.0f}m")
    for i, leg in enumerate(data2['routes'][0]['legs']):
        print(f"  Leg {i+10}->{i+11}: {leg['distance']:.0f}m")

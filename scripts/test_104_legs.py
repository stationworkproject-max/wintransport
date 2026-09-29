import json
import urllib.request
import math

def get_distance(p1, p2):
    R = 6371000
    dLat = math.radians(p2[0] - p1[0])
    dLon = math.radians(p2[1] - p1[1])
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(p1[0])) * math.cos(math.radians(p2[0])) * math.sin(dLon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def osrm_route(points):
    # points are list of (lat, lon)
    coords_str = ";".join([f"{p[1]:.5f},{p[0]:.5f}" for p in points])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI-Transit-Processor'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        if data.get('code') != 'Ok' or not data.get('routes'):
            return None, 0
        r = data['routes'][0]
        pts = [(c[1], c[0]) for c in r['geometry']['coordinates']]
        return pts, r['distance']

# Load 104 Aller from GeoJSON
data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
feat = data['features']
line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]
num_key = [k for k in feat[0]['properties'] if 'station' in k.lower() and 'nom' not in k.lower()][0]
name_key = [k for k in feat[0]['properties'] if 'nom' in k.lower()][0]

stops_104 = [f for f in feat if str(f['properties'][line_key]).strip() == '104']
stops_104.sort(key=lambda f: f['properties'][num_key])

# 1. Remove obvious outlier spike: Stop 7 (Gouvernorat Manouba in the middle of Tunis stops)
clean_stops = []
for i, f in enumerate(stops_104):
    p = f['properties']
    c = (f['geometry']['coordinates'][1], f['geometry']['coordinates'][0])
    name = p[name_key]
    num = p[num_key]
    
    # Check outlier
    if num == 7 and 'gouvernorat' in name.lower():
        print(f"Skipping misplaced stop {num}: {name} from position {i+1}")
        continue
    clean_stops.append((num, name, c[0], c[1]))

print(f"Cleaned stops count: {len(clean_stops)}")

# Now test routing stop by stop and detect if any stop causes a huge U-turn loop
final_route = []
total_dist = 0

# Check legs between stops
for i in range(len(clean_stops) - 1):
    s_curr = clean_stops[i]
    s_next = clean_stops[i+1]
    
    p_curr = (s_curr[2], s_curr[3])
    p_next = (s_next[2], s_next[3])
    
    direct_pts, d_direct = osrm_route([p_curr, p_next])
    straight_d = get_distance(p_curr, p_next)
    
    ratio = d_direct / max(straight_d, 50)
    print(f"Leg {i+1}->{i+2} ({s_curr[1][:15]} -> {s_next[1][:15]}): straight={straight_d:.0f}m, routed={d_direct:.0f}m, ratio={ratio:.2f}")


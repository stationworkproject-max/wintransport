import json
import urllib.request
import math
from collections import defaultdict

def get_distance(p1, p2):
    R = 6371000
    dLat = math.radians(p2[0] - p1[0])
    dLon = math.radians(p2[1] - p1[1])
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(p1[0])) * math.cos(math.radians(p2[0])) * math.sin(dLon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def project_point_onto_segment(p, a, b):
    cos_lat = math.cos(math.radians(a[0]))
    m_per_deg_lat = 111132
    m_per_deg_lon = 111132 * cos_lat
    
    ax, ay = a[1] * m_per_deg_lon, a[0] * m_per_deg_lat
    bx, by = b[1] * m_per_deg_lon, b[0] * m_per_deg_lat
    px, py = p[1] * m_per_deg_lon, p[0] * m_per_deg_lat
    
    dx = bx - ax
    dy = by - ay
    len_sq = dx * dx + dy * dy
    if len_sq == 0:
        return a
        
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len_sq))
    return (ay + t * dy) / m_per_deg_lat, (ax + t * dx) / m_per_deg_lon

def project_point_onto_polyline(p, polyline):
    best_dist = float('inf')
    best_proj = p
    for i in range(len(polyline) - 1):
        proj = project_point_onto_segment(p, polyline[i], polyline[i+1])
        d = get_distance(p, proj)
        if d < best_dist:
            best_dist = d
            best_proj = proj
    return best_proj, best_dist

def osrm_route(points):
    coords_str = ";".join([f"{p[1]:.5f},{p[0]:.5f}" for p in points])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI-Transit-Engine/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data.get('code') != 'Ok' or not data.get('routes'):
                return None, 0
            r = data['routes'][0]
            pts = [(c[1], c[0]) for c in r['geometry']['coordinates']]
            return pts, r['distance']
    except Exception as e:
        return None, 0

# Test clean routing algorithm on Bus 104 Aller and Retour
data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
feat = data['features']
line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]
num_key = [k for k in feat[0]['properties'] if 'station' in k.lower() and 'nom' not in k.lower()][0]
name_key = [k for k in feat[0]['properties'] if 'nom' in k.lower()][0]

stops_104_aller = [f for f in feat if str(f['properties'][line_key]).strip() == '104']
stops_104_aller.sort(key=lambda f: f['properties'][num_key])

stops_104_retour = [f for f in feat if str(f['properties'][line_key]).strip() == '104 (Retour)']
stops_104_retour.sort(key=lambda f: f['properties'][num_key])

def clean_and_route_line(stops_list, is_retour=False, reverse_if_needed=True):
    raw_stops = []
    for f in stops_list:
        p = f['properties']
        coords = f['geometry']['coordinates']
        raw_stops.append({
            'num': p[num_key],
            'name': p[name_key],
            'lat': coords[1],
            'lon': coords[0]
        })
        
    # Check sequence orientation for retour:
    # If first stop is near Tunis Marine and last stop is Khaireddine Mannouba, reverse it
    if is_retour and reverse_if_needed and len(raw_stops) > 1:
        d_start_marine = get_distance((raw_stops[0]['lat'], raw_stops[0]['lon']), (36.80038, 10.19039))
        d_end_marine = get_distance((raw_stops[-1]['lat'], raw_stops[-1]['lon']), (36.80038, 10.19039))
        if d_start_marine < 2000 and d_end_marine > 5000:
            print("  Reversing Retour stops so it starts at suburban terminus and heads to Tunis Marine")
            raw_stops = list(reversed(raw_stops))
            
    # 1. Filter outlier coordinate jumps
    clean = []
    for i, s in enumerate(raw_stops):
        if 0 < i < len(raw_stops) - 1:
            prev_s = raw_stops[i-1]
            next_s = raw_stops[i+1]
            d_prev = get_distance((prev_s['lat'], prev_s['lon']), (s['lat'], s['lon']))
            d_next = get_distance((s['lat'], s['lon']), (next_s['lat'], next_s['lon']))
            d_direct = get_distance((prev_s['lat'], prev_s['lon']), (next_s['lat'], next_s['lon']))
            if d_prev > 2500 and d_next > 2500 and d_direct < 1500:
                print(f"  Removing outlier stop {s['num']}: {s['name']} (jump={d_prev:.0f}m)")
                continue
        clean.append(s)
        
    print(f"  Stops: {len(raw_stops)} -> {len(clean)} clean stops")
    
    # 2. Check each triplet for opposite-road U-turn loops
    # If routing A -> B -> C causes > 1.7x direct distance A -> C:
    # Project B onto direct path A -> C
    adjusted_coords = [(s['lat'], s['lon']) for s in clean]
    for i in range(1, len(clean) - 1):
        p_prev = adjusted_coords[i-1]
        p_curr = adjusted_coords[i]
        p_next = adjusted_coords[i+1]
        
        # Test direct route
        direct_pts, d_direct = osrm_route([p_prev, p_next])
        if direct_pts and d_direct > 0:
            via_pts, d_via = osrm_route([p_prev, p_curr, p_next])
            if via_pts and d_via > 1.7 * d_direct and d_via > d_direct + 400:
                # B is on opposite carriageway or side loop causing roundabout U-turn!
                proj_pt, dist_to_road = project_point_onto_polyline(p_curr, direct_pts)
                print(f"  Opposite road U-turn detected at stop {clean[i]['num']} ({clean[i]['name']})! Detour: {d_via:.0f}m vs direct {d_direct:.0f}m. Projecting onto road (offset {dist_to_road:.0f}m).")
                adjusted_coords[i] = proj_pt
                
    # 3. Final OSRM route with adjusted coords in chunks of 20
    final_shape = []
    chunk_size = 20
    for c_start in range(0, len(adjusted_coords) - 1, chunk_size - 1):
        c_end = min(c_start + chunk_size, len(adjusted_coords))
        chunk_pts = adjusted_coords[c_start:c_end]
        pts, dist = osrm_route(chunk_pts)
        if pts:
            if final_shape:
                pts = pts[1:]
            final_shape.extend(pts)
            
    return clean, adjusted_coords, final_shape

print("=== Testing 104 Aller ===")
clean_a, adj_a, shape_a = clean_and_route_line(stops_104_aller, is_retour=False)
print(f"104 Aller shape points: {len(shape_a)}")

print("\n=== Testing 104 Retour ===")
clean_r, adj_r, shape_r = clean_and_route_line(stops_104_retour, is_retour=True)
print(f"104 Retour shape points: {len(shape_r)}")

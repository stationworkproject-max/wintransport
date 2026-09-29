import json
import urllib.request
import math

def get_distance(p1, p2):
    R = 6371000
    dLat = math.radians(p2[0] - p1[0])
    dLon = math.radians(p2[1] - p1[1])
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(p1[0])) * math.cos(math.radians(p2[0])) * math.sin(dLon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def project_point_onto_polyline(pt, polyline):
    # Find closest point on polyline to pt
    best_pt = None
    min_d = float('inf')
    for i in range(len(polyline) - 1):
        a = polyline[i]
        b = polyline[i+1]
        
        cos_lat = math.cos(math.radians(a[0]))
        m_per_deg_lat = 111132
        m_per_deg_lon = 111132 * cos_lat
        ax, ay = a[1] * m_per_deg_lon, a[0] * m_per_deg_lat
        bx, by = b[1] * m_per_deg_lon, b[0] * m_per_deg_lat
        px, py = pt[1] * m_per_deg_lon, pt[0] * m_per_deg_lat
        
        dx = bx - ax
        dy = by - ay
        len_sq = dx * dx + dy * dy
        if len_sq == 0:
            proj = a
        else:
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len_sq))
            proj = ((ay + t * dy) / m_per_deg_lat, (ax + t * dx) / m_per_deg_lon)
            
        d = get_distance(pt, proj)
        if d < min_d:
            min_d = d
            best_pt = proj
    return best_pt, min_d

# Load 38B from staticTransit.js
with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
idx = text.find('export const STATIC_LINES = ')
lines = json.loads(text[idx + len('export const STATIC_LINES = '):].strip()[:-1])
bus_38b = [l for l in lines if l['short_name'] == '38B'][0]

print("=== TESTING 38B RETOUR CORRIDOR SNAPPING ===")
raw_stops = bus_38b['stops_retour']
coords = [(s['lat'], s['lon']) for s in raw_stops]

# Original distance
coords_str = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in coords])
url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=false"
req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    orig_dist = data['routes'][0]['distance']
    legs = data['routes'][0]['legs']

print(f"Original total distance: {orig_dist:.0f}m")

# Let's inspect Section 1: Stop 6 (Faculte de Droit) to Stop 10 (Mutuelleville)
# Direct route 6 -> 10:
c6 = coords[5] # index 5 is stop 6
c10 = coords[9] # index 9 is stop 10
url_c1 = f"https://router.project-osrm.org/route/v1/driving/{c6[1]:.5f},{c6[0]:.5f};{c10[1]:.5f},{c10[0]:.5f}?overview=full&geometries=geojson"
req_c1 = urllib.request.Request(url_c1, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req_c1) as resp:
    poly_c1 = [(c[1], c[0]) for c in json.loads(resp.read())['routes'][0]['geometry']['coordinates']]

# Section 2: Stop 11 (Chedly Zouiten) to Stop 18 (Terminus Tunis Marine)
c11 = coords[10]
c18 = coords[17]
url_c2 = f"https://router.project-osrm.org/route/v1/driving/{c11[1]:.5f},{c11[0]:.5f};{c18[1]:.5f},{c18[0]:.5f}?overview=full&geometries=geojson"
req_c2 = urllib.request.Request(url_c2, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req_c2) as resp:
    poly_c2 = [(c[1], c[0]) for c in json.loads(resp.read())['routes'][0]['geometry']['coordinates']]

# Snap intermediate stops:
clean_coords = list(coords)

# Snap stops 7, 8, 9 onto poly_c1
for idx in [6, 7, 8]:
    pt, d = project_point_onto_polyline(coords[idx], poly_c1)
    clean_coords[idx] = (round(pt[0], 6), round(pt[1], 6))
    print(f"  Snapped Stop {idx+1} ({raw_stops[idx]['name'][:15]}): moved {d:.1f}m onto corridor")

# Snap stops 12, 13, 14, 15, 16, 17 onto poly_c2
for idx in [11, 12, 13, 14, 15, 16]:
    pt, d = project_point_onto_polyline(coords[idx], poly_c2)
    clean_coords[idx] = (round(pt[0], 6), round(pt[1], 6))
    print(f"  Snapped Stop {idx+1} ({raw_stops[idx]['name'][:15]}): moved {d:.1f}m onto corridor")

# Route clean coords:
coords_str_clean = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in clean_coords])
url_clean = f"https://router.project-osrm.org/route/v1/driving/{coords_str_clean}?overview=false"
req_clean = urllib.request.Request(url_clean, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req_clean) as resp:
    data_clean = json.loads(resp.read())
    clean_dist = data_clean['routes'][0]['distance']
    clean_legs = data_clean['routes'][0]['legs']

print(f"\nFinal Cleaned Retour distance: {clean_dist:.0f}m (SAVED {orig_dist - clean_dist:.0f}m!)")
print(f"Total distance reduced from {orig_dist/1000:.2f}km to {clean_dist/1000:.2f}km!")

# Check remaining detours
for i, leg in enumerate(clean_legs):
    st = get_distance(clean_coords[i], clean_coords[i+1])
    r = leg['distance'] / max(st, 30)
    flag = " *** DETOUR ***" if r > 1.45 and leg['distance'] > st + 250 else ""
    print(f"  Leg {i+1}->{i+2}: straight {st:.0f}m, routed {leg['distance']:.0f}m ({r:.2f}x){flag}")

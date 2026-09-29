import urllib.request
import json
import math

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

# Load 104 Aller stops
data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
feat = data['features']
stops_104 = [f for f in feat if str(f['properties'].get('N_de_la_ligne') or list(f['properties'].values())[1]).strip() == '104']
num_key = [k for k in feat[0]['properties'] if 'station' in k.lower() and 'nom' not in k.lower()][0]
name_key = [k for k in feat[0]['properties'] if 'nom' in k.lower()][0]

stops_104.sort(key=lambda f: f['properties'][num_key])
clean = []
for f in stops_104:
    p = f['properties']
    c = (f['geometry']['coordinates'][1], f['geometry']['coordinates'][0])
    if p[num_key] == 7 and 'gouvernorat' in p[name_key].lower():
        continue
    clean.append({'num': p[num_key], 'name': p[name_key], 'lat': c[0], 'lon': c[1]})

print(f"Stops count: {len(clean)}")

# Route chunk
coords = [(s['lat'], s['lon']) for s in clean]
coords_str = ";".join([f"{p[1]:.5f},{p[0]:.5f}" for p in coords])
url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
req = urllib.request.Request(url, headers={'User-Agent': 'FastTest'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    r = data['routes'][0]
    print(f"Initial total distance: {r['distance']:.1f} m")
    legs = r['legs']
    for i, leg in enumerate(legs):
        straight = get_distance(coords[i], coords[i+1])
        ratio = leg['distance'] / max(straight, 30)
        if ratio > 1.8 and leg['distance'] > straight + 350:
            print(f"  Flagged leg {i} -> {i+1} ({clean[i]['name'][:15]} -> {clean[i+1]['name'][:15]}): straight={straight:.0f}m, routed={leg['distance']:.0f}m, ratio={ratio:.2f}")


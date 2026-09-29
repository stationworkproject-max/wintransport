import json
import urllib.request
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
    if len_sq == 0: return a
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len_sq))
    return (ay + t * dy) / m_per_deg_lat, (ax + t * dx) / m_per_deg_lon

with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
idx = text.find('export const STATIC_LINES = ')
lines = json.loads(text[idx + len('export const STATIC_LINES = '):].strip()[:-1])
bus_38b = [l for l in lines if l['short_name'] == '38B'][0]

coords_aller = [(s['lat'], s['lon']) for s in bus_38b['stops']]

# Let's inspect routing before projection:
coords_str = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in coords_aller])
url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=false"
req = urllib.request.Request(url, headers={'User-Agent': 'Test38B'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    dist1 = data['routes'][0]['distance']
    legs = data['routes'][0]['legs']

print(f"Original 38B Aller total distance: {dist1:.0f}m")
for i in [9, 10, 11]:
    st = get_distance(coords_aller[i], coords_aller[i+1])
    print(f"  Leg {i+1}->{i+2} ({bus_38b['stops'][i]['name'][:15]} -> {bus_38b['stops'][i+1]['name'][:15]}): straight={st:.0f}m, routed={legs[i]['distance']:.0f}m, ratio={legs[i]['distance']/st:.2f}")

# Now what if stop 11 (SONED, index 10) is projected onto segment between 10 (RX) and 12 (Clinique Taoufik)?
coords_aller_proj = list(coords_aller)
proj_11 = project_point_onto_segment(coords_aller[10], coords_aller[9], coords_aller[11])
coords_aller_proj[10] = (round(proj_11[0], 5), round(proj_11[1], 5))

coords_str2 = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in coords_aller_proj])
url2 = f"https://router.project-osrm.org/route/v1/driving/{coords_str2}?overview=false"
req2 = urllib.request.Request(url2, headers={'User-Agent': 'Test38B'})
with urllib.request.urlopen(req2) as resp2:
    data2 = json.loads(resp2.read())
    dist2 = data2['routes'][0]['distance']
    legs2 = data2['routes'][0]['legs']

print(f"\nAfter projecting Stop 11 (SONED): total distance: {dist2:.0f}m (saved {dist1 - dist2:.0f}m!)")
for i in [9, 10, 11]:
    st = get_distance(coords_aller_proj[i], coords_aller_proj[i+1])
    print(f"  Leg {i+1}->{i+2}: straight={st:.0f}m, routed={legs2[i]['distance']:.0f}m, ratio={legs2[i]['distance']/st:.2f}")

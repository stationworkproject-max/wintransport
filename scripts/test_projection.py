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
    # p, a, b are (lat, lon)
    # convert to local flat coordinates (meters)
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
        
    t = ((px - ax) * dx + (py - ay) * dy) / len_sq
    t = max(0.0, min(1.0, t))
    
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    
    proj_lat = proj_y / m_per_deg_lat
    proj_lon = proj_x / m_per_deg_lon
    return (proj_lat, proj_lon)

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

# Test stops 13, 14, 15
c13 = (36.80390, 10.14529)
c14 = (36.80905, 10.14710)
c15 = (36.80689, 10.13838)

# 1. Direct route 13 -> 15
url_direct = f"https://router.project-osrm.org/route/v1/driving/{c13[1]},{c13[0]};{c15[1]},{c15[0]}?overview=full&geometries=geojson"
req = urllib.request.Request(url_direct, headers={'User-Agent': 'WhereAmI-Debug'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    direct_route = data['routes'][0]
    direct_pts = [(c[1], c[0]) for c in direct_route['geometry']['coordinates']]
    print(f"Direct route 13->15: {direct_route['distance']:.1f} m, {len(direct_pts)} points")

# Project stop 14 onto direct route 13->15
c14_proj, dist_to_road = project_point_onto_polyline(c14, direct_pts)
print(f"Stop 14 distance to direct road: {dist_to_road:.1f} m")
print(f"Stop 14 original: {c14}, projected: {c14_proj}")

# Route 13 -> c14_proj -> 15
url_proj = f"https://router.project-osrm.org/route/v1/driving/{c13[1]},{c13[0]};{c14_proj[1]},{c14_proj[0]};{c15[1]},{c15[0]}?overview=full&geometries=geojson"
req_proj = urllib.request.Request(url_proj, headers={'User-Agent': 'WhereAmI-Debug'})
with urllib.request.urlopen(req_proj) as resp:
    data = json.loads(resp.read())
    proj_route = data['routes'][0]
    print(f"Projected route 13->14'->15: {proj_route['distance']:.1f} m")

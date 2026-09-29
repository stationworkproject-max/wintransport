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

def osrm_route(coords, overview=True):
    if len(coords) < 2:
        return None, 0, []
    coords_str = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in coords])
    ov = "full" if overview else "false"
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview={ov}&geometries=geojson"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'TestHealing/2.0'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
                if data.get('code') == 'Ok' and data.get('routes'):
                    r = data['routes'][0]
                    pts = [(round(c[1], 5), round(c[0], 5)) for c in r['geometry']['coordinates']] if overview else []
                    return pts, r['distance'], r.get('legs', [])
        except Exception:
            pass
    return None, 0, []

def heal_line(stops):
    coords = [(s['lat'], s['lon']) for s in stops]
    current = list(coords)
    
    for pass_num in range(3):
        pts, dist, legs = osrm_route(current[:65], overview=True)
        if not legs: break
        
        flagged = []
        for i, leg in enumerate(legs):
            st = get_distance(current[i], current[i+1])
            ratio = leg['distance'] / max(st, 30)
            detour = leg['distance'] - st
            if (ratio > 1.45 and detour > 250) or (ratio > 2.2 and detour > 150):
                flagged.append(i)
                
        if not flagged:
            break
            
        # Cluster consecutive or close flagged legs
        clusters = []
        curr = [flagged[0]]
        for f in flagged[1:]:
            if f <= curr[-1] + 2:
                curr.append(f)
            else:
                clusters.append(curr)
                curr = [f]
        clusters.append(curr)
        
        modified = False
        for c in clusters:
            start_leg = c[0]
            end_leg = c[-1]
            anchor_s = max(0, start_leg - 1)
            anchor_e = min(len(current) - 1, end_leg + 2)
            
            if anchor_s >= anchor_e - 1:
                continue
                
            poly_corr, _, _ = osrm_route([current[anchor_s], current[anchor_e]], overview=True)
            if not poly_corr or len(poly_corr) < 2:
                continue
                
            for idx in range(anchor_s + 1, anchor_e):
                snapped_pt, d_moved = project_point_onto_polyline(current[idx], poly_corr)
                if d_moved < 850:
                    current[idx] = (round(snapped_pt[0], 6), round(snapped_pt[1], 6))
                    modified = True
                    
        if not modified:
            break
            
    pts_final, dist_final, legs_final = osrm_route(current[:65], overview=True)
    return current, pts_final, dist_final, legs_final

with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])

for sname in ['104', '38B', '24', '14A']:
    b = [l for l in lines if l['short_name'] == sname][0]
    for dir_name, stops in [('Aller', b['stops']), ('Retour', b.get('stops_retour', []))]:
        if not stops: continue
        coords_orig = [(s['lat'], s['lon']) for s in stops]
        _, d_orig, _ = osrm_route(coords_orig, overview=False)
        _, _, d_clean, clean_legs = heal_line(stops)
        remaining_detours = sum(1 for i, leg in enumerate(clean_legs) if leg['distance'] / max(get_distance(coords_orig[i], coords_orig[i+1]), 30) > 1.45 and leg['distance'] - get_distance(coords_orig[i], coords_orig[i+1]) > 250)
        print(f"Line {sname} {dir_name}: {d_orig:.0f}m -> {d_clean:.0f}m (saved {d_orig - d_clean:.0f}m), remaining detours: {remaining_detours}")

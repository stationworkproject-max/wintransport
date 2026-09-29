import json
import urllib.request
import math
import time

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
            req = urllib.request.Request(url, headers={'User-Agent': 'CorridorFixer/1.0'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
                if data.get('code') == 'Ok' and data.get('routes'):
                    r = data['routes'][0]
                    pts = [(round(c[1], 5), round(c[0], 5)) for c in r['geometry']['coordinates']] if overview else []
                    return pts, r['distance'], r.get('legs', [])
        except Exception:
            time.sleep(0.3)
    return None, 0, []

def fix_line_detours(stops, line_name="Line", dir_name="Aller"):
    coords = [(s['lat'], s['lon']) for s in stops]
    if len(coords) < 3:
        pts, d, _ = osrm_route(coords)
        return coords, pts, d
        
    current_coords = list(coords)
    
    # 2 passes maximum
    for pass_num in range(2):
        pts, total_dist, legs = osrm_route(current_coords, overview=True)
        if not legs:
            break
            
        # Detect flagged legs
        flagged_indices = []
        for i, leg in enumerate(legs):
            st = get_distance(current_coords[i], current_coords[i+1])
            ratio = leg['distance'] / max(st, 30)
            detour = leg['distance'] - st
            if (ratio > 1.45 and detour > 250) or (ratio > 2.5 and detour > 150):
                flagged_indices.append(i)
                
        if not flagged_indices:
            # Clean route!
            break
            
        # Group contiguous flagged legs into clusters
        clusters = []
        curr_cluster = [flagged_indices[0]]
        for f in flagged_indices[1:]:
            if f <= curr_cluster[-1] + 2: # close or consecutive
                curr_cluster.append(f)
            else:
                clusters.append(curr_cluster)
                curr_cluster = [f]
        clusters.append(curr_cluster)
        
        # For each cluster, find safe anchor before and safe anchor after
        modified = False
        for c in clusters:
            start_leg = c[0]
            end_leg = c[-1]
            
            # The stops involved in this detour are from start_leg to end_leg + 1
            # Anchor before: start_leg - 1 (or 0)
            anchor_start = max(0, start_leg - 1)
            # Anchor after: end_leg + 2 (or len - 1)
            anchor_end = min(len(current_coords) - 1, end_leg + 2)
            
            if anchor_start >= anchor_end - 1:
                continue
                
            # Query direct corridor between anchor_start and anchor_end
            poly_corridor, d_corr, _ = osrm_route([current_coords[anchor_start], current_coords[anchor_end]], overview=True)
            if not poly_corridor or len(poly_corridor) < 2:
                continue
                
            # Project all intermediate stops between anchor_start and anchor_end onto this corridor
            for idx in range(anchor_start + 1, anchor_end):
                orig_pt = current_coords[idx]
                snapped_pt, d_moved = project_point_onto_polyline(orig_pt, poly_corridor)
                # Only move if the projected point is reasonably close (< 450m)
                if d_moved < 450:
                    current_coords[idx] = (round(snapped_pt[0], 6), round(snapped_pt[1], 6))
                    modified = True
                    
        if not modified:
            break
            
    # Final route
    pts_final, dist_final, legs_final = osrm_route(current_coords, overview=True)
    return current_coords, pts_final, dist_final

# Let's test on 38B Aller, 38B Retour, 24 Retour, and 16 Retour
with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
idx = text.find('export const STATIC_LINES = ')
lines = json.loads(text[idx + len('export const STATIC_LINES = '):].strip()[:-1])

for test_name in ['38B', '24', '16']:
    line = [l for l in lines if l['short_name'] == test_name][0]
    for dir_idx, dir_name in [(0, 'Aller'), (1, 'Retour')]:
        stops = line.get('stops_retour') if dir_idx == 1 and line.get('stops_retour') else line.get('stops', [])
        
        orig_coords = [(s['lat'], s['lon']) for s in stops]
        _, d_orig, _ = osrm_route(orig_coords, overview=False)
        
        cleaned_coords, final_pts, d_final = fix_line_detours(stops, test_name, dir_name)
        saved = d_orig - d_final
        print(f"Line {test_name} {dir_name}: original {d_orig:.0f}m -> cleaned {d_final:.0f}m (SAVED {saved:.0f}m, -{saved/d_orig*100:.1f}%)")

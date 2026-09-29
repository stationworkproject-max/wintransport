"""
HIGH-SPEED TRANSTU BUS LINE CORRECTOR & ROUTING ENGINE (v2.1)
Using official ArcGIS export:
C:\\Users\\AymenFrd\\Desktop\\MapTrans\\arcgis_export\\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson

Solves:
1. Opposite-road stops causing U-turn loops to the next roundabout ('hip') and back.
2. Outlier coordinate spikes (misplaced stops from other cities).
3. Correct orientation for Aller (pôle central -> banlieue) and Retour (banlieue -> pôle central).
4. Fast single-pass routing with smart pivot projection.
5. Updates src/data/transitShapes.json with clean _0 and _1 polylines.
6. Updates src/data/staticTransit.js with real Transtu stops and stops_retour via clean JSON serialization.
"""

import json
import os
import re
import sys
import time
import math
import urllib.request
from collections import defaultdict

GEOJSON_PATH = r"C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson"
SHAPES_PATH = r"src\data\transitShapes.json"
STATIC_PATH = r"src\data\staticTransit.js"
CACHE_PATH = r"scripts\bus_correction_cache.json"

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

def osrm_route_chunk(coords):
    if len(coords) < 2:
        return None, 0, []
    coords_str = ";".join([f"{p[1]:.5f},{p[0]:.5f}" for p in coords])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI-BusEngine/2.1'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                if data.get('code') == 'Ok' and data.get('routes'):
                    r = data['routes'][0]
                    pts = [(round(c[1], 5), round(c[0], 5)) for c in r['geometry']['coordinates']]
                    legs = r.get('legs', [])
                    return pts, r['distance'], legs
        except Exception:
            time.sleep(0.35 * (attempt + 1))
    return None, 0, []

def clean_and_prepare_stops(raw_stops, is_retour=False):
    if not raw_stops:
        return []
    
    central_hubs = [
        (36.80038, 10.19039), # Tunis Marine
        (36.7950, 10.1800),   # Barcelone
        (36.8050, 10.1800),   # Passage / Thameur
        (36.7860, 10.1810),   # Bab Alioua
        (36.8080, 10.1700)    # Ali Balahouan
    ]
    
    def min_dist_to_hubs(pt):
        return min(get_distance(pt, h) for h in central_hubs)
        
    # Check sequence orientation for Retour:
    # If Retour start is closer to central Tunis than Retour end by > 2.5km:
    # It was digitized outbound instead of inbound! Reverse it so it runs inbound!
    if is_retour and len(raw_stops) > 2:
        start_pt = (raw_stops[0]['lat'], raw_stops[0]['lon'])
        end_pt = (raw_stops[-1]['lat'], raw_stops[-1]['lon'])
        d_start_hub = min_dist_to_hubs(start_pt)
        d_end_hub = min_dist_to_hubs(end_pt)
        if d_start_hub < 2500 and d_end_hub > 3500 and d_end_hub > d_start_hub + 1500:
            raw_stops = list(reversed(raw_stops))
            
    # Filter outlier coordinate spikes (>2.5km jump while direct <1.8km)
    clean = []
    for i, s in enumerate(raw_stops):
        if 0 < i < len(raw_stops) - 1:
            prev_s = clean[-1] if clean else raw_stops[i-1]
            next_s = raw_stops[i+1]
            d_prev = get_distance((prev_s['lat'], prev_s['lon']), (s['lat'], s['lon']))
            d_next = get_distance((s['lat'], s['lon']), (next_s['lat'], next_s['lon']))
            d_direct = get_distance((prev_s['lat'], prev_s['lon']), (next_s['lat'], next_s['lon']))
            if d_prev > 2500 and d_next > 2500 and d_direct < 1800:
                continue
        clean.append(s)
        
    # Check for terminal outlier (>12km jump)
    if len(clean) > 2:
        d01 = get_distance((clean[0]['lat'], clean[0]['lon']), (clean[1]['lat'], clean[1]['lon']))
        if d01 > 12000:
            clean = clean[1:]
    if len(clean) > 2:
        d_last = get_distance((clean[-1]['lat'], clean[-1]['lon']), (clean[-2]['lat'], clean[-2]['lon']))
        if d_last > 12000:
            clean = clean[:-1]
            
    return clean

def route_stops_cleanly(clean_stops):
    if len(clean_stops) < 2:
        return None
        
    coords = [(s['lat'], s['lon']) for s in clean_stops]
    
    # If coords <= 65, route all in a single call
    if len(coords) <= 65:
        pts, dist, legs = osrm_route_chunk(coords)
        time.sleep(0.08)
        
        if legs and len(legs) == len(coords) - 1:
            need_reroute = False
            flagged = []
            for i, leg in enumerate(legs):
                st = get_distance(coords[i], coords[i+1])
                ratio = leg['distance'] / max(st, 30)
                if ratio > 1.8 and leg['distance'] > st + 350:
                    flagged.append(i)
                    
            pivots = set()
            for f_idx in range(len(flagged) - 1):
                if flagged[f_idx+1] == flagged[f_idx] + 1:
                    pivots.add(flagged[f_idx] + 1)
                    
            for p_idx in pivots:
                if 0 < p_idx < len(coords) - 1:
                    p_prev = coords[p_idx - 1]
                    p_curr = coords[p_idx]
                    p_next = coords[p_idx + 1]
                    proj_pt = project_point_onto_segment(p_curr, p_prev, p_next)
                    coords[p_idx] = (round(proj_pt[0], 5), round(proj_pt[1], 5))
                    clean_stops[p_idx]['lat'] = round(proj_pt[0], 6)
                    clean_stops[p_idx]['lon'] = round(proj_pt[1], 6)
                    need_reroute = True
                    
            if need_reroute:
                pts_clean, dist_clean, _ = osrm_route_chunk(coords)
                time.sleep(0.08)
                if pts_clean and dist_clean > 0:
                    pts = pts_clean
                    
        return pts or coords
        
    # Fallback chunking for very long lines (>65 stops)
    chunk_size = 40
    final_shape = []
    for c_start in range(0, len(coords) - 1, chunk_size - 1):
        c_end = min(c_start + chunk_size, len(coords))
        chunk_coords = list(coords[c_start:c_end])
        pts, dist, legs = osrm_route_chunk(chunk_coords)
        time.sleep(0.08)
        
        if legs and len(legs) == len(chunk_coords) - 1:
            need_reroute = False
            flagged = []
            for i, leg in enumerate(legs):
                st = get_distance(chunk_coords[i], chunk_coords[i+1])
                ratio = leg['distance'] / max(st, 30)
                if ratio > 1.8 and leg['distance'] > st + 350:
                    flagged.append(i)
            pivots = set()
            for f_idx in range(len(flagged) - 1):
                if flagged[f_idx+1] == flagged[f_idx] + 1:
                    pivots.add(flagged[f_idx] + 1)
            for p_idx in pivots:
                if 0 < p_idx < len(chunk_coords) - 1:
                    proj = project_point_onto_segment(chunk_coords[p_idx], chunk_coords[p_idx-1], chunk_coords[p_idx+1])
                    chunk_coords[p_idx] = (round(proj[0], 5), round(proj[1], 5))
                    if c_start + p_idx < len(clean_stops):
                        clean_stops[c_start + p_idx]['lat'] = round(proj[0], 6)
                        clean_stops[c_start + p_idx]['lon'] = round(proj[1], 6)
                    need_reroute = True
            if need_reroute:
                pts_c, d_c, _ = osrm_route_chunk(chunk_coords)
                time.sleep(0.08)
                if pts_c and d_c > 0:
                    pts = pts_c
                    
        if pts:
            if final_shape:
                final_shape.extend(pts[1:])
            else:
                final_shape.extend(pts)
        else:
            if final_shape:
                final_shape.extend(chunk_coords[1:])
            else:
                final_shape.extend(chunk_coords)
                
    return final_shape

def main():
    print("=== HIGH-SPEED TRANSTU BUS LINE CORRECTOR ===", flush=True)
    
    # 1. Load GeoJSON
    print(f"Loading {GEOJSON_PATH}...", flush=True)
    data = json.load(open(GEOJSON_PATH, encoding='utf-8', errors='replace'))
    feat = data['features']
    line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]
    num_key = [k for k in feat[0]['properties'] if 'station' in k.lower() and 'nom' not in k.lower()][0]
    name_key = [k for k in feat[0]['properties'] if 'nom' in k.lower()][0]

    # Group into base line -> aller / retour
    geojson_lines = defaultdict(lambda: {'aller': [], 'retour': []})
    for f in feat:
        p = f['properties']
        raw_l = str(p[line_key]).strip()
        is_retour = 'retour' in raw_l.lower()
        
        base_l = raw_l
        for sfx in ['(Retour)', '(retour)', 'Retour', 'retour', '-Retour', '-retour']:
            base_l = base_l.replace(sfx, '')
        base_l = base_l.strip().lower()
        
        coords = f['geometry']['coordinates'] if f.get('geometry') else [p.get('Longitude'), p.get('Latitude')]
        st_data = {
            'stop_id': p[num_key] or 0,
            'name': p[name_key] or 'Arrêt',
            'lat': round(coords[1], 6),
            'lon': round(coords[0], 6),
            'horaires_count': 30
        }
        
        if is_retour:
            geojson_lines[base_l]['retour'].append(st_data)
        else:
            geojson_lines[base_l]['aller'].append(st_data)

    for b in geojson_lines:
        geojson_lines[b]['aller'].sort(key=lambda x: x['stop_id'])
        geojson_lines[b]['retour'].sort(key=lambda x: x['stop_id'])

    print(f"Extracted {len(geojson_lines)} unique bus lines from GeoJSON.", flush=True)
    
    # 2. Load staticTransit.js
    with open(STATIC_PATH, 'r', encoding='utf-8') as f:
        static_raw = f.read()

    marker = 'export const STATIC_LINES = '
    marker_pos = static_raw.find(marker)
    if marker_pos == -1:
        print("ERROR: Could not find STATIC_LINES in staticTransit.js")
        return
    prefix = static_raw[:marker_pos + len(marker)]
    json_part = static_raw[marker_pos + len(marker):].strip()
    if json_part.endswith(';'):
        json_part = json_part[:-1].strip()
        
    static_lines = json.loads(json_part)
    static_buses = [l for l in static_lines if l.get('type_id') == 'bus']
    print(f"Found {len(static_buses)} bus lines in staticTransit.js.", flush=True)
    
    # 3. Load existing shapes and cache
    shapes = json.load(open(SHAPES_PATH, 'r', encoding='utf-8'))
    cache = {}
    if os.path.exists(CACHE_PATH):
        try:
            cache = json.load(open(CACHE_PATH, 'r', encoding='utf-8'))
            print(f"Loaded {len(cache)} cached lines from {CACHE_PATH}.", flush=True)
        except Exception:
            cache = {}
            
    lines_stops_updates = {}
    total = len(static_buses)
    
    for idx, bus in enumerate(static_buses):
        bid = bus['id']
        sname = bus['short_name']
        lname = bus['long_name']
        
        clean_name = sname.lower().strip()
        matched_geo = geojson_lines.get(clean_name)
        if not matched_geo:
            clean2 = clean_name.replace(' ', '').replace('/', '')
            for gb in geojson_lines:
                if gb.replace(' ', '').replace('/', '') == clean2:
                    matched_geo = geojson_lines[gb]
                    break
                    
        cache_key = f"{bid}_v2"
        is_cached = cache_key in cache and 'aller' in cache[cache_key] and len(cache[cache_key]['aller']) > 1
        status_msg = " [CACHED]" if is_cached else ""
        print(f"[{idx+1}/{total}] Processing Line {sname} ({bid}){status_msg}...", flush=True)
        
        if not matched_geo:
            continue
            
        raw_aller = matched_geo['aller']
        raw_retour = matched_geo['retour']
        
        clean_aller = clean_and_prepare_stops(raw_aller, is_retour=False)
        clean_retour = clean_and_prepare_stops(raw_retour, is_retour=True)
        
        if not clean_retour and clean_aller:
            clean_retour = list(reversed(clean_aller))
            
        if is_cached:
            shape_aller = cache[cache_key]['aller']
            shape_retour = cache[cache_key]['retour']
            if 'stops_aller' in cache[cache_key]:
                clean_aller = cache[cache_key]['stops_aller']
            if 'stops_retour' in cache[cache_key]:
                clean_retour = cache[cache_key]['stops_retour']
        else:
            shape_aller = route_stops_cleanly(clean_aller) or shapes.get(f"{bid}_0", shapes.get(bid, []))
            shape_retour = route_stops_cleanly(clean_retour) or shapes.get(f"{bid}_1", [])
            
            cache[cache_key] = {
                'aller': shape_aller,
                'retour': shape_retour,
                'stops_aller': clean_aller,
                'stops_retour': clean_retour
            }
            if (idx + 1) % 5 == 0:
                with open(CACHE_PATH, 'w', encoding='utf-8') as cf:
                    json.dump(cache, cf)
                    
        if shape_aller and len(shape_aller) > 1:
            shapes[bid] = shape_aller
            shapes[f"{bid}_0"] = shape_aller
        if shape_retour and len(shape_retour) > 1:
            shapes[f"{bid}_1"] = shape_retour
            
        lines_stops_updates[bid] = {
            'aller': clean_aller,
            'retour': clean_retour
        }
        
    print(f"\nSaving updated {SHAPES_PATH}...", flush=True)
    with open(SHAPES_PATH, 'w', encoding='utf-8') as sf:
        json.dump(shapes, sf)
    print("[SUCCESS] transitShapes.json updated successfully!", flush=True)
    
    with open(CACHE_PATH, 'w', encoding='utf-8') as cf:
        json.dump(cache, cf)
        
    print(f"\nUpdating {STATIC_PATH} with clean Transtu stops and stops_retour...", flush=True)
    updated_count = 0
    for line in static_lines:
        bid = line.get('id')
        if bid in lines_stops_updates:
            aller_stops = lines_stops_updates[bid]['aller']
            retour_stops = lines_stops_updates[bid]['retour']
            if aller_stops:
                formatted_aller = [
                    {
                        "id": f"st-{s['stop_id']}",
                        "stop_id": s['stop_id'],
                        "name": s['name'],
                        "lat": s['lat'],
                        "lon": s['lon'],
                        "horaires_count": s.get('horaires_count', 30)
                    }
                    for s in aller_stops
                ]
                line['stops'] = formatted_aller
                line['stops_aller'] = formatted_aller
                
            if retour_stops:
                formatted_retour = [
                    {
                        "id": f"st-{s['stop_id']}-r",
                        "stop_id": s['stop_id'],
                        "name": s['name'],
                        "lat": s['lat'],
                        "lon": s['lon'],
                        "horaires_count": s.get('horaires_count', 30)
                    }
                    for s in retour_stops
                ]
                line['stops_retour'] = formatted_retour
                
            if aller_stops and retour_stops:
                # Keep human-readable directions if already set, else set from termini
                if not line.get('directions') or len(line['directions']) < 2:
                    line['directions'] = [aller_stops[-1]['name'], retour_stops[-1]['name']]
                    
            updated_count += 1
            
    with open(STATIC_PATH, 'w', encoding='utf-8') as f:
        f.write(prefix + json.dumps(static_lines, indent=2, ensure_ascii=False) + ';\n')
    print(f"[SUCCESS] staticTransit.js updated successfully ({updated_count} lines updated)!", flush=True)
    print("\n=== ALL TRANSTU BUS LINES CORRECTED SUCCESSFULLY ===", flush=True)

if __name__ == '__main__':
    main()

import json
import re
import math
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load buses.geojson
with open('buses.geojson', 'r', encoding='utf-8') as f:
    buses_geo = json.load(f)

geo_stops = []
for f in buses_geo['features']:
    coords = f.get('geometry', {}).get('coordinates', [])
    if len(coords) >= 2:
        p = f.get('properties', {})
        geo_stops.append({
            'lon': coords[0],
            'lat': coords[1],
            'name': p.get('name') or '',
            'name_ar': p.get('name:ar') or '',
            'name_fr': p.get('name:fr') or '',
            'ref': p.get('ref') or p.get('route_ref') or ''
        })

print(f"Loaded {len(geo_stops)} OSM bus stops from buses.geojson")

# Load staticTransit.js
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))
bus_lines = [l for l in lines if l.get('type_id') == 'bus']

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def normalize(s):
    if not s: return ''
    s = s.upper()
    # remove accents
    for c, r in [('É', 'E'), ('È', 'E'), ('Ê', 'E'), ('Ë', 'E'), ('À', 'A'), ('Â', 'A'), ('Î', 'I'), ('Ï', 'I'), ('Ô', 'O'), ('Ù', 'U'), ('Û', 'U'), ('Ç', 'C')]:
        s = s.replace(c, r)
    s = re.sub(r'[^A-Z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def clean_direction_suffix(name):
    # Remove ' ALLER', ' RETOUR', ' - ALLER', ' - RETOUR', '(ALLER)', etc.
    n = re.sub(r'\s*[-–(]?\s*(ALLER|RETOUR)\s*\)?$', '', name, flags=re.IGNORECASE).strip()
    return n

# Check lines 36B, 38B, 104, 10
sample_check_ids = ['bus_846', 'bus_847', 'bus_772', 'bus_703']

for lid in sample_check_ids:
    line = next((l for l in bus_lines if l['id'] == lid), None)
    if not line:
        continue
    print(f"\n==========================================")
    print(f"LINE: {line['id']} | {line['short_name']} - {line['long_name']}")
    print(f"==========================================")
    
    for gname in ['stops_aller', 'stops_retour']:
        stops = line.get(gname, [])
        print(f"\n--- {gname} ({len(stops)} stops) ---")
        for idx, s in enumerate(stops):
            s_lat, s_lon = s['lat'], s['lon']
            s_name = s.get('name', '')
            clean_name = clean_direction_suffix(s_name)
            norm_name = normalize(clean_name)
            
            # Find best match in geo_stops
            # Strategy:
            # 1. Nearby stops within 150m
            nearby = []
            for gs in geo_stops:
                d = haversine(s_lat, s_lon, gs['lat'], gs['lon'])
                if d <= 250:
                    nearby.append((d, gs))
            nearby.sort(key=lambda x: x[0])
            
            best_match = None
            best_score = -1
            match_type = 'none'
            
            # First check if any nearby stop has matching name
            for d, gs in nearby:
                gnorm_fr = normalize(gs['name_fr'])
                gnorm = normalize(gs['name'])
                sim_fr = SequenceMatcher(None, norm_name, gnorm_fr).ratio() if gnorm_fr else 0
                sim_nm = SequenceMatcher(None, norm_name, gnorm).ratio() if gnorm else 0
                max_sim = max(sim_fr, sim_nm)
                
                # If very close (<35m), even moderate similarity is good
                score = (1.0 - d / 250.0) * 0.4 + max_sim * 0.6
                if d < 35:
                    score += 0.3
                if score > best_score:
                    best_score = score
                    best_match = (d, gs, max_sim)
                    match_type = 'spatial+name'
            
            # If no nearby match or score too low, check within 60m purely spatially
            if (not best_match or best_score < 0.45) and nearby:
                closest_d, closest_gs = nearby[0]
                if closest_d <= 60:
                    best_match = (closest_d, closest_gs, 0)
                    match_type = 'spatial_close'
            
            if best_match and (best_score >= 0.45 or best_match[0] <= 60):
                d, gs, sim = best_match
                ar_val = gs['name_ar'] or gs['name']
                fr_val = gs['name_fr'] or s_name
                print(f"[{idx+1:02d}] '{s_name}'")
                print(f"     -> Matched ({d:.1f}m, type={match_type}, sim={sim:.2f}): FR='{fr_val}' | AR='{ar_val}'")
            else:
                print(f"[{idx+1:02d}] '{s_name}' -> NO CLOSE OSM MATCH (nearest: {nearby[0][0]:.1f}m if nearby else 'none')")

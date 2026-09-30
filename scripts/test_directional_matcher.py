import json
import re
import math
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. Load buses.geojson
with open('buses.geojson', 'r', encoding='utf-8') as f:
    buses_geo = json.load(f)

# Helper to normalize French strings
def normalize_name(s):
    if not s: return ''
    s = s.upper()
    for c, r in [('É', 'E'), ('È', 'E'), ('Ê', 'E'), ('Ë', 'E'), ('À', 'A'), ('Â', 'A'), ('Î', 'I'), ('Ï', 'I'), ('Ô', 'O'), ('Ù', 'U'), ('Û', 'U'), ('Ç', 'C')]:
        s = s.replace(c, r)
    s = re.sub(r'[^A-Z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def clean_direction_tag(name):
    # Strip (Aller), (Retour), ALLER, RETOUR, ذهاب, إياب, etc.
    n = re.sub(r'\s*[-–(]?\s*(ALLER|RETOUR|ذهاب|إياب|اياب|رجوع)\s*\)?$', '', name, flags=re.IGNORECASE).strip()
    return n

# Index geo_stops
geo_stops = []
for idx, f in enumerate(buses_geo['features']):
    coords = f.get('geometry', {}).get('coordinates', [])
    if len(coords) < 2:
        continue
    p = f.get('properties', {})
    raw_name = p.get('name') or ''
    name_fr = p.get('name:fr') or ''
    name_ar = p.get('name:ar') or ''
    
    # Clean arabic name if multiple variants separated by semicolon
    if ';' in name_ar:
        name_ar = name_ar.split(';')[0].strip()
    if ';' in raw_name:
        raw_name = raw_name.split(';')[0].strip()
        
    full_text = f"{raw_name} {name_fr} {name_ar}".lower()
    is_aller = ('aller' in full_text or 'ذهاب' in full_text) and not ('retour' in full_text or 'إياب' in full_text)
    is_retour = ('retour' in full_text or 'إياب' in full_text or 'اياب' in full_text or 'رجوع' in full_text) and not ('aller' in full_text or 'ذهاب' in full_text)
    
    base_fr = clean_direction_tag(name_fr or raw_name)
    base_ar = clean_direction_tag(name_ar or raw_name)
    
    geo_stops.append({
        'id': f.get('id') or f"osm_{idx}",
        'lon': coords[0],
        'lat': coords[1],
        'name': raw_name,
        'name_fr': name_fr or raw_name,
        'name_ar': name_ar or raw_name,
        'base_fr': base_fr,
        'base_ar': base_ar,
        'norm_base': normalize_name(base_fr),
        'is_aller': is_aller,
        'is_retour': is_retour,
    })

print(f"Loaded {len(geo_stops)} OSM stops.")
aller_stops = [s for s in geo_stops if s['is_aller']]
retour_stops = [s for s in geo_stops if s['is_retour']]
neutral_stops = [s for s in geo_stops if not s['is_aller'] and not s['is_retour']]
print(f"Aller: {len(aller_stops)}, Retour: {len(retour_stops)}, Neutral: {len(neutral_stops)}")

# Spatial distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Spatial grid index for superfast lookups (0.01 deg is ~1km)
grid = {}
for gs in geo_stops:
    gx, gy = int(gs['lat'] * 100), int(gs['lon'] * 100)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            cell = (gx + dx, gy + dy)
            if cell not in grid:
                grid[cell] = []
            grid[cell].append(gs)

def find_best_osm_stop(lat, lon, original_name, target_direction='aller'):
    # target_direction: 'aller' or 'retour' or 'neutral'
    gx, gy = int(lat * 100), int(lon * 100)
    candidates = grid.get((gx, gy), [])
    
    clean_orig = clean_direction_tag(original_name)
    norm_orig = normalize_name(clean_orig)
    
    best_candidate = None
    best_score = -1
    
    for gs in candidates:
        d = haversine(lat, lon, gs['lat'], gs['lon'])
        if d > 350:
            continue
            
        sim = SequenceMatcher(None, norm_orig, gs['norm_base']).ratio() if gs['norm_base'] else 0
        
        # Direction matching bonus
        dir_bonus = 0.0
        if target_direction == 'aller':
            if gs['is_aller']:
                dir_bonus = 0.65
            elif gs['is_retour']:
                dir_bonus = -0.50
        elif target_direction == 'retour':
            if gs['is_retour']:
                dir_bonus = 0.65
            elif gs['is_aller']:
                dir_bonus = -0.50
            
        # Distance score: 1.0 at 0m, 0.0 at 350m
        dist_score = max(0.0, 1.0 - d / 350.0)
        
        score = dist_score * 0.35 + sim * 0.45 + dir_bonus
        if d < 35:
            score += 0.20
        if sim > 0.80:
            score += 0.30
            
        if score > best_score:
            best_score = score
            best_candidate = (d, gs, score, sim)
            
    return best_candidate

# Test on 36B and 38B
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

for lid in ['bus_846', 'bus_847']:
    l = next((x for x in lines if x['id'] == lid), None)
    print(f"\n==========================================")
    print(f"TESTING DIRECTIONAL MATCH: {l['id']} - {l['short_name']}")
    print(f"==========================================")
    for dir_idx, gname, target_dir in [(0, 'stops_aller', 'aller'), (1, 'stops_retour', 'retour')]:
        stops = l.get(gname, [])
        print(f"\n--- {gname} (Target dir: {target_dir}) ---")
        for i, s in enumerate(stops):
            match = find_best_osm_stop(s['lat'], s['lon'], s['name'], target_dir)
            if match:
                d, gs, score, sim = match
                dir_flag = "ALLER" if gs['is_aller'] else ("RETOUR" if gs['is_retour'] else "NEUTRAL")
                print(f"[{i+1:02d}] '{s['name']}' ({s['lat']:.5f}, {s['lon']:.5f})")
                print(f"     -> Matched [{dir_flag}] ({d:.1f}m): FR='{gs['name_fr']}' | AR='{gs['name_ar']}'")
            else:
                print(f"[{i+1:02d}] '{s['name']}' -> NO MATCH")

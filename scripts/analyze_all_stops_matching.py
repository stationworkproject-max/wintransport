import json
import re
import math
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

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

print(f"Total OSM stops: {len(geo_stops)}")

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def normalize(s):
    if not s: return ''
    s = s.upper()
    for c, r in [('É', 'E'), ('È', 'E'), ('Ê', 'E'), ('Ë', 'E'), ('À', 'A'), ('Â', 'A'), ('Î', 'I'), ('Ï', 'I'), ('Ô', 'O'), ('Ù', 'U'), ('Û', 'U'), ('Ç', 'C')]:
        s = s.replace(c, r)
    s = re.sub(r'[^A-Z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def clean_direction_suffix(name):
    return re.sub(r'\s*[-–(]?\s*(ALLER|RETOUR)\s*\)?$', '', name, flags=re.IGNORECASE).strip()

# Collect unique stops across ALL lines
all_unique_stops = {}
for line in lines:
    is_bus = line.get('type_id') == 'bus'
    for g in ['stops', 'stops_aller', 'stops_retour']:
        for s in line.get(g, []):
            name = s.get('name', '').strip()
            key = (round(s['lat'], 4), round(s['lon'], 4), normalize(clean_direction_suffix(name)))
            if key not in all_unique_stops:
                all_unique_stops[key] = {
                    'name': name,
                    'lat': s['lat'],
                    'lon': s['lon'],
                    'is_bus': is_bus,
                    'lines': set()
                }
            all_unique_stops[key]['lines'].add(line.get('short_name', line['id']))

print(f"Total unique stop instances: {len(all_unique_stops)}")

matched_count = 0
unmatched_list = []

for key, s in all_unique_stops.items():
    s_lat, s_lon = s['lat'], s['lon']
    clean_name = clean_direction_suffix(s['name'])
    norm_name = normalize(clean_name)
    
    nearby = [(haversine(s_lat, s_lon, gs['lat'], gs['lon']), gs) for gs in geo_stops if haversine(s_lat, s_lon, gs['lat'], gs['lon']) <= 250]
    nearby.sort(key=lambda x: x[0])
    
    best_match = None
    best_score = -1
    
    for d, gs in nearby:
        gnorm_fr = normalize(gs['name_fr'])
        gnorm = normalize(gs['name'])
        sim_fr = SequenceMatcher(None, norm_name, gnorm_fr).ratio() if gnorm_fr else 0
        sim_nm = SequenceMatcher(None, norm_name, gnorm).ratio() if gnorm else 0
        max_sim = max(sim_fr, sim_nm)
        score = (1.0 - d / 250.0) * 0.4 + max_sim * 0.6
        if d < 35: score += 0.35
        if score > best_score:
            best_score = score
            best_match = (d, gs, max_sim)
            
    if best_match and (best_score >= 0.42 or (nearby and nearby[0][0] <= 45)):
        matched_count += 1
    else:
        unmatched_list.append(s)

print(f"Direct OSM matches: {matched_count} / {len(all_unique_stops)} ({matched_count/len(all_unique_stops)*100:.1f}%)")
print(f"Unmatched stops: {len(unmatched_list)}")
print("\nSample 20 unmatched stops:")
for u in unmatched_list[:20]:
    print(f"  '{u['name']}' ({u['lat']:.5f}, {u['lon']:.5f}) - lines: {list(u['lines'])[:3]}")

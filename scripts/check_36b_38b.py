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
    for c, r in [('É', 'E'), ('È', 'E'), ('Ê', 'E'), ('Ë', 'E'), ('À', 'A'), ('Â', 'A'), ('Î', 'I'), ('Ï', 'I'), ('Ô', 'O'), ('Ù', 'U'), ('Û', 'U'), ('Ç', 'C')]:
        s = s.replace(c, r)
    s = re.sub(r'[^A-Z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def clean_direction_suffix(name):
    return re.sub(r'\s*[-–(]?\s*(ALLER|RETOUR)\s*\)?$', '', name, flags=re.IGNORECASE).strip()

for lid in ['bus_846', 'bus_847']:
    line = next((l for l in bus_lines if l['id'] == lid), None)
    print(f"\n==========================================")
    print(f"=== {line['id']} : {line['short_name']} - {line['long_name']} ===")
    print(f"==========================================")
    for gname in ['stops_aller', 'stops_retour']:
        stops = line.get(gname, [])
        print(f"\n-- {gname} ({len(stops)} stops) --")
        for idx, s in enumerate(stops):
            s_lat, s_lon = s['lat'], s['lon']
            s_name = s.get('name', '')
            clean_name = clean_direction_suffix(s_name)
            norm_name = normalize(clean_name)
            nearby = [(haversine(s_lat, s_lon, gs['lat'], gs['lon']), gs) for gs in geo_stops if haversine(s_lat, s_lon, gs['lat'], gs['lon']) <= 350]
            nearby.sort(key=lambda x: x[0])
            best_match = None
            best_score = -1
            for d, gs in nearby:
                gnorm_fr = normalize(gs['name_fr'])
                gnorm = normalize(gs['name'])
                sim_fr = SequenceMatcher(None, norm_name, gnorm_fr).ratio() if gnorm_fr else 0
                sim_nm = SequenceMatcher(None, norm_name, gnorm).ratio() if gnorm else 0
                max_sim = max(sim_fr, sim_nm)
                score = (1.0 - d / 350.0) * 0.4 + max_sim * 0.6
                if d < 35: score += 0.3
                if score > best_score:
                    best_score = score
                    best_match = (d, gs, max_sim)
            if best_match and (best_score >= 0.40 or (nearby and nearby[0][0] <= 50)):
                d, gs, sim = best_match
                print(f"[{idx+1:02d}] '{s_name}' -> FR: \"{gs['name_fr'] or gs['name']}\" | AR: \"{gs['name_ar'] or gs['name']}\" ({d:.1f}m, sim={sim:.2f})")
            elif nearby:
                print(f"[{idx+1:02d}] '{s_name}' -> CLOSEST OSM ({nearby[0][0]:.1f}m): \"{nearby[0][1]['name']}\"")
            else:
                print(f"[{idx+1:02d}] '{s_name}' -> NO NEARBY OSM STOP")

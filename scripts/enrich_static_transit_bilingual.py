import json
import re
import math
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. Load buses.geojson
with open('buses.geojson', 'r', encoding='utf-8') as f:
    buses_geo = json.load(f)

def normalize_name(s):
    if not s: return ''
    s = s.upper()
    for c, r in [('É', 'E'), ('È', 'E'), ('Ê', 'E'), ('Ë', 'E'), ('À', 'A'), ('Â', 'A'), ('Î', 'I'), ('Ï', 'I'), ('Ô', 'O'), ('Ù', 'U'), ('Û', 'U'), ('Ç', 'C')]:
        s = s.replace(c, r)
    s = re.sub(r'[^A-Z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def clean_direction_tag(name):
    n = re.sub(r'\s*[-–(]?\s*(ALLER|RETOUR|ذهاب|إياب|اياب|رجوع)\s*\)?$', '', name, flags=re.IGNORECASE).strip()
    return n

# Index geo_stops
geo_stops = []
for idx, f in enumerate(buses_geo['features']):
    coords = f.get('geometry', {}).get('coordinates', [])
    if len(coords) < 2:
        continue
    p = f.get('properties', {})
    raw_name = (p.get('name') or '').strip()
    name_fr = (p.get('name:fr') or '').strip()
    name_ar = (p.get('name:ar') or '').strip()
    
    if ';' in name_ar:
        name_ar = name_ar.split(';')[0].strip()
    if ';' in raw_name and not name_ar:
        name_ar = raw_name.split(';')[0].strip()
        
    full_text = f"{raw_name} {name_fr} {name_ar}".lower()
    is_aller = ('aller' in full_text or 'ذهاب' in full_text) and not ('retour' in full_text or 'إياب' in full_text)
    is_retour = ('retour' in full_text or 'إياب' in full_text or 'اياب' in full_text or 'رجوع' in full_text) and not ('aller' in full_text or 'ذهاب' in full_text)
    
    base_fr = clean_direction_tag(name_fr or raw_name)
    base_ar = clean_direction_tag(name_ar or raw_name)
    
    geo_stops.append({
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

print(f"Loaded {len(geo_stops)} OSM stops from buses.geojson.")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Fast spatial grid
grid = {}
for gs in geo_stops:
    gx, gy = int(gs['lat'] * 100), int(gs['lon'] * 100)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            cell = (gx + dx, gy + dy)
            if cell not in grid:
                grid[cell] = []
            grid[cell].append(gs)

def find_best_osm_stop(lat, lon, original_name, target_direction='neutral'):
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
        
        dir_bonus = 0.0
        if target_direction == 'aller':
            if gs['is_aller']: dir_bonus = 0.65
            elif gs['is_retour']: dir_bonus = -0.50
        elif target_direction == 'retour':
            if gs['is_retour']: dir_bonus = 0.65
            elif gs['is_aller']: dir_bonus = -0.50
            
        dist_score = max(0.0, 1.0 - d / 350.0)
        score = dist_score * 0.35 + sim * 0.45 + dir_bonus
        if d < 35: score += 0.20
        if sim > 0.80: score += 0.30
            
        if score > best_score:
            best_score = score
            best_candidate = (d, gs, score, sim)
            
    return best_candidate

# Translation dictionary for well-known words and intercity stations
KNOWN_TERMS = {
    'TUNIS MARINE': ('Tunis Marine', 'تونس البحرية'),
    'PLACE BARCELONE': ('Place Barcelone', 'ساحة برشلونة'),
    'PLACE DE BARCELONE': ('Place Barcelone', 'ساحة برشلونة'),
    'BARCELONE': ('Place Barcelone', 'ساحة برشلونة'),
    'TUNIS VILLE': ('Tunis Ville (Gare Centrale)', 'تونس المدينة (المحطة المركزية)'),
    'GARE CENTRALE': ('Gare Centrale', 'المحطة المركزية'),
    'AEROPORT TUNIS CARTHAGE': ('Aéroport Tunis-Carthage', 'مطار تونس قرطاج'),
    'AEROPORT': ('Aéroport', 'المطار'),
    'CARTHAGE': ('Carthage', 'قرطاج'),
    'LA MARSA': ('La Marsa', 'المرسى'),
    'MARSA PLAGE': ('La Marsa Plage', 'شاطئ المرسى'),
    'SIDI BOU SAID': ('Sidi Bou Saïd', 'سيدي بوسعيد'),
    'LA GOULETTE': ('La Goulette', 'حلق الوادي'),
    'LE KRAM': ('Le Kram', 'الكرم'),
    'BEN AROUS': ('Ben Arous', 'بن عروس'),
    'RADES': ('Radès', 'رادس'),
    'EZZAHRA': ('Ezzahra', 'الزهراء'),
    'HAMMAM LIF': ('Hammam Lif', 'حمام الأنف'),
    'HAMMAM CHATT': ('Hammam Chatt', 'حمام الشط'),
    'BORJ CEDRIA': ('Borj Cédria', 'برج السدرية'),
    'ERRIADH': ('Erriadh', 'الرياض'),
    'EL MOUROUJ 4': ('El Mourouj 4', 'المروج 4'),
    'EL MOUROUJ': ('El Mourouj', 'المروج'),
    'MANNOUBA': ('La Manouba', 'منوبة'),
    'DEN DEN': ('Den Den', 'الدندان'),
    'BARDO': ('Le Bardo', 'باردو'),
    'BAB SAADOUN': ('Bab Saadoun', 'باب سعدون'),
    'BAB ALIOUA': ('Bab Alioua', 'باب عليوة'),
    'ARIANA': ('Ariana', 'أريانة'),
    'INTILAKA': ('Cité Ennour / Intilaka', 'الانطلاقة'),
    'IBN KHALDOUN': ('Cité Ibn Khaldoun', 'ابن خلدون'),
    'KHEIREDDINE': ('Kheireddine', 'خير الدين'),
    'BORJ LOUZIR': ('Borj Louzir', 'برج الوزير'),
    'SOUSSE': ('Sousse', 'سوسة'),
    'SOUSSE VILLE': ('Sousse Ville', 'سوسة المدينة'),
    'SFAX': ('Sfax', 'صفاقس'),
    'GABES': ('Gabès', 'قابس'),
    'BIZERTE': ('Bizerte', 'بنزرت'),
    'NABEUL': ('Nabeul', 'نابل'),
    'HAMMAMET': ('Hammamet', 'الحمامات'),
    'BEJA': ('Béja', 'باجة'),
    'JENDOUBA': ('Jendouba', 'جندوبة'),
    'GAFSA': ('Gafsa', 'قفصة'),
    'TOZEUR': ('Tozeur', 'توزر'),
    'MAHDIA': ('Mahdia', 'المهدية'),
    'MONASTIR': ('Monastir', 'المنستير'),
    'TEBOURBA': ('Tébourba', 'طبربة'),
    'MEJEZ EL BAB': ('Mejez El Bab', 'مجاز الباب'),
    'BOU SALEM': ('Bou Salem', 'بوسالم'),
    'GHARDIMAOU': ('Ghardimaou', 'غار الدماء'),
    'ZAGHOUAN': ('Zaghouan', 'زغوان'),
    'BIR MCHERGA': ('Bir Mcherga', 'بئر مشارقة'),
}

# Arabic letters mapping for bus lines like 36B -> 36 ب, 14A -> 14 أ
LETTER_MAP = {
    'A': 'أ', 'B': 'ب', 'C': 'ج', 'D': 'د', 'E': 'هـ', 'F': 'ف', 'G': 'غ',
    'H': 'ح', 'I': 'ي', 'J': 'ج', 'K': 'ك', 'L': 'ل', 'M': 'م', 'N': 'ن'
}

def translate_short_name(sn):
    if not sn: return ''
    res = sn
    for lat, ar in LETTER_MAP.items():
        res = re.sub(rf'\b([0-9]+){lat}\b', rf'\1 {ar}', res)
        res = re.sub(rf'\b{lat}([0-9]+)\b', rf'{ar} \1', res)
        res = re.sub(rf'^{lat}$', ar, res)
    return res

# Read staticTransit.js
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    orig_content = f.read()

# Make backup
with open('src/data/staticTransit.js.pre-bilingual.bak', 'w', encoding='utf-8') as f:
    f.write(orig_content)

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', orig_content, re.DOTALL)
lines = json.loads(m.group(1))

# First pass: map of known station name -> (name_fr, name_ar)
name_dictionary = {}
for k, v in KNOWN_TERMS.items():
    name_dictionary[normalize_name(k)] = v

# Collect matches from all stops
total_stops = 0
direct_osm_matches = 0

for line in lines:
    is_bus = line.get('type_id') == 'bus'
    
    # Process aller and retour
    for dir_idx, gname, target_dir in [(0, 'stops_aller', 'aller'), (1, 'stops_retour', 'retour')]:
        stops = line.get(gname, [])
        for s in stops:
            total_stops += 1
            s_name = s.get('name', '')
            match = find_best_osm_stop(s['lat'], s['lon'], s_name, target_dir)
            if match and (match[2] >= 0.40 or match[0] <= 50):
                d, gs, score, sim = match
                direct_osm_matches += 1
                fr_clean = gs['name_fr'] or s_name
                ar_clean = gs['name_ar'] or gs['name']
                
                # Snap coordinates to OSM roadside bus stop if within 85m or if direction matched within 160m
                if d <= 85 or (d <= 160 and (gs['is_aller'] or gs['is_retour'])):
                    s['lat'] = round(gs['lat'], 6)
                    s['lon'] = round(gs['lon'], 6)
                    
                s['name_fr'] = fr_clean
                s['name_ar'] = ar_clean
                
                # Remember in name_dictionary
                base_key = normalize_name(clean_direction_tag(s_name))
                if base_key and base_key not in name_dictionary:
                    name_dictionary[base_key] = (clean_direction_tag(fr_clean), clean_direction_tag(ar_clean))
            else:
                # Check name_dictionary
                base_key = normalize_name(clean_direction_tag(s_name))
                if base_key in name_dictionary:
                    dict_fr, dict_ar = name_dictionary[base_key]
                    dir_suffix_fr = " (Aller)" if target_dir == 'aller' and is_bus else (" (Retour)" if target_dir == 'retour' and is_bus else "")
                    dir_suffix_ar = " (ذهاب)" if target_dir == 'aller' and is_bus else (" (إياب)" if target_dir == 'retour' and is_bus else "")
                    s['name_fr'] = dict_fr + dir_suffix_fr
                    s['name_ar'] = dict_ar + dir_suffix_ar
                else:
                    s['name_fr'] = s_name
                    # Basic Arabic transliteration/fallback
                    s['name_ar'] = s_name

    # If line has flat 'stops' array, also update it
    if 'stops' in line and line['stops']:
        # By default mirror stops_aller if stops has same length
        aller_stops = line.get('stops_aller', [])
        if len(aller_stops) == len(line['stops']):
            line['stops'] = [dict(s) for s in aller_stops]
        else:
            for s in line['stops']:
                s_name = s.get('name', '')
                base_key = normalize_name(clean_direction_tag(s_name))
                if base_key in name_dictionary:
                    s['name_fr'], s['name_ar'] = name_dictionary[base_key]
                else:
                    s['name_fr'] = s_name
                    s['name_ar'] = s_name

    # Enrich line-level metadata
    line['short_name_ar'] = translate_short_name(line.get('short_name', ''))
    
    # Derive long_name_ar and long_name_fr
    aller = line.get('stops_aller', []) or line.get('stops', [])
    retour = line.get('stops_retour', [])
    
    if aller:
        start_stop = aller[0]
        end_stop = aller[-1]
        
        start_fr = clean_direction_tag(start_stop.get('name_fr', start_stop.get('name', '')))
        end_fr = clean_direction_tag(end_stop.get('name_fr', end_stop.get('name', '')))
        start_ar = clean_direction_tag(start_stop.get('name_ar', start_stop.get('name', '')))
        end_ar = clean_direction_tag(end_stop.get('name_ar', end_stop.get('name', '')))
        
        line['long_name_fr'] = f"{start_fr} - {end_fr}"
        line['long_name_ar'] = f"{start_ar} - {end_ar}"
        
        line['directions_fr'] = [f"Vers {end_fr}", f"Vers {start_fr}"]
        line['directions_ar'] = [f"إلى {end_ar}", f"إلى {start_ar}"]
    else:
        line['long_name_fr'] = line.get('long_name', '')
        line['long_name_ar'] = line.get('long_name', '')
        line['directions_fr'] = line.get('directions', ['Aller', 'Retour'])
        line['directions_ar'] = ['ذهاب', 'إياب']

print(f"Total stops processed: {total_stops}")
print(f"Direct OSM matches: {direct_osm_matches} ({direct_osm_matches/total_stops*100:.1f}%)")

# Write enriched STATIC_LINES back into staticTransit.js
new_json_str = json.dumps(lines, ensure_ascii=False, indent=2)
new_content = orig_content[:m.start(1)] + new_json_str + orig_content[m.end(1):]

with open('src/data/staticTransit.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully written enriched bilingual data to src/data/staticTransit.js")

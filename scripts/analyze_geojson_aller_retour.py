import json
from collections import defaultdict

data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
feat = data['features']
line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]
num_key = [k for k in feat[0]['properties'] if 'station' in k.lower() and 'nom' not in k.lower()][0]
name_key = [k for k in feat[0]['properties'] if 'nom' in k.lower()][0]

lines_dict = defaultdict(lambda: {'aller': [], 'retour': []})

for f in feat:
    p = f['properties']
    raw_l = str(p[line_key]).strip()
    is_retour = 'retour' in raw_l.lower()
    
    # clean base line name (e.g. '104 (Retour)' -> '104', '116 Retour' -> '116')
    base_l = raw_l
    for sfx in ['(Retour)', '(retour)', 'Retour', 'retour', '-Retour', '-retour']:
        base_l = base_l.replace(sfx, '')
    base_l = base_l.strip()
    
    station_item = {
        'num': p[num_key],
        'name': p[name_key],
        'lat': f['geometry']['coordinates'][1] if f.get('geometry') else p.get('Latitude'),
        'lon': f['geometry']['coordinates'][0] if f.get('geometry') else p.get('Longitude')
    }
    
    if is_retour:
        lines_dict[base_l]['retour'].append(station_item)
    else:
        lines_dict[base_l]['aller'].append(station_item)

print(f"Total base lines extracted: {len(lines_dict)}")

both_count = 0
aller_only = 0
retour_only = 0

for b, d in lines_dict.items():
    has_a = len(d['aller']) > 0
    has_r = len(d['retour']) > 0
    if has_a and has_r:
        both_count += 1
    elif has_a:
        aller_only += 1
    else:
        retour_only += 1

print(f"Lines with BOTH Aller and Retour: {both_count}")
print(f"Lines with Aller only: {aller_only}")
print(f"Lines with Retour only: {retour_only}")

if aller_only:
    print("Sample aller only lines:", list(lines_dict.keys())[:10])

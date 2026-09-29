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
    base_l = raw_l
    for sfx in ['(Retour)', '(retour)', 'Retour', 'retour', '-Retour', '-retour']:
        base_l = base_l.replace(sfx, '')
    base_l = base_l.strip()
    
    st = {
        'num': p[num_key],
        'name': p[name_key],
        'lat': f['geometry']['coordinates'][1] if f.get('geometry') else p.get('Latitude'),
        'lon': f['geometry']['coordinates'][0] if f.get('geometry') else p.get('Longitude')
    }
    if is_retour:
        lines_dict[base_l]['retour'].append(st)
    else:
        lines_dict[base_l]['aller'].append(st)

print("Checking 15 lines with Aller and Retour:")
sample_bases = ['104', '20', '3D', '116', '12', '14A', '15', '16', '17', '18', '23', '33', '35', '4A', '71']

for b in sample_bases:
    d = lines_dict.get(b, {})
    a_stops = sorted(d.get('aller', []), key=lambda s: s['num'] if s['num'] is not None else 0)
    r_stops = sorted(d.get('retour', []), key=lambda s: s['num'] if s['num'] is not None else 0)
    
    print(f"\n=== LINE {b} ===")
    if a_stops:
        print(f"  ALLER ({len(a_stops)} stops): [1] {a_stops[0]['name']} -> [{len(a_stops)}] {a_stops[-1]['name']}")
    if r_stops:
        print(f"  RETOUR ({len(r_stops)} stops): [1] {r_stops[0]['name']} -> [{len(r_stops)}] {r_stops[-1]['name']}")

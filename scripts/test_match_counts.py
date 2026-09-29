import json, re
from collections import defaultdict

GEOJSON_PATH = r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson'
data = json.load(open(GEOJSON_PATH, encoding='utf-8', errors='replace'))
feat = data['features']
line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]

geojson_lines = defaultdict(lambda: {'aller': [], 'retour': []})
for f in feat:
    p = f['properties']
    raw_l = str(p[line_key]).strip()
    is_retour = 'retour' in raw_l.lower()
    base_l = raw_l
    for sfx in ['(Retour)', '(retour)', 'Retour', 'retour', '-Retour', '-retour']:
        base_l = base_l.replace(sfx, '')
    base_l = base_l.strip().lower()
    if is_retour:
        geojson_lines[base_l]['retour'].append(f)
    else:
        geojson_lines[base_l]['aller'].append(f)

with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()

marker = 'export const STATIC_LINES = '
idx = text.find(marker)
json_part = text[idx + len(marker):].strip()
if json_part.endswith(';'):
    json_part = json_part[:-1].strip()
static_lines = json.loads(json_part)
static_buses = [l for l in static_lines if l.get('type_id') == 'bus']

matched = []
unmatched = []
for bus in static_buses:
    bid = bus['id']
    sname = bus['short_name']
    clean_name = sname.lower().strip()
    matched_geo = geojson_lines.get(clean_name)
    if not matched_geo:
        clean2 = clean_name.replace(' ', '').replace('/', '')
        for gb in geojson_lines:
            if gb.replace(' ', '').replace('/', '') == clean2:
                matched_geo = geojson_lines[gb]
                break
    if matched_geo:
        matched.append((bid, sname, len(matched_geo['aller']), len(matched_geo['retour'])))
    else:
        unmatched.append((bid, sname))

print('Total static buses:', len(static_buses))
print('Matched buses:', len(matched))
print('Unmatched buses count:', len(unmatched))
for u in unmatched:
    print('  Unmatched:', u)

import json
import re
from collections import defaultdict

# 1. Load GeoJSON
data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
feat = data['features']
line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]

geojson_lines = set(str(f['properties'][line_key]).strip() for f in feat)

# Group into base lines
geojson_bases = defaultdict(dict)
for l in geojson_lines:
    is_retour = 'retour' in l.lower()
    base = l.lower().replace('(retour)', '').replace('retour', '').strip()
    if is_retour:
        geojson_bases[base]['retour'] = l
    else:
        geojson_bases[base]['aller'] = l

# 2. Load staticTransit.js
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r'\{\s*"id":\s*"(bus_[^"]+)",\s*"route_id":\s*"([^"]+)",\s*"type_id":\s*"bus",\s*"short_name":\s*"([^"]+)",\s*"long_name":\s*"([^"]+)"')
static_buses = pattern.findall(text)

print(f"Static bus lines: {len(static_buses)}")
print(f"GeoJSON base lines: {len(geojson_bases)}")

matched = []
unmatched_static = []

for bid, rid, sname, lname in static_buses:
    clean_sname = sname.lower().strip()
    if clean_sname in geojson_bases:
        matched.append((bid, sname, clean_sname))
    else:
        # try without spaces or slashes
        clean2 = clean_sname.replace(' ', '').replace('/', '')
        found = False
        for gb in geojson_bases:
            if gb.replace(' ', '').replace('/', '') == clean2:
                matched.append((bid, sname, gb))
                found = True
                break
        if not found:
            unmatched_static.append((bid, sname, lname))

print(f"Matched bus lines: {len(matched)}")
print(f"Unmatched static lines: {len(unmatched_static)}")
if unmatched_static:
    print("Sample unmatched static lines:", unmatched_static[:20])

unmatched_geojson = []
matched_gbases = set(m[2] for m in matched)
for gb in geojson_bases:
    if gb not in matched_gbases:
        unmatched_geojson.append(gb)

print(f"GeoJSON lines not in staticTransit: {len(unmatched_geojson)}")
print("Sample GeoJSON lines not in static:", sorted(unmatched_geojson)[:30])

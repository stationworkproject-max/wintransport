import json

data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
feat = data['features']
line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]

raw_lines = sorted(list(set(str(f['properties'][line_key]).strip() for f in feat)))
print(f"Total raw lines: {len(raw_lines)}")
# Look at the first 50
for l in raw_lines[:50]:
    print(repr(l))

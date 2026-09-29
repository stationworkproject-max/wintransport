import json
import urllib.request

data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
feat = data['features']
line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]
num_key = [k for k in feat[0]['properties'] if 'station' in k.lower() and 'nom' not in k.lower()][0]
name_key = [k for k in feat[0]['properties'] if 'nom' in k.lower()][0]

stops_104_aller = [f for f in feat if str(f['properties'][line_key]).strip() == '104']
stops_104_aller.sort(key=lambda f: f['properties'][num_key])

print(f"104 Aller stops: {len(stops_104_aller)}")
for i, f in enumerate(stops_104_aller):
    p = f['properties']
    c = f['geometry']['coordinates']
    print(f"[{i+1}] {p[num_key]}: {p[name_key]} - ({c[1]:.5f}, {c[0]:.5f})")

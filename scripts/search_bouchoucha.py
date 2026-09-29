import json

data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
feat = data['features']
line_key = [k for k in feat[0]['properties'] if 'ligne' in k.lower()][0]
name_key = [k for k in feat[0]['properties'] if 'nom' in k.lower()][0]

bouchoucha_stops = []
for f in feat:
    p = f['properties']
    if 'bouchoucha' in str(p[name_key]).lower():
        bouchoucha_stops.append((p[line_key], p[name_key], f['geometry']['coordinates']))

print(f"Total Bouchoucha stations: {len(bouchoucha_stops)}")
unique_stations = {}
for l, n, c in bouchoucha_stops:
    k = (n, round(c[1], 4), round(c[0], 4))
    if k not in unique_stations:
        unique_stations[k] = []
    unique_stations[k].append(l)

for k, lines in unique_stations.items():
    print(f"Station: {k[0]} at ({k[1]}, {k[2]}) - Lines ({len(lines)}): {lines[:10]}")

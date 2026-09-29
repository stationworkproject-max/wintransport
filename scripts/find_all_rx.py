import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))
lkey = [k for k in d['features'][0]['properties'].keys() if 'ligne' in k.lower()][0]
nkey = [k for k in d['features'][0]['properties'].keys() if 'nom' in k.lower()][0]

rx_stations = []
for f in d['features']:
    nom = str(f['properties'].get(nkey, ''))
    if 'RX' in nom.upper():
        rx_stations.append((f['properties'].get(lkey), nom, f['geometry']['coordinates']))

print(f"Total RX occurrences: {len(rx_stations)}")
for s in rx_stations:
    print(f"  Line {s[0]}: {s[1]} at {s[2]}")

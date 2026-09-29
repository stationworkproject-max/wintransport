import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson'
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

for target in ['38B', '38B Retour']:
    feats = [f['properties'] for f in data['features'] if f['properties'].get('N°_de_la_ligne') == target]
    feats.sort(key=lambda x: x.get('N°_de_station', 0))
    print(f"\n--- {target} ({len(feats)} stations) ---")
    for st in feats:
        print(f"  [{st.get('N°_de_station'):2d}] {st.get('Nom_de_station')} : ({st.get('Latitude'):.6f}, {st.get('Longitude'):.6f})")

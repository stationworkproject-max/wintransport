import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson'
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

for target in ['36 B', '38 B']:
    print(f"\n==================== LINE {target} ====================")
    feats = []
    for feat in data['features']:
        props = feat.get('properties', {})
        line_no = props.get('N°_de_la_ligne', '')
        if line_no.strip().upper().startswith(target):
            feats.append(props)
            
    # Group by line_no
    groups = {}
    for pr in feats:
        lno = pr.get('N°_de_la_ligne', '').strip()
        if lno not in groups: groups[lno] = []
        groups[lno].append(pr)
        
    for lno, group in groups.items():
        print(f"\n--- {lno} ({len(group)} stations) ---")
        group.sort(key=lambda x: x.get('N°_de_station', 0))
        for st in group:
            print(f"  [{st.get('N°_de_station'):2d}] {st.get('Nom_de_station')} : ({st.get('Latitude'):.6f}, {st.get('Longitude'):.6f})")

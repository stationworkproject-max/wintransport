import json
from collections import defaultdict

data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))

features = data['features']
print(f"Total features in geojson: {len(features)}")

# Group by line
lines = defaultdict(list)
for f in features:
    props = f['properties']
    # find line key
    line_key = [k for k in props.keys() if 'ligne' in k.lower()][0]
    line_name = str(props[line_key]).strip()
    
    geom = f['geometry']
    coords = geom['coordinates'] if geom else [props.get('Longitude'), props.get('Latitude')]
    
    station_num_key = [k for k in props.keys() if 'station' in k.lower() and 'nom' not in k.lower()][0]
    station_name_key = [k for k in props.keys() if 'nom' in k.lower()][0]
    
    lines[line_name].append({
        'objectid': props.get('OBJECTID'),
        'num': props.get(station_num_key),
        'name': props.get(station_name_key),
        'lon': coords[0],
        'lat': coords[1]
    })

print(f"Total line keys: {len(lines)}")

# Let's inspect line names: Aller vs Retour
aller_retour_pairs = defaultdict(dict)
for l_name, stations in lines.items():
    stations.sort(key=lambda s: s['num'] if s['num'] is not None else 0)
    is_retour = 'retour' in l_name.lower()
    base_name = l_name.lower().replace('(retour)', '').replace('retour', '').strip()
    
    if is_retour:
        aller_retour_pairs[base_name]['retour'] = (l_name, len(stations), stations)
    else:
        aller_retour_pairs[base_name]['aller'] = (l_name, len(stations), stations)

print(f"Total base lines: {len(aller_retour_pairs)}")
sample_pairs = list(aller_retour_pairs.items())[:15]
for base, p in sample_pairs:
    aller_info = f"{p['aller'][0]} ({p['aller'][1]} stops)" if 'aller' in p else "NO ALLER"
    retour_info = f"{p['retour'][0]} ({p['retour'][1]} stops)" if 'retour' in p else "NO RETOUR"
    print(f"  Line '{base}': {aller_info} | {retour_info}")

# Check line 104 specifically
print("\n--- LINE 104 in GeoJSON ---")
for base in ['104', '35', '3d', '20', '116']:
    p = aller_retour_pairs.get(base, {})
    print(f"Base '{base}': aller={bool('aller' in p)}, retour={bool('retour' in p)}")
    if 'aller' in p:
        print(f"  Aller ({p['aller'][1]} stops): first={p['aller'][2][0]['name']}, last={p['aller'][2][-1]['name']}")
    if 'retour' in p:
        print(f"  Retour ({p['retour'][1]} stops): first={p['retour'][2][0]['name']}, last={p['retour'][2][-1]['name']}")

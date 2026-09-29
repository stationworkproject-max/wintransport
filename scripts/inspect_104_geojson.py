import json

data = json.load(open(r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson', encoding='utf-8', errors='replace'))

features = data['features']
f_104_aller = []
f_104_retour = []

for f in features:
    props = f['properties']
    line_key = [k for k in props if 'ligne' in k.lower()][0]
    num_key = [k for k in props if 'station' in k.lower() and 'nom' not in k.lower()][0]
    name_key = [k for k in props if 'nom' in k.lower()][0]
    l_name = str(props.get(line_key, '')).strip()
    if l_name == '104':
        f_104_aller.append(props)
    elif '104' in l_name and 'retour' in l_name.lower():
        f_104_retour.append(props)

f_104_aller.sort(key=lambda x: x.get(num_key, 0))
f_104_retour.sort(key=lambda x: x.get(num_key, 0))

print(f"104 Aller count: {len(f_104_aller)}")
for s in f_104_aller:
    print(f"  {s.get(num_key)}: {s.get(name_key)} ({s.get('Latitude'):.5f}, {s.get('Longitude'):.5f})")

print(f"\n104 Retour count: {len(f_104_retour)}")
for s in f_104_retour:
    print(f"  {s.get(num_key)}: {s.get(name_key)} ({s.get('Latitude'):.5f}, {s.get('Longitude'):.5f})")

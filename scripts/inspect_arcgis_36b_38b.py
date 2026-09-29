import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export\01_Bus_Stations_Lignes_TRANSTU_Tunis.geojson'
print("Reading geojson...")
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total features: {len(data['features'])}")

# Check feature types and properties
geom_types = {}
sample_props = None
matching_features = []

for idx, feat in enumerate(data['features']):
    gtype = feat.get('geometry', {}).get('type')
    geom_types[gtype] = geom_types.get(gtype, 0) + 1
    props = feat.get('properties', {})
    # Search for 36 or 38 or 846 or 847
    prop_str = str(props).lower()
    if '36b' in prop_str or '38b' in prop_str or '36 b' in prop_str or '38 b' in prop_str:
        matching_features.append((idx, gtype, props))

print("Geometry types:", geom_types)
print(f"Matching features for 36b/38b: {len(matching_features)}")
for idx, gt, props in matching_features[:10]:
    print(f"  feat #{idx} ({gt}): {props}")

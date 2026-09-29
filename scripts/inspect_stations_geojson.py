import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\stations.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total features in stations.geojson: {len(data['features'])}")
sample = data['features'][0]
print("Sample properties:", sample['properties'])
print("Geometry type:", sample['geometry']['type'])

# Let's inspect some sample names
for f in data['features'][:15]:
    props = f['properties']
    coords = f['geometry']['coordinates']
    print(f"  {coords} : {props.get('name')} | {props.get('name:fr')} | {props.get('railway')}")

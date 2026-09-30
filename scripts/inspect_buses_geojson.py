import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('buses.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

features = data.get('features', [])
print(f"Total features in buses.geojson: {len(features)}")

# Check geometry types
geom_types = {}
for f in features:
    gt = f.get('geometry', {}).get('type')
    geom_types[gt] = geom_types.get(gt, 0) + 1
print("Geometry types:", geom_types)

# Inspect unique property keys across features
prop_keys = set()
for f in features:
    for k in f.get('properties', {}).keys():
        prop_keys.add(k)
print(f"\nProperty keys ({len(prop_keys)}):", sorted(list(prop_keys)))

# Sample features
print("\nSample 5 features:")
for i, f in enumerate(features[:5]):
    print(f"--- Feature {i+1} ---")
    print(f"  Geom: {f.get('geometry', {}).get('type')}")
    props = f.get('properties', {})
    for k, v in props.items():
        print(f"  {k}: {v}")

# Check lines or ref or operator or station names
lines_set = set()
for f in features:
    p = f.get('properties', {})
    for k in ['line', 'ref', 'ligne', 'N°_de_la_ligne', 'route', 'bus']:
        if k in p and p[k]:
            lines_set.add((k, str(p[k])))

print(f"\nLines found in properties: {len(lines_set)}")
for item in sorted(list(lines_set))[:20]:
    print(f"  {item[0]} = {item[1]}")

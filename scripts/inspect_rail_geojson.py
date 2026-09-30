import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

features = data.get('features', [])
print(f"Total features in rail.geojson: {len(features)}")

# Collect unique property keys and sample values
prop_keys = set()
railway_types = {}
for f in features:
    props = f.get('properties', {})
    for k in props:
        prop_keys.add(k)
    rw = props.get('railway')
    railway_types[rw] = railway_types.get(rw, 0) + 1

print("\nProperty keys:", prop_keys)
print("\nRailway types distribution:")
for rw, count in sorted(railway_types.items(), key=lambda x: -x[1]):
    print(f"  {rw}: {count}")

# Check lines or names or services
names = set()
services = set()
usage = set()
for f in features:
    props = f.get('properties', {})
    if props.get('name'):
        names.add(props['name'])
    if props.get('service'):
        services.add(props['service'])
    if props.get('usage'):
        usage.add(props['usage'])

print(f"\nUnique names ({len(names)}):")
for n in sorted(list(names))[:30]:
    print(f"  {n}")

print(f"\nServices: {services}")
print(f"Usage: {usage}")

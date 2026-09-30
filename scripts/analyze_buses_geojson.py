import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('buses.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

features = data['features']
total = len(features)
has_name = 0
has_name_ar = 0
has_name_fr = 0
has_name_en = 0
has_ref = 0

for f in features:
    p = f.get('properties', {})
    if p.get('name'): has_name += 1
    if p.get('name:ar'): has_name_ar += 1
    if p.get('name:fr'): has_name_fr += 1
    if p.get('name:en'): has_name_en += 1
    if p.get('ref') or p.get('route_ref'): has_ref += 1

print(f"Total features: {total}")
print(f"has name:    {has_name} ({has_name/total*100:.1f}%)")
print(f"has name:ar: {has_name_ar} ({has_name_ar/total*100:.1f}%)")
print(f"has name:fr: {has_name_fr} ({has_name_fr/total*100:.1f}%)")
print(f"has name:en: {has_name_en} ({has_name_en/total*100:.1f}%)")
print(f"has ref:     {has_ref} ({has_ref/total*100:.1f}%)")

# Sample features that have both arabic and french names
print("\nSample 10 features with Arabic and French names:")
sample_count = 0
for f in features:
    p = f.get('properties', {})
    if p.get('name:ar') and (p.get('name:fr') or p.get('name:en') or p.get('name')):
        coords = f.get('geometry', {}).get('coordinates', [])
        print(f"  [{coords[1]:.5f}, {coords[0]:.5f}] | name: '{p.get('name')}' | ar: '{p.get('name:ar')}' | fr: '{p.get('name:fr')}' | ref: '{p.get('ref') or p.get('route_ref')}'")
        sample_count += 1
        if sample_count >= 10:
            break

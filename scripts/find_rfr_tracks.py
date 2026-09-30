import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total features: {len(data['features'])}")

keywords = ['rfr', 'ligne d', 'ligne e', 'خط d', 'خط e', 'gobaa', 'bougatfa', 'manoubia', 'saïda', 'mellassine', 'bardo', 'hrairia']

rfr_features = []
for f in data['features']:
    props = f.get('properties', {})
    text = " ".join([str(v) for v in props.values()]).lower()
    for kw in keywords:
        if kw in text:
            rfr_features.append((kw, props, f['geometry']['type']))
            break

print(f"Features matching RFR keywords: {len(rfr_features)}")
for kw, props, gtype in rfr_features:
    print(f"  [{kw}] railway={props.get('railway')} | name={props.get('name')} | ref={props.get('ref')} | line={props.get('line')} | operator={props.get('operator')}")

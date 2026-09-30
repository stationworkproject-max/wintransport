import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    rail = json.load(f)

for idx, feat in enumerate(rail['features']):
    geom = feat.get('geometry', {})
    coords = geom.get('coordinates', [])
    props = feat.get('properties', {})
    pts = coords if geom.get('type') == 'LineString' else []
    # check if in depot box
    in_box = any(36.8115 <= p[1] <= 36.8145 and 10.286 <= p[0] <= 10.292 for p in pts)
    if in_box:
        print(f"Way #{idx}: id={props.get('@id')}, name={props.get('name')}, railway={props.get('railway')}, service={props.get('service')}, tags={props}")

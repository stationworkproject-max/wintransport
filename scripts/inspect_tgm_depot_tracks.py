import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('rail.geojson', 'r', encoding='utf-8') as f:
    rail = json.load(f)

found_ways = []
for idx, feat in enumerate(rail['features']):
    geom = feat.get('geometry', {})
    coords = geom.get('coordinates', [])
    props = feat.get('properties', {})
    
    pts = coords if geom.get('type') == 'LineString' else []
    in_box = any(36.811 <= p[1] <= 36.817 and 10.280 <= p[0] <= 10.296 for p in pts)
    if in_box:
        found_ways.append((idx, props, pts))

print(f"Found {len(found_ways)} rail ways near La Goulette depot:")
for idx, props, pts in found_ways:
    print(f"\nWay #{idx}:")
    print(f"  name: {props.get('name')}, railway: {props.get('railway')}, service: {props.get('service')}, usage: {props.get('usage')}")
    print(f"  tags: {props}")
    print(f"  points count: {len(pts)}")
    print(f"  start: lat={pts[0][1]}, lon={pts[0][0]}")
    print(f"  end:   lat={pts[-1][1]}, lon={pts[-1][0]}")
    # print all points
    for p_idx, p in enumerate(pts):
        print(f"    p{p_idx}: lat={p[1]:.6f}, lon={p[0]:.6f}")

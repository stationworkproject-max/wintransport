import json

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

# list of 32 IDs
from parse_static_transit import static_lines
train_lines = [l for l in static_lines if l.get('type_id') == 'train' or l['id'].startswith('train_') or l['id'].startswith('rfr_')]

print(f"Total shapes in transitShapes.json: {len(shapes)}")
missing = []
has_points = []
for l in train_lines:
    lid = l['id']
    pts = shapes.get(lid, [])
    # Also check if there's _aller or _retour
    aller = shapes.get(f"{lid}_aller", [])
    retour = shapes.get(f"{lid}_retour", [])
    print(f"  {lid:10s} : direct={len(pts)} pts, aller={len(aller)}, retour={len(retour)} | stops={len(l.get('stops', []))}")
    if len(pts) == 0 and len(aller) == 0:
        missing.append(lid)
    else:
        has_points.append(lid)

print(f"\nMissing shape count: {len(missing)}: {missing}")

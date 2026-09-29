import json

with open('src/data/transitShapes.json', 'r') as f:
    shapes = json.load(f)

for bid in ['bus_846', 'bus_847']:
    for suffix in ['', '_0', '_1', '_aller', '_retour']:
        k = f"{bid}{suffix}"
        pts = shapes.get(k, [])
        print(f"Key {k:15s}: {len(pts)} points")

import json

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

for k in ['bus_846', 'bus_846_0', 'bus_846_1', 'bus_847', 'bus_847_0', 'bus_847_1']:
    if k in shapes:
        pts = shapes[k]
        print(f"Shape {k}: {len(pts)} points")
        if len(pts) > 0:
            print(f"  First: {pts[0]}, Last: {pts[-1]}")
    else:
        print(f"Shape {k}: NOT FOUND")

import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

for k in sorted(shapes.keys()):
    if 'rfr_46' in k or 'rfr_47' in k:
        pts = shapes[k]
        print(f"Key: {k:15s} | Pts: {len(pts)} | Start: {pts[0]} | End: {pts[-1]}")

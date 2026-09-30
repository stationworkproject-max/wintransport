import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

for lid in ['rfr_46', 'rfr_47']:
    pts = shapes[lid]
    print(f"\n=== {lid} path points 30 to 80 ===")
    for i in range(30, min(80, len(pts))):
        print(f"  {i:2d}: {pts[i][0]:.6f}, {pts[i][1]:.6f}")

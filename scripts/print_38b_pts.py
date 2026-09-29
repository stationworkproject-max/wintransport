import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r') as f:
    shapes = json.load(f)

pts = shapes['bus_847_0']

print("--- 38B Aller shape points 180 to 255 ---")
for i in range(180, min(len(pts), 255)):
    p = pts[i]
    print(f"  pt #{i:3d}: ({p[0]:.6f}, {p[1]:.6f})")

import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

for lid in ['rfr_46', 'rfr_47']:
    pts = shapes[lid]
    print(f"\n=== {lid} path first 30 points (from Tunis Ville) ===")
    for i, p in enumerate(pts[:30]):
        print(f"  {i:2d}: {p[0]:.6f}, {p[1]:.6f}")

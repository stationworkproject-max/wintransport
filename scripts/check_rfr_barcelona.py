import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

pts = shapes['rfr_46']
print(f"rfr_46 points count: {len(pts)}")
print("First 10 points:")
for i, p in enumerate(pts[:10]):
    print(f"  {i}: {p[0]:.6f}, {p[1]:.6f}")

# Check if any point goes north of 36.7950 (Barcelona square is 36.7955 to 36.7975)
north_pts = [p for p in pts if p[0] > 36.7950]
print(f"Points north of 36.7950 (in Barcelona square): {len(north_pts)}")
for p in north_pts:
    print(f"  {p}")

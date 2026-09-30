import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

tgm_orig = shapes['metro_56']
print(f"Original tgm points: {len(tgm_orig)}")

# Let's inspect points 38 to 98
print("Points 38 to 98 before fix:")
for i in range(38, 98):
    print(f"  {i}: {tgm_orig[i]}")

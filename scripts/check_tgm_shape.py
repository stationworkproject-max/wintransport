import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

tgm = shapes['metro_56']
print(f"Total points in metro_56: {len(tgm)}")
print(f"First point: {tgm[0]}")
print(f"Last point:  {tgm[-1]}")

# Check if there are any other backward loops or duplicates
for i in range(len(tgm) - 1):
    p1 = tgm[i]
    p2 = tgm[i+1]
    if p1 == p2:
        print(f"Duplicate point at index {i}: {p1}")

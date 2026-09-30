import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

tgm = shapes['metro_56']

# Find indices where it enters and leaves the depot area
# lon between 10.285 and 10.293
start_idx = None
end_idx = None
for i, p in enumerate(tgm):
    if 10.285 <= p[1] <= 10.293:
        if start_idx is None: start_idx = i
        end_idx = i

print(f"TGM total points: {len(tgm)}")
print(f"Depot section from index {start_idx} to {end_idx}:")
for i in range(start_idx - 2, end_idx + 3):
    print(f"  {i}: lat={tgm[i][0]:.6f}, lon={tgm[i][1]:.6f}")

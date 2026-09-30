import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
idx = text.find(prefix)
lines = json.loads(text[idx + len(prefix):text.rfind(']') + 1])

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

for mid in ['metro_50', 'metro_51', 'metro_52', 'metro_53', 'metro_54', 'metro_55', 'metro_56']:
    line = [l for l in lines if l['id'] == mid][0]
    shape = shapes.get(mid, [])
    stops = line.get('stops', [])
    print(f"\n==========================================")
    print(f"=== {mid} ({line['short_name']} - {line['long_name']}) ===")
    print(f"Stops ({len(stops)}):")
    for s in stops:
        print(f"  {s['stop_id']}. {s['name']} ({s['lat']}, {s['lon']})")
    print(f"Shape: {len(shape)} points")
    if len(shape):
        print(f"  Shape start: {shape[0]}, Shape end: {shape[-1]}")

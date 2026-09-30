import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    st_text = f.read()

prefix = 'export const STATIC_LINES = '
idx = st_text.find(prefix)
lines = json.loads(st_text[idx + len(prefix):st_text.rfind(']') + 1])

for lid in ['rfr_46', 'rfr_47', 'rfr_19']:
    line = [l for l in lines if l['id'] == lid][0]
    pts = shapes.get(lid, [])
    print(f"\n==========================================")
    print(f"=== {lid} ({line['short_name']} - {line['long_name']}) ===")
    print(f"Stops ({len(line['stops'])}):")
    for s in line['stops']:
        print(f"  {s['stop_id']}. {s['name']} ({s['lat']}, {s['lon']})")
    print(f"Shape points: {len(pts)}")
    if pts:
        print(f"  Start: {pts[0]}, End: {pts[-1]}")

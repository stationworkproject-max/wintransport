import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
lines_json = text[text.find(prefix) + len(prefix):].strip()
if lines_json.endswith(';'): lines_json = lines_json[:-1].strip()
lines = json.loads(lines_json)

for bid in ['bus_846', 'bus_847']:
    l = [x for x in lines if x['id'] == bid][0]
    print(f"\n==================== {bid}: {l['short_name']} - {l['long_name']} ====================")
    print("ALLER STOPS (count:", len(l.get('stops_aller', l.get('stops', []))), "):")
    for i, s in enumerate(l.get('stops_aller', l.get('stops', []))):
        print(f"  [{i+1:2d}] {s['name']:35s} ({s['lat']:.6f}, {s['lon']:.6f})")
    print("\nRETOUR STOPS (count:", len(l.get('stops_retour', [])), "):")
    for i, s in enumerate(l.get('stops_retour', [])):
        print(f"  [{i+1:2d}] {s['name']:35s} ({s['lat']:.6f}, {s['lon']:.6f})")

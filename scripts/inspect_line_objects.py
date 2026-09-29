import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])

for bid in ['bus_846', 'bus_847']:
    l = [x for x in lines if x['id'] == bid][0]
    print(f"\n==================== {bid} ====================")
    for k, v in l.items():
        if k in ['stops', 'stops_aller', 'stops_retour']:
            print(f"  {k}: {len(v)} items")
        else:
            print(f"  {k}: {v}")

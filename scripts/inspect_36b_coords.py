import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

b36b = next(l for l in lines if l['id'] == 'bus_846')
print("=== 36B ALLER ===")
for i, s in enumerate(b36b.get('stops_aller', [])):
    print(f"Aller {i+1}: {s.get('name_fr')} | ({s['lat']}, {s['lon']})")
print("\n=== 36B RETOUR ===")
for i, s in enumerate(b36b.get('stops_retour', [])):
    print(f"Retour {i+1}: {s.get('name_fr')} | ({s['lat']}, {s['lon']})")

b38b = next(l for l in lines if l['id'] == 'bus_847')
print("\n=== 38B ALLER ===")
for i, s in enumerate(b38b.get('stops_aller', [])):
    print(f"Aller {i+1}: {s.get('name_fr')} | ({s['lat']}, {s['lon']})")
print("\n=== 38B RETOUR ===")
for i, s in enumerate(b38b.get('stops_retour', [])):
    print(f"Retour {i+1}: {s.get('name_fr')} | ({s['lat']}, {s['lon']})")

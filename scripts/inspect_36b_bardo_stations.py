import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])
bus_36b = [l for l in lines if l['id'] == 'bus_846'][0]

print("36B Aller stops 5, 6, 7, 8:")
for i in [4, 5, 6, 7]:
    s = bus_36b['stops_aller'][i]
    print(f"  [{i+1}] {s['name']} : ({s['lat']}, {s['lon']})")

print("\n36B Retour stops 1, 2, 3, 4:")
for i in [0, 1, 2, 3]:
    s = bus_36b['stops_retour'][i]
    print(f"  [{i+1}] {s['name']} : ({s['lat']}, {s['lon']})")

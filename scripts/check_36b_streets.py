import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])
bus_36b = [l for l in lines if l['id'] == 'bus_846'][0]

print("=== 36B ALLER STATIONS AND NEAREST STREETS ===")
for i, s in enumerate(bus_36b['stops_aller']):
    url = f"https://router.project-osrm.org/nearest/v1/driving/{s['lon']},{s['lat']}?number=1"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        wp = d['waypoints'][0]
        print(f"[{i+1}] {s['name'][:30]:30s} ({s['lat']:.6f}, {s['lon']:.6f}) -> street: '{wp.get('name')}', dist={wp['distance']:.1f}m")

print("\n=== 36B RETOUR STATIONS AND NEAREST STREETS ===")
for i, s in enumerate(bus_36b['stops_retour']):
    url = f"https://router.project-osrm.org/nearest/v1/driving/{s['lon']},{s['lat']}?number=1"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        wp = d['waypoints'][0]
        print(f"[{i+1}] {s['name'][:30]:30s} ({s['lat']:.6f}, {s['lon']:.6f}) -> street: '{wp.get('name')}', dist={wp['distance']:.1f}m")

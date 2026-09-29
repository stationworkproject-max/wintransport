import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])
bus_36b = [l for l in lines if l['id'] == 'bus_846'][0]

print("=== 36B ALLER LEGS ===")
for i in range(len(bus_36b['stops_aller']) - 1):
    s1, s2 = bus_36b['stops_aller'][i], bus_36b['stops_aller'][i+1]
    url = f"https://router.project-osrm.org/route/v1/driving/{s1['lon']},{s1['lat']};{s2['lon']},{s2['lat']}?overview=full&steps=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        direct = 1000 * ( ( (s1['lat']-s2['lat'])*111)**2 + ((s1['lon']-s2['lon'])*89)**2 )**0.5
        ratio = r['distance'] / max(1.0, direct)
        warn = " *** DETOUR ***" if ratio > 1.8 and r['distance'] > 300 else ""
        print(f"Leg {i+1}->{i+2} ({s1['name'][:25]:25s} -> {s2['name'][:25]:25s}): {r['distance']:5.0f}m (direct: {direct:4.0f}m, ratio {ratio:.2f}){warn}")

print("\n=== 36B RETOUR LEGS ===")
for i in range(len(bus_36b['stops_retour']) - 1):
    s1, s2 = bus_36b['stops_retour'][i], bus_36b['stops_retour'][i+1]
    url = f"https://router.project-osrm.org/route/v1/driving/{s1['lon']},{s1['lat']};{s2['lon']},{s2['lat']}?overview=full&steps=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        direct = 1000 * ( ( (s1['lat']-s2['lat'])*111)**2 + ((s1['lon']-s2['lon'])*89)**2 )**0.5
        ratio = r['distance'] / max(1.0, direct)
        warn = " *** DETOUR ***" if ratio > 1.8 and r['distance'] > 300 else ""
        print(f"Leg {i+1}->{i+2} ({s1['name'][:25]:25s} -> {s2['name'][:25]:25s}): {r['distance']:5.0f}m (direct: {direct:4.0f}m, ratio {ratio:.2f}){warn}")

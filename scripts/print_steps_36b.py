import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])
bus_36b = [l for l in lines if l['id'] == 'bus_846'][0]

print("=== 36B ALLER STEPS ===")
stops_aller = bus_36b.get('stops_aller', bus_36b['stops'])
for i in range(len(stops_aller) - 1):
    s1, s2 = stops_aller[i], stops_aller[i+1]
    url = f"https://router.project-osrm.org/route/v1/driving/{s1['lon']},{s1['lat']};{s2['lon']},{s2['lat']}?overview=full&steps=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"\nLeg {i+1}->{i+2} ({s1['name']} -> {s2['name']}): {r['distance']:.0f}m")
        for st in r['legs'][0]['steps']:
            print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):12s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

print("\n\n=== 36B RETOUR STEPS ===")
stops_retour = bus_36b['stops_retour']
for i in range(len(stops_retour) - 1):
    s1, s2 = stops_retour[i], stops_retour[i+1]
    url = f"https://router.project-osrm.org/route/v1/driving/{s1['lon']},{s1['lat']};{s2['lon']},{s2['lat']}?overview=full&steps=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"\nLeg {i+1}->{i+2} ({s1['name']} -> {s2['name']}): {r['distance']:.0f}m")
        for st in r['legs'][0]['steps']:
            print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):12s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

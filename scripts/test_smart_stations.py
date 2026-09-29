import urllib.request
import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(p1, p2):
    R = 6371000
    phi1, phi2 = math.radians(p1[0]), math.radians(p2[0])
    dphi = math.radians(p2[0] - p1[0])
    dlambda = math.radians(p2[1] - p1[1])
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Let's inspect the shapes and stations of 36B and 38B
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])

bus_36b = [l for l in lines if l['id'] == 'bus_846'][0]
bus_38b = [l for l in lines if l['id'] == 'bus_847'][0]

print("=== INSPECTING 36B STATIONS ===")
print("ALLER:")
for i, s in enumerate(bus_36b['stops_aller']):
    print(f"  {i+1}. {s['name']:35s} ({s['lat']:.6f}, {s['lon']:.6f})")
print("RETOUR:")
for i, s in enumerate(bus_36b['stops_retour']):
    print(f"  {i+1}. {s['name']:35s} ({s['lat']:.6f}, {s['lon']:.6f})")

print("\n=== INSPECTING 38B STATIONS ===")
print("ALLER:")
for i, s in enumerate(bus_38b['stops_aller']):
    print(f"  {i+1}. {s['name']:35s} ({s['lat']:.6f}, {s['lon']:.6f})")
print("RETOUR:")
for i, s in enumerate(bus_38b['stops_retour']):
    print(f"  {i+1}. {s['name']:35s} ({s['lat']:.6f}, {s['lon']:.6f})")

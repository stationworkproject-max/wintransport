import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('buses.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

def haversine(p1, p2):
    R = 6371000
    phi1, phi2 = math.radians(p1[0]), math.radians(p2[0])
    dphi, dlambda = math.radians(p2[0] - p1[0]), math.radians(p2[1] - p1[1])
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

target = (36.8360529, 10.1606257)

print("Bus stops within 500m of SONED:")
for f in data['features']:
    props = f.get('properties', {})
    coords = f.get('geometry', {}).get('coordinates', [])
    if len(coords) < 2: continue
    pt = (coords[1], coords[0])
    d = haversine(target, pt)
    if d <= 500:
        print(f"  {props.get('name')} | AR: {props.get('name:ar')} | {pt} -> dist={d:.1f}m")

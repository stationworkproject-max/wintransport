import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p1 = (36.832198, 10.154312) # Clinique Taoufik Aller
p2 = (36.825112, 10.143985) # Campus Aller

url = f"https://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?steps=true&overview=false"
req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

print("Waypoints:")
for wp in data.get('waypoints', []):
    print(f"  Name: {wp.get('name')}, Location: {wp.get('location')}, Hint: {wp.get('hint')[:20]}")

legs = data['routes'][0]['legs'][0]
print(f"\nTotal distance: {legs['distance']}m, duration: {legs['duration']}s")
for step in legs['steps']:
    print(f"  {step.get('name', 'unnamed')} ({step['maneuver']['type']}) -> {step['distance']}m")

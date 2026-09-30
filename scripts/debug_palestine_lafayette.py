import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p1 = (36.820217, 10.182178) # Palestine
p2 = (36.810986, 10.184607) # Lafayette Retour

url = f"https://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?steps=true&overview=false"
req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

leg = data['routes'][0]['legs'][0]
print(f"Palestine -> Lafayette Retour: {leg['distance']}m")
for s in leg['steps']:
    print(f"  {s.get('name', 'unnamed')} ({s['maneuver']['type']}) -> {s['distance']}m")

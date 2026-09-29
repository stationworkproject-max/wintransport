import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Let's inspect the road graph between Mutuelleville and Bouazizi using Overpass API or routing
# Overpass query to find highway ways around 36.832 to 36.840, 10.160 to 10.170
query = """
[out:json][timeout:25];
(
  way["highway"](36.833, 10.162, 36.840, 10.168);
);
out body;
>;
out skel qt;
"""

url = "https://overpass-api.de/api/interpreter"
req = urllib.request.Request(url, data=query.encode('utf-8'), headers={'User-Agent': 'TestTransit'})
try:
    with urllib.request.urlopen(req) as resp:
        osm = json.loads(resp.read())
        ways = [e for e in osm['elements'] if e['type'] == 'way']
        print(f"Total ways found: {len(ways)}")
        for w in ways:
            tags = w.get('tags', {})
            name = tags.get('name', tags.get('name:fr', tags.get('name:en', 'unnamed')))
            hw = tags.get('highway', '')
            oneway = tags.get('oneway', '')
            print(f"  Way {w['id']}: '{name}' ({hw}), oneway={oneway}")
except Exception as e:
    print(f"Overpass error: {e}")

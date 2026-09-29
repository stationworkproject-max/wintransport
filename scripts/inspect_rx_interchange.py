import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Query Overpass for all ways around the RX interchange
query = """
[out:json][timeout:25];
(
  way(36.835, 10.163, 36.840, 10.168)["highway"];
);
out geom;
"""

url = "https://overpass-api.de/api/interpreter"
req = urllib.request.Request(url, data=query.encode('utf-8'), headers={'User-Agent': 'TestTransit'})
with urllib.request.urlopen(req) as resp:
    osm = json.loads(resp.read())

print(f"Total ways: {len(osm['elements'])}")
for e in osm['elements']:
    tags = e.get('tags', {})
    name = tags.get('name', tags.get('name:ar', 'unnamed'))
    hw = tags.get('highway', '')
    geom = e.get('geometry', [])
    if 'link' in hw or 'secondary' in hw or 'tertiary' in hw:
        start = (geom[0]['lat'], geom[0]['lon']) if geom else None
        end = (geom[-1]['lat'], geom[-1]['lon']) if geom else None
        print(f"Way {e['id']}: '{name}' ({hw}), oneway={tags.get('oneway')}, nodes={len(geom)}, start={start}, end={end}")

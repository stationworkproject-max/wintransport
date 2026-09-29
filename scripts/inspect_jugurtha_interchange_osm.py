import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Query overpass for all ways and nodes at the interchange
# Bounding box around interchange: lat 36.836 to 36.841, lon 10.160 to 10.167
overpass_url = "https://overpass-api.de/api/interpreter"
query = """
[out:json][timeout:25];
(
  way(36.836, 10.160, 36.841, 10.167)["highway"];
);
out body;
>;
out skel qt;
"""

data = urllib.parse.urlencode({'data': query}).encode('utf-8')
req = urllib.request.Request(overpass_url, data=data, headers={'User-Agent': 'TransitAudit/2.0'})
try:
    with urllib.request.urlopen(req) as resp:
        osm_data = json.loads(resp.read())
    nodes = {n['id']: (n['lat'], n['lon']) for n in osm_data['elements'] if n['type'] == 'node'}
    ways = [w for w in osm_data['elements'] if w['type'] == 'way']
    print(f"Loaded {len(nodes)} nodes and {len(ways)} ways at interchange:")
    for w in ways:
        name = w.get('tags', {}).get('name', 'unnamed')
        hw = w.get('tags', {}).get('highway', '')
        oneway = w.get('tags', {}).get('oneway', 'no')
        w_nodes = [nodes[nid] for nid in w['nodes'] if nid in nodes]
        if w_nodes:
            print(f"Way #{w['id']}: '{name}' ({hw}, oneway={oneway}) | {len(w_nodes)} pts | start=({w_nodes[0][0]:.5f}, {w_nodes[0][1]:.5f}), end=({w_nodes[-1][0]:.5f}, {w_nodes[-1][1]:.5f})")
except Exception as e:
    print("Overpass error:", e)

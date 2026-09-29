import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Query OSM around Taoufik and SONED on Avenue Mohamed Bouazizi
overpass_url = "https://overpass-api.de/api/interpreter"
query = """
[out:json][timeout:25];
(
  way(around:150, 36.835932, 10.160730)["highway"];
  way(around:150, 36.832431, 10.154153)["highway"];
  way(around:150, 36.838100, 10.165200)["highway"];
);
out body;
>;
out skel qt;
"""

data = urllib.parse.urlencode({'data': query}).encode('utf-8')
req = urllib.request.Request(overpass_url, data=data, headers={'User-Agent': 'TransitAudit/1.0'})
with urllib.request.urlopen(req) as resp:
    osm_data = json.loads(resp.read())

nodes = {n['id']: (n['lat'], n['lon']) for n in osm_data['elements'] if n['type'] == 'node'}
ways = [w for w in osm_data['elements'] if w['type'] == 'way']

print("--- Road ways near SONED, Clinique Taoufik, RX ---")
for w in ways:
    name = w.get('tags', {}).get('name', 'unnamed')
    oneway = w.get('tags', {}).get('oneway', 'no')
    hw = w.get('tags', {}).get('highway', '')
    w_nodes = [nodes[nid] for nid in w['nodes'] if nid in nodes]
    if len(w_nodes) >= 2:
        # Calculate heading/bearing of the way
        p0 = w_nodes[0]
        p1 = w_nodes[-1]
        print(f"Way #{w['id']}: '{name}' ({hw}, oneway={oneway}) | {len(w_nodes)} pts | start=({p0[0]:.6f}, {p0[1]:.6f}) -> end=({p1[0]:.6f}, {p1[1]:.6f})")
        for i, nd in enumerate(w_nodes):
            print(f"    node #{i}: ({nd[0]:.6f}, {nd[1]:.6f})")

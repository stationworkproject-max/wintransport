import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Query overpass for Boulevard 10 Decembre / Taoufik corridor (lat 36.828 to 36.840, lon 10.148 to 10.170)
overpass_url = "https://overpass-api.de/api/interpreter"
query = """
[out:json][timeout:25];
(
  way["highway"](36.828,10.148,36.840,10.170);
);
out body;
>;
out skel qt;
"""

print("Querying Overpass for Taoufik / SONED / RX corridor...")
data = urllib.parse.urlencode({'data': query}).encode('utf-8')
req = urllib.request.Request(overpass_url, data=data, headers={'User-Agent': 'TransitAudit/1.0'})
try:
    with urllib.request.urlopen(req) as resp:
        osm_data = json.loads(resp.read())
        
    nodes = {n['id']: (n['lat'], n['lon']) for n in osm_data['elements'] if n['type'] == 'node'}
    ways = [w for w in osm_data['elements'] if w['type'] == 'way']
    print(f"Loaded {len(nodes)} nodes, {len(ways)} ways.")
    
    # Print main avenues
    for w in ways:
        name = w.get('tags', {}).get('name', '')
        ref = w.get('tags', {}).get('ref', '')
        oneway = w.get('tags', {}).get('oneway', 'no')
        hw = w.get('tags', {}).get('highway', '')
        if any(k in name.lower() for k in ['10', 'décembre', 'decembre', 'taoufik', 'savary', 'mutuel', 'louis', 'pasteur', 'tanit', 'samaouel', 'charles']):
            w_nodes = [nodes[nid] for nid in w['nodes'] if nid in nodes]
            if w_nodes:
                p_start = w_nodes[0]
                p_end = w_nodes[-1]
                print(f"Way #{w['id']}: '{name}' ({hw}, oneway={oneway}) | pts={len(w_nodes)} | start=({p_start[0]:.5f}, {p_start[1]:.5f}), end=({p_end[0]:.5f}, {p_end[1]:.5f})")
except Exception as e:
    print("Overpass error:", e)

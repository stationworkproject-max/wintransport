import urllib.request
import json

# Query Overpass API for all ways near (36.830..36.840, 10.150..10.168)
query = """
[out:json][timeout:25];
(
  way["highway"~"primary|secondary|trunk|tertiary|residential"](36.830, 10.150, 36.840, 10.168);
);
out body;
>;
out skel qt;
"""

url = "https://overpass-api.de/api/interpreter"
req = urllib.request.Request(url, data=query.encode('utf-8'), headers={'User-Agent': 'WhereAmI-Debug'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        elements = data.get('elements', [])
        nodes = {e['id']: (e['lat'], e['lon']) for e in elements if e.get('type') == 'node'}
        ways = [e for e in elements if e.get('type') == 'way']
        print(f"Total ways retrieved: {len(ways)}")
        
        # Look for ways named Tanit, Essamaouel, Jugurtha, Bouazizi, etc.
        for w in ways:
            tags = w.get('tags', {})
            name = tags.get('name', tags.get('name:fr', tags.get('name:ar', 'unnamed')))
            name_clean = ''.join([c for c in name if ord(c) < 128])
            hw = tags.get('highway')
            oneway = tags.get('oneway', 'no')
            w_nodes = [nodes[nid] for nid in w.get('nodes', []) if nid in nodes]
            if w_nodes:
                mid_lat = sum(n[0] for n in w_nodes) / len(w_nodes)
                mid_lon = sum(n[1] for n in w_nodes) / len(w_nodes)
                if any(x in name_clean.lower() for x in ['tanit', 'essamaouel', 'jugurtha', 'bouazizi', 'novembre', 'taoufik', 'soned', 'ligue']):
                    print(f"Way {w['id']}: '{name_clean}', hw={hw}, oneway={oneway}, mid=({mid_lat:.4f}, {mid_lon:.4f})")
except Exception as e:
    print("Overpass error:", e)

import urllib.request
import json

query = """
[out:json];
way["highway"~"primary|secondary|trunk"](36.830, 10.150, 36.840, 10.168);
out tags;
"""
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=query.encode('utf-8'))
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    for e in data['elements']:
        t = e.get('tags', {})
        name = ''.join([c for c in t.get('name', 'unnamed') if ord(c) < 128])
        print(f"Way {e['id']}: name='{name}' hw={t.get('highway')} oneway={t.get('oneway')}")

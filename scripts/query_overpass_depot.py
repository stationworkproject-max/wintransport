import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Let's query OpenStreetMap Overpass API for all ways (roads and railways) between 10.285 and 10.293, 36.812 and 36.816
# Overpass interpreter query
overpass_url = "https://overpass-api.de/api/interpreter"
query = """
[out:json][timeout:25];
(
  way["railway"](36.811,10.284,36.816,10.294);
  way["highway"](36.811,10.284,36.816,10.294);
);
out body geom;
"""

req = urllib.request.Request(overpass_url, data=query.encode('utf-8'), headers={'User-Agent': 'WhereAmI/1.0'})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        print(f"Overpass returned {len(data.get('elements', []))} elements:")
        for el in data.get('elements', []):
            tags = el.get('tags', {})
            geom = el.get('geometry', [])
            print(f"\nID: {el.get('type')}/{el.get('id')}")
            print(f"  tags: highway={tags.get('highway')}, railway={tags.get('railway')}, name={tags.get('name')}, ref={tags.get('ref')}, service={tags.get('service')}")
            print(f"  points count: {len(geom)}")
            if len(geom) > 0:
                print(f"  sample: lat={geom[0]['lat']}, lon={geom[0]['lon']} -> lat={geom[-1]['lat']}, lon={geom[-1]['lon']}")
                # print points between lon 10.287 and 10.291
                mid_pts = [p for p in geom if 10.287 <= p['lon'] <= 10.291]
                if mid_pts:
                    print(f"  mid_pts sample: {[ (round(p['lat'], 6), round(p['lon'], 6)) for p in mid_pts[:5] ]}")
except Exception as e:
    print(f"Overpass query error: {e}")

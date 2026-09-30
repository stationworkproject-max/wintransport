import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Let's test routing between each pair of candidates to see which combination produces a direct straight route!

pts_taoufik = {
    'aller_osm': (36.8321978, 10.154312),
    'retour_osm': (36.8316956, 10.1529334),
}

pts_campus = {
    'aller_osm': (36.8251118, 10.1439852),
    'retour_osm': (36.8253694, 10.1438886),
}

pts_14jan = {
    'aller_osm': (36.823507, 10.1418129),
    'retour_osm': (36.823507, 10.1414964),
}

def get_osrm_dist(p1, p2):
    url = f"https://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=false"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            if data.get('code') == 'Ok':
                return data['routes'][0]['distance']
    except Exception as e:
        return str(e)
    return None

print("=== TESTING TAOUFIK -> CAMPUS (ALLER: North -> South towards Bardo) ===")
for tk, tv in pts_taoufik.items():
    for ck, cv in pts_campus.items():
        d = get_osrm_dist(tv, cv)
        print(f"  {tk} -> {ck}: distance = {d}m")

print("\n=== TESTING CAMPUS -> 14 JANVIER (ALLER: North -> South towards Bardo) ===")
for ck, cv in pts_campus.items():
    for jk, jv in pts_14jan.items():
        d = get_osrm_dist(cv, jv)
        print(f"  {ck} -> {jk}: distance = {d}m")

print("\n=== TESTING 14 JANVIER -> CAMPUS (RETOUR: South -> North towards Taoufik) ===")
for jk, jv in pts_14jan.items():
    for ck, cv in pts_campus.items():
        d = get_osrm_dist(jv, cv)
        print(f"  {jk} -> {ck}: distance = {d}m")

print("\n=== TESTING CAMPUS -> TAOUFIK (RETOUR: South -> North towards Taoufik) ===")
for ck, cv in pts_campus.items():
    for tk, tv in pts_taoufik.items():
        d = get_osrm_dist(cv, tv)
        print(f"  {ck} -> {tk}: distance = {d}m")

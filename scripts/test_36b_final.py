import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

stops_36b_aller = [
    ("1. Terminus Ministere", 36.829562, 10.159038),
    ("2. Clinique Taoufik Aller", 36.831696, 10.152933),
    ("3. Campus Aller", 36.825369, 10.143889),
    ("4. 14 Janvier 2011 Aller", 36.823508, 10.141495),
    ("5. Foyer Bardo 2 Aller", 36.818349, 10.141493),
    ("6. Foyer Bardo 1 Aller", 36.813941, 10.146199),
    ("7. Cafe El Haj Aller", 36.812810, 10.144989),
    ("8. Touta Bardo", 36.808844, 10.137977),
]

stops_36b_retour = [
    ("1. Touta Bardo", 36.808844, 10.137977),
    ("2. Cafe El Haj", 36.812835, 10.145171),
    ("3. Foyer Bardo 1", 36.814154, 10.146217),
    ("4. Foyer Bardo 2", 36.818640, 10.141400),
    ("5. Centre de Formation Ras Tabia", 36.820024, 10.139791),
    ("6. 14 Janvier 2011", 36.823507, 10.141813),
    ("7. Campus Retour", 36.825350, 10.144100),
    ("8. Clinique Taoufik Retour", 36.832198, 10.154312),
    ("9. Terminus Ministere", 36.829562, 10.159038),
]

def test(name, stops):
    coords = ";".join([f"{s[2]},{s[1]}" for s in stops])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"\n=======================================================")
        print(f"=== {name} ({len(stops)} stops) -> Total: {r['distance']:.0f}m ===")
        print(f"=======================================================")
        for i, leg in enumerate(r['legs']):
            s1 = stops[i]
            s2 = stops[i+1]
            crow = 1000 * (((s1[1]-s2[1])*111)**2 + ((s1[2]-s2[2])*89)**2)**0.5
            ratio = leg['distance'] / max(1.0, crow)
            warn = " *** DETOUR ***" if ratio > 1.8 and leg['distance'] > 300 else ""
            print(f"  Leg {i+1:2d}->{i+2:2d} ({s1[0][:23]:23s} -> {s2[0][:23]:23s}): {leg['distance']:5.0f}m [crow: {crow:4.0f}m, ratio: {ratio:.2f}]{warn}")

test("Line 36B ALLER", stops_36b_aller)
test("Line 36B RETOUR", stops_36b_retour)

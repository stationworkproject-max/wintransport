import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Current 36B Aller from staticTransit
stops_36b_aller = [
    ("1. Terminus Ministere", 36.829562, 10.159038),
    ("2. Clinique Taoufik", 36.831657, 10.152977),
    ("3. Campus", 36.825369, 10.143889),
    ("4. 14 Janvier 2011", 36.823508, 10.141495),
    ("5. Foyer Bardo 2", 36.818349, 10.141493),
    ("6. Foyer Bardo 1", 36.813941, 10.146199),
    ("7. Cafe El Haj", 36.812810, 10.144989),
    ("8. Touta Bardo", 36.808844, 10.137977),
]

# Current 36B Retour from staticTransit
stops_36b_retour = [
    ("1. Touta Bardo", 36.808844, 10.137977),
    ("2. Cafe El Haj", 36.812835, 10.145171),
    ("3. Foyer Bardo 1", 36.814154, 10.146217),
    ("4. Foyer Bardo 2", 36.818640, 10.141400),
    ("5. Centre de Formation Ras Tabia", 36.820024, 10.139791),
    ("6. 14 Janvier 2011", 36.823507, 10.141813),
    ("7. Campus", 36.825112, 10.143985),
    ("8. Clinique Taoufik", 36.832198, 10.154312),
    ("9. Terminus Ministere", 36.829562, 10.159038),
]

def analyze(name, stops):
    coords = ";".join([f"{s[2]},{s[1]}" for s in stops])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson&steps=true"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"\n==========================================")
        print(f"=== {name} (total {r['distance']:.0f}m) ===")
        print(f"==========================================")
        for i, leg in enumerate(r['legs']):
            s1 = stops[i]
            s2 = stops[i+1]
            crow = 1000 * (((s1[1]-s2[1])*111)**2 + ((s1[2]-s2[2])*89)**2)**0.5
            ratio = leg['distance'] / max(1.0, crow)
            warn = " *** DETOUR ***" if ratio > 1.8 and leg['distance'] > 300 else ""
            print(f"  Leg {i+1:2d} ({s1[0][:20]:20s} -> {s2[0][:20]:20s}): {leg['distance']:5.0f}m [crow: {crow:4.0f}m, ratio: {ratio:.2f}]{warn}")
            # print steps that look suspicious
            for st in leg['steps']:
                man = st['maneuver']
                if man.get('modifier') in ['uturn', 'sharp left', 'sharp right'] or 'roundabout' in man.get('type'):
                    print(f"      Maneuver: {man.get('type')} {man.get('modifier', '')} on '{st.get('name')}' ({st['distance']:.0f}m)")

analyze("36B ALLER (Current)", stops_36b_aller)
analyze("36B RETOUR (Current)", stops_36b_retour)

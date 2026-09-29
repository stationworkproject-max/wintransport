import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def test_steps(name, stops):
    coords = ";".join([f"{s[2]},{s[1]}" for s in stops])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson&steps=true"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"\n==========================================")
        print(f"=== {name} (total {r['distance']:.0f}m) ===")
        print(f"==========================================")
        for i, leg in enumerate(r['legs']):
            s1, s2 = stops[i], stops[i+1]
            print(f"\n--- Leg {i+1}: {s1[0]} -> {s2[0]} ({leg['distance']:.0f}m) ---")
            for st in leg['steps']:
                mod = f" ({st['maneuver'].get('modifier')})" if st['maneuver'].get('modifier') else ""
                print(f"    {st['maneuver']['type']}{mod:12s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

# 1. 846 Aller stops 1 to 5
stops_846_aller_sample = [
    ("1. Terminus Ministere", 36.829562, 10.159038),
    ("2. Clinique Taoufik", 36.831657, 10.152977),
    ("3. Campus", 36.825369, 10.143889),
    ("4. 14 Janvier 2011", 36.823508, 10.141495),
    ("5. Foyer Bardo 2", 36.818349, 10.141493),
    ("6. Foyer Bardo 1", 36.813941, 10.146199),
]
test_steps("846 Aller Sample (1-6)", stops_846_aller_sample)

# 2. 847 Aller stops 8 to 13
stops_847_aller_sample = [
    ("8. Chedly Zouiten", 36.829621, 10.170550),
    ("9. Municipalite Mutuelle", 36.833778, 10.167208),
    ("10. RX", 36.838561, 10.166151),
    ("11. SONED", 36.836053, 10.160626),
    ("12. Clinique Taoufik", 36.832198, 10.154312),
    ("13. Faculte de Droit", 36.830720, 10.150380),
]
test_steps("847 Aller Sample (8-13, raw coords)", stops_847_aller_sample)

# 3. 847 Retour stops 5 to 11
stops_847_retour_sample = [
    ("5. Faculte des Sciences", 36.832833, 10.148073),
    ("6. Faculte de Droit", 36.830720, 10.150380),
    ("7. Clinique Taoufik", 36.832198, 10.154312),
    ("8. SONED", 36.836053, 10.160626),
    ("9. RX", 36.838561, 10.166151),
    ("10. Municipalite Mutuelle", 36.833778, 10.167208),
    ("11. Chedly Zouiten", 36.829621, 10.170550),
]
test_steps("847 Retour Sample (5-11, raw coords)", stops_847_retour_sample)

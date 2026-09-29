import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------
# LINE 36B (bus_846)
# ---------------------------------------------------------
# Aller: Ministére Des Affaires Etrangeres -> Bardo
stops_36b_aller = [
    ("1. Terminus Ministere", 36.829562, 10.159038),
    ("2. Clinique Taoufik", 36.832431, 10.154153), # Westbound
    ("3. Campus", 36.825369, 10.143889),           # Westbound
    ("4. 14 Janvier 2011", 36.823508, 10.141495),  # Westbound
    ("5. Foyer Bardo 2", 36.818349, 10.141493),
    ("6. Foyer Bardo 1", 36.813941, 10.146199),
    ("7. Cafe El Haj", 36.812810, 10.144989),
    ("8. Touta Bardo", 36.808844, 10.137977),
]

# Retour: Bardo -> Ministére Des Affaires Etrangeres
stops_36b_retour = [
    ("1. Touta Bardo", 36.808844, 10.137977),
    ("2. Cafe El Haj", 36.812835, 10.145171),
    ("3. Foyer Bardo 1", 36.814154, 10.146217),
    ("4. Foyer Bardo 2", 36.818640, 10.141400),
    ("5. Centre de Formation Ras Tabia", 36.820024, 10.139791),
    ("6. 14 Janvier 2011", 36.823507, 10.141813),  # Eastbound
    ("7. Campus", 36.825350, 10.144100),           # Eastbound mainline
    ("8. Clinique Taoufik", 36.832309, 10.154203), # Eastbound
    ("9. Terminus Ministere", 36.829562, 10.159038),
]

# ---------------------------------------------------------
# LINE 38B (bus_847)
# ---------------------------------------------------------
# Aller: Tunis Marine -> Omrane Supérieur
stops_38b_aller = [
    ("1. Terminus Tunis Marine", 36.800384, 10.190388),
    ("2. Jeans Jaures", 36.801618, 10.183899),
    ("3. STEG Jeans Jaures", 36.805500, 10.181998),
    ("4. Passage Jeans Jaures", 36.806911, 10.181536),
    ("5. La Fayette", 36.810562, 10.180724),
    ("6. Place Jeanne d'Arc", 36.818357, 10.179579),
    ("7. Place Pasteur", 36.823094, 10.177674),
    ("8. Chedly Zouiten", 36.829621, 10.170550),
    ("9. Municipalite Mutuelleville", 36.833778, 10.167208),
    ("10. RX", 36.838000, 10.165300),
    ("11. SONED", 36.835931, 10.160730),           # Westbound
    ("12. Clinique Taoufik", 36.832431, 10.154153), # Westbound
    ("13. Faculte de Droit", 36.830720, 10.150380), # Westbound
    ("14. Faculte des Sciences", 36.832833, 10.148073),
    ("15. Carrefour", 36.836543, 10.144694),
    ("16. Maison des Mamans", 36.835397, 10.138117),
    ("17. Foyer Omrane Superieur", 36.836190, 10.132044),
    ("18. Terminus Omrane Superieur", 36.836859, 10.129029),
]

# Retour: Omrane Supérieur -> Tunis Marine
stops_38b_retour = [
    ("1. Terminus Omrane Superieur", 36.836859, 10.129029),
    ("2. Foyer Omrane Superieur", 36.836190, 10.132044),
    ("3. Maison des Mamans", 36.835397, 10.138117),
    ("4. Carrefour", 36.836543, 10.144694),
    ("5. Faculte des Sciences", 36.832833, 10.148073),
    ("6. Faculte de Droit", 36.830720, 10.150160), # Eastbound
    ("7. Clinique Taoufik", 36.832309, 10.154203), # Eastbound
    ("8. SONED", 36.835836, 10.160810),           # Eastbound
    ("9. RX", 36.835486, 10.166438),              # Eastbound Jugurtha entrance
    ("10. Municipalite Mutuelleville", 36.833770, 10.167180),
    ("11. Chedly Zouiten", 36.829621, 10.170550),
    ("12. Place Pasteur", 36.823108, 10.177685),
    ("13. Place Jeanne d'Arc", 36.819920, 10.181580),
    ("14. La Fayette", 36.810986, 10.184607),
    ("15. Passage Jeans Jaures", 36.807310, 10.185221),
    ("16. STEG Jeans Jaures", 36.805868, 10.185461),
    ("17. Jeans Jaures", 36.803375, 10.185868),
    ("18. Terminus Tunis Marine", 36.800384, 10.190388),
]

def test_line(title, stops):
    coords = ";".join([f"{s[2]},{s[1]}" for s in stops])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"\n=======================================================")
        print(f"=== {title} ({len(stops)} stops) -> Total: {r['distance']:.0f}m ===")
        print(f"=======================================================")
        for i, leg in enumerate(r['legs']):
            s1 = stops[i]
            s2 = stops[i+1]
            crow = 1000 * (((s1[1]-s2[1])*111)**2 + ((s1[2]-s2[2])*89)**2)**0.5
            ratio = leg['distance'] / max(1.0, crow)
            warn = " *** DETOUR ***" if ratio > 1.8 and leg['distance'] > 300 else ""
            print(f"  Leg {i+1:2d}->{i+2:2d} ({s1[0][:22]:22s} -> {s2[0][:22]:22s}): {leg['distance']:5.0f}m [crow: {crow:4.0f}m, ratio: {ratio:.2f}]{warn}")

test_line("Line 36B ALLER", stops_36b_aller)
test_line("Line 36B RETOUR", stops_36b_retour)
test_line("Line 38B ALLER", stops_38b_aller)
test_line("Line 38B RETOUR", stops_38b_retour)

import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

stops_38b_retour_fixed = [
    ("1. Terminus Omrane Superieur", 36.836859, 10.129029),
    ("2. Foyer Omrane Superieur", 36.836190, 10.132044),
    ("3. Maison des Mamans", 36.835397, 10.138117),
    ("4. Carrefour", 36.836543, 10.144694),
    ("5. Faculte des Sciences", 36.832833, 10.148073),
    ("6. Faculte de Droit", 36.830720, 10.150160),
    ("7. Clinique Taoufik", 36.832309, 10.154203), # Exactly on eastbound carriageway
    ("8. SONED", 36.835836, 10.160810),           # Exactly on eastbound carriageway
    ("9. RX", 36.835486, 10.166438),              # Exactly on eastbound Avenue Jugurtha
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

coords = ";".join([f"{s[2]},{s[1]}" for s in stops_38b_retour_fixed])
url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    data = json.loads(resp.read())
    r = data['routes'][0]
    print(f"Total distance 38B Retour: {r['distance']:.0f}m")
    for i, leg in enumerate(r['legs']):
        s1 = stops_38b_retour_fixed[i]
        s2 = stops_38b_retour_fixed[i+1]
        direct = 1000 * (((s1[1]-s2[1])*111)**2 + ((s1[2]-s2[2])*89)**2)**0.5
        ratio = leg['distance'] / max(1.0, direct)
        warn = " *** DETOUR ***" if ratio > 1.8 and leg['distance'] > 300 else ""
        print(f"  Leg {i+1:2d}->{i+2:2d} ({s1[0][:20]:20s} -> {s2[0][:20]:20s}): {leg['distance']:5.0f}m (ratio: {ratio:.2f}){warn}")

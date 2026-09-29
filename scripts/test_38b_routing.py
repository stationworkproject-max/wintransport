import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

st_38b_aller = [
    ("1. Terminus Tunis Marine", 36.800384, 10.190388),
    ("2. Jeans Jaures", 36.801618, 10.183899),
    ("3. STEG Jeans Jaures", 36.805500, 10.181998),
    ("4. Passage Jeans Jaures", 36.806911, 10.181536),
    ("5. La Fayette", 36.810562, 10.180724),
    ("6. Place Jeanne d'Arc", 36.818357, 10.179579),
    ("7. Place Pasteur", 36.823094, 10.177674),
    ("8. Chedly Zouiten", 36.829621, 10.170550),
    ("9. Municipalite Mutuelleville", 36.833778, 10.167208),
    ("10. RX", 36.838561, 10.166151),
    ("11. SONED", 36.836053, 10.160626),
    ("12. Clinique Taoufik", 36.832198, 10.154312),
    ("13. Faculte de Droit", 36.830720, 10.150380),
    ("14. Faculte des Sciences", 36.832833, 10.148073),
    ("15. Carrefour", 36.836543, 10.144694),
    ("16. Maison des Mamans", 36.835397, 10.138117),
    ("17. Foyer Omrane Superieur", 36.836190, 10.132044),
    ("18. Terminus Omrane Superieur", 36.836859, 10.129029),
]

st_38b_retour = [
    ("1. Terminus Omrane Superieur", 36.836859, 10.129029),
    ("2. Foyer Omrane Superieur", 36.836190, 10.132044),
    ("3. Maison des Mamans", 36.835397, 10.138117),
    ("4. Carrefour", 36.836543, 10.144694),
    ("5. Faculte des Sciences", 36.832833, 10.148073),
    ("6. Faculte de Droit", 36.830720, 10.150380),
    ("7. Clinique Taoufik", 36.832198, 10.154312),
    ("8. SONED", 36.836053, 10.160626),
    ("9. RX", 36.838561, 10.166151),
    ("10. Municipalite Mutuelleville", 36.833778, 10.167208),
    ("11. Chedly Zouiten", 36.829621, 10.170550),
    ("12. Place Pasteur", 36.823094, 10.177674),
    ("13. Place Jeanne d'Arc", 36.818357, 10.179579),
    ("14. La Fayette", 36.810562, 10.180724),
    ("15. Passage Jeans Jaures", 36.806911, 10.181536),
    ("16. STEG Jeans Jaures", 36.805500, 10.181998),
    ("17. Jeans Jaures", 36.801618, 10.183899),
    ("18. Terminus Tunis Marine", 36.800384, 10.190388),
]

def check_route(name, stops):
    print(f"\n=== Routing {name} ===")
    coords = ";".join([f"{s[2]},{s[1]}" for s in stops])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            route = data['routes'][0]
            print(f"Total distance: {route['distance']:.0f}m")
            for i, leg in enumerate(route['legs']):
                s1, s2 = stops[i], stops[i+1]
                direct = 1000 * ( ( (s1[1]-s2[1])*111)**2 + ((s1[2]-s2[2])*89)**2 )**0.5
                ratio = leg['distance'] / max(1.0, direct)
                warn = " *** DETOUR ***" if ratio > 1.8 and leg['distance'] > 400 else ""
                print(f"  Leg {i+1:2d}->{i+2:2d} ({s1[0][:20]:20s} -> {s2[0][:20]:20s}): {leg['distance']:5.0f}m (direct: {direct:4.0f}m, ratio: {ratio:.2f}){warn}")
    except Exception as e:
        print("OSRM error:", e)

check_route("38B Aller", st_38b_aller)
check_route("38B Retour", st_38b_retour)

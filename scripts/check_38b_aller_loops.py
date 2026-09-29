import urllib.request
import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

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
    ("11. SONED", 36.835931, 10.160730),
    ("12. Clinique Taoufik", 36.832431, 10.154153),
    ("13. Faculte de Droit", 36.830720, 10.150380),
    ("14. Faculte des Sciences", 36.832833, 10.148073),
    ("15. Carrefour", 36.836543, 10.144694),
    ("16. Maison des Mamans", 36.835397, 10.138117),
    ("17. Foyer Omrane Superieur", 36.836190, 10.132044),
    ("18. Terminus Omrane Superieur", 36.836859, 10.129029),
]

coords = ";".join([f"{s[2]},{s[1]}" for s in stops_38b_aller])
url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    d = json.loads(resp.read())
    pts = [[c[1], c[0]] for c in d['routes'][0]['geometry']['coordinates']]

def haversine(c1, c2):
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

print(f"Total points: {len(pts)}")
loops = []
for i in range(len(pts)):
    for j in range(i + 15, len(pts)):
        crow = haversine(pts[i], pts[j])
        along = sum(haversine(pts[m], pts[m+1]) for m in range(i, j))
        if crow < 40 and along > 300:
            loops.append((i, j, crow, along, pts[i]))

print(f"Detected {len(loops)} loops in 38B Aller shape")
for l in loops[:5]:
    print(f"  Pts {l[0]}->{l[1]}: crow={l[2]:.1f}m, along={l[3]:.0f}m at {l[4]}")

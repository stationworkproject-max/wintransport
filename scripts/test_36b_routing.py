import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 36B Aller from arcgis
st_36b_aller = [
    ("1. Terminus Affaires Etrangeres", 36.829562, 10.159038),
    ("2. Clinique Taoufik", 36.831696, 10.152933),
    ("3. Campus", 36.825369, 10.143889),
    ("4. 14 Janvier 2011", 36.823507, 10.141496),
    ("5. Foyer Bardo 2", 36.818324, 10.141459),
    ("6. Foyer Bardo 1", 36.813941, 10.146199),
    ("7. Cafe El Haj", 36.812810, 10.144989),
    ("8. Touta Bardo", 36.808844, 10.137977),
]

st_36b_retour = [
    ("1. Touta Bardo", 36.808844, 10.137977),
    ("2. Cafe El Haj", 36.812835, 10.145171),
    ("3. Foyer Bardo 1", 36.814154, 10.146217),
    ("4. Foyer Bardo 2", 36.818640, 10.141400),
    ("5. Centre Form. Ras Tabia", 36.820024, 10.139791),
    ("6. 14 Janvier 2011", 36.823507, 10.141813),
    ("7. Campus", 36.825112, 10.143985),
    ("8. Clinique Taoufik", 36.832198, 10.154312),
    ("9. Terminus Affaires Etrangeres", 36.829562, 10.159038),
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
                print(f"  Leg {i+1}->{i+2} ({stops[i][0]} -> {stops[i+1][0]}): {leg['distance']:.0f}m")
    except Exception as e:
        print("OSRM error:", e)

check_route("36B Aller", st_36b_aller)
check_route("36B Retour", st_36b_retour)

import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------
# LINE 36B (bus_846)
# ---------------------------------------------------------
stops_36b_aller = [
    {"stop_id": 1, "name": "TERMINUS MINISTÉRE DES AFFAIRES ETRANGERES ( L 36 B )", "lat": 36.829562, "lon": 10.159038},
    {"stop_id": 2, "name": "CLINIQUE TAOUFIK ALLER", "lat": 36.831696, "lon": 10.152933},
    {"stop_id": 3, "name": "CAMPUS ALLER", "lat": 36.825369, "lon": 10.143889},
    {"stop_id": 4, "name": "14 JANVIER 2011 ALLER", "lat": 36.823508, "lon": 10.141495},
    {"stop_id": 5, "name": "FOYER BARDO 2 ALLER", "lat": 36.818349, "lon": 10.141493},
    {"stop_id": 6, "name": "FOYER BARDO 1 ALLER", "lat": 36.813941, "lon": 10.146199},
    {"stop_id": 7, "name": "CAFÉ EL HAJ ALLER", "lat": 36.812810, "lon": 10.144989},
    {"stop_id": 8, "name": "TOUTA BARDO", "lat": 36.808844, "lon": 10.137977},
]

stops_36b_retour = [
    {"stop_id": 1, "name": "TOUTA BARDO", "lat": 36.808844, "lon": 10.137977},
    {"stop_id": 2, "name": "CAFÉ EL HAJ RETOUR", "lat": 36.812835, "lon": 10.145171},
    {"stop_id": 3, "name": "FOYER BARDO 1 RETOUR", "lat": 36.814154, "lon": 10.146217},
    {"stop_id": 4, "name": "FOYER BARDO 2 RETOUR", "lat": 36.818640, "lon": 10.141400},
    {"stop_id": 5, "name": "CENTRE DE FORMATION RAS TABIA", "lat": 36.820024, "lon": 10.139791},
    {"stop_id": 6, "name": "14 JANVIER 2011 RETOUR", "lat": 36.823507, "lon": 10.141813},
    {"stop_id": 7, "name": "CAMPUS RETOUR", "lat": 36.825350, "lon": 10.144100},
    {"stop_id": 8, "name": "CLINIQUE TAOUFIK RETOUR", "lat": 36.832198, "lon": 10.154312},
    {"stop_id": 9, "name": "TERMINUS MINISTÉRE DES AFFAIRES ETRANGERES ( L 36 B )", "lat": 36.829562, "lon": 10.159038},
]

# ---------------------------------------------------------
# LINE 38B (bus_847)
# ---------------------------------------------------------
stops_38b_aller = [
    {"stop_id": 1, "name": "TERMINUS TUNIS MARINE BUS", "lat": 36.800384, "lon": 10.190388},
    {"stop_id": 2, "name": "JEANS JAURES", "lat": 36.801618, "lon": 10.183899},
    {"stop_id": 3, "name": "STEG JEANS JAURES ALLER", "lat": 36.805500, "lon": 10.181998},
    {"stop_id": 4, "name": "PASSAGE JEANS JAURES ALLER", "lat": 36.806911, "lon": 10.181536},
    {"stop_id": 5, "name": "LA FAYETTE ALLER", "lat": 36.810562, "lon": 10.180724},
    {"stop_id": 6, "name": "PLACE JEANS DARK ALLER", "lat": 36.818357, "lon": 10.179579},
    {"stop_id": 7, "name": "PLACE PASTEUR ALLER", "lat": 36.823094, "lon": 10.177674},
    {"stop_id": 8, "name": "CHEDLY ZOUITEN", "lat": 36.829621, "lon": 10.170550},
    {"stop_id": 9, "name": "MUNICIPALITÉ MUTUELLE VILLE", "lat": 36.833778, "lon": 10.167208},
    {"stop_id": 10, "name": "RX", "lat": 36.838000, "lon": 10.165300},
    {"stop_id": 11, "name": "SONED", "lat": 36.835931, "lon": 10.160730},
    {"stop_id": 12, "name": "CLINIQUE TAOUFIK ALLER", "lat": 36.832431, "lon": 10.154153},
    {"stop_id": 13, "name": "FACULTÉ DE DROIT", "lat": 36.830720, "lon": 10.150380},
    {"stop_id": 14, "name": "FACULTÉ DES SCIENCES DE TUNIS", "lat": 36.832833, "lon": 10.148073},
    {"stop_id": 15, "name": "CARREFOUR", "lat": 36.836543, "lon": 10.144694},
    {"stop_id": 16, "name": "MAISON DES MAMANS", "lat": 36.835397, "lon": 10.138117},
    {"stop_id": 17, "name": "FOYER OMRANE SUPÉRIEUR", "lat": 36.836190, "lon": 10.132044},
    {"stop_id": 18, "name": "TERMINUS OMRANE SUPÉRIEUR L 78 + 38 B", "lat": 36.836859, "lon": 10.129029},
]

stops_38b_retour = [
    {"stop_id": 1, "name": "TERMINUS OMRANE SUPÉRIEUR L 78 + 38 B", "lat": 36.836859, "lon": 10.129029},
    {"stop_id": 2, "name": "FOYER OMRANE SUPÉRIEUR", "lat": 36.836190, "lon": 10.132044},
    {"stop_id": 3, "name": "MAISON DES MAMANS", "lat": 36.835397, "lon": 10.138117},
    {"stop_id": 4, "name": "CARREFOUR", "lat": 36.836543, "lon": 10.144694},
    {"stop_id": 5, "name": "FACULTÉ DES SCIENCES DE TUNIS", "lat": 36.832833, "lon": 10.148073},
    {"stop_id": 6, "name": "FACULTÉ DE DROIT", "lat": 36.830720, "lon": 10.150160},
    {"stop_id": 7, "name": "CLINIQUE TAOUFIK RETOUR", "lat": 36.832309, "lon": 10.154203},
    {"stop_id": 8, "name": "SONED", "lat": 36.835836, "lon": 10.160810},
    {"stop_id": 9, "name": "RX", "lat": 36.835486, "lon": 10.166438},
    {"stop_id": 10, "name": "MUNICIPALITÉ MUTUELLE VILLE", "lat": 36.833770, "lon": 10.167180},
    {"stop_id": 11, "name": "CHEDLY ZOUITEN", "lat": 36.829621, "lon": 10.170550},
    {"stop_id": 12, "name": "PLACE PASTEUR ALLER", "lat": 36.823108, "lon": 10.177685},
    {"stop_id": 13, "name": "PLACE JEANS DARK ALLER", "lat": 36.819920, "lon": 10.181580},
    {"stop_id": 14, "name": "LA FAYETTE ALLER", "lat": 36.810986, "lon": 10.184607},
    {"stop_id": 15, "name": "PASSAGE JEANS JAURES ALLER", "lat": 36.807310, "lon": 10.185221},
    {"stop_id": 16, "name": "STEG JEANS JAURES ALLER", "lat": 36.805868, "lon": 10.185461},
    {"stop_id": 17, "name": "JEANS JAURES", "lat": 36.803375, "lon": 10.185868},
    {"stop_id": 18, "name": "TERMINUS TUNIS MARINE BUS", "lat": 36.800384, "lon": 10.190388},
]

routes = {
    "bus_846_0": stops_36b_aller,
    "bus_846_1": stops_36b_retour,
    "bus_847_0": stops_38b_aller,
    "bus_847_1": stops_38b_retour,
}

shapes_result = {}

for rkey, stops in routes.items():
    coords = ";".join([f"{s['lon']},{s['lat']}" for s in stops])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'TransitGenerator'})) as resp:
        data = json.loads(resp.read())
        r = data['routes'][0]
        # OSRM returns [lon, lat], our shapes need [lat, lon]
        pts = [[round(p[1], 5), round(p[0], 5)] for p in r['geometry']['coordinates']]
        shapes_result[rkey] = pts
        print(f"Generated {rkey}: {len(pts)} points, total distance: {r['distance']:.0f}m")

shapes_result["bus_846"] = shapes_result["bus_846_0"]
shapes_result["bus_847"] = shapes_result["bus_847_0"]

# Save generated shapes to temporary file for inspection
with open('scripts/generated_36b_38b_shapes.json', 'w', encoding='utf-8') as f:
    json.dump(shapes_result, f, indent=2)

print("\nGenerated shapes saved to scripts/generated_36b_38b_shapes.json successfully!")

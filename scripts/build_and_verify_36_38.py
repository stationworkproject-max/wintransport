import urllib.request
import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------
# LINE 36B (bus_846)
# ---------------------------------------------------------
stops_36b_aller = [
    {"id": "st-1", "stop_id": 1, "name": "TERMINUS MINISTÉRE DES AFFAIRES ETRANGERES ( L 36 B )", "lat": 36.830000, "lon": 10.157500, "horaires_count": 30},
    {"id": "st-2", "stop_id": 2, "name": "CLINIQUE TAOUFIK ALLER", "lat": 36.831696, "lon": 10.152933, "horaires_count": 30},
    {"id": "st-3", "stop_id": 3, "name": "CAMPUS ALLER", "lat": 36.825369, "lon": 10.143889, "horaires_count": 30},
    {"id": "st-4", "stop_id": 4, "name": "14 JANVIER 2011 ALLER", "lat": 36.823508, "lon": 10.141495, "horaires_count": 30},
    {"id": "st-5", "stop_id": 5, "name": "FOYER BARDO 2 ALLER", "lat": 36.818349, "lon": 10.141493, "horaires_count": 30},
    {"id": "st-6", "stop_id": 6, "name": "FOYER BARDO 1 ALLER", "lat": 36.813941, "lon": 10.146199, "horaires_count": 30},
    {"id": "st-7", "stop_id": 7, "name": "CAFÉ EL HAJ ALLER", "lat": 36.812810, "lon": 10.144989, "horaires_count": 30},
    {"id": "st-8", "stop_id": 8, "name": "TOUTA BARDO", "lat": 36.808844, "lon": 10.137977, "horaires_count": 30},
]

stops_36b_retour = [
    {"id": "st-1-r", "stop_id": 1, "name": "TOUTA BARDO", "lat": 36.808844, "lon": 10.137977, "horaires_count": 30},
    {"id": "st-2-r", "stop_id": 2, "name": "CAFÉ EL HAJ RETOUR", "lat": 36.812835, "lon": 10.145171, "horaires_count": 30},
    {"id": "st-3-r", "stop_id": 3, "name": "FOYER BARDO 1 RETOUR", "lat": 36.814154, "lon": 10.146217, "horaires_count": 30},
    {"id": "st-4-r", "stop_id": 4, "name": "FOYER BARDO 2 RETOUR", "lat": 36.818640, "lon": 10.141400, "horaires_count": 30},
    {"id": "st-5-r", "stop_id": 5, "name": "CENTRE DE FORMATION RAS TABIA", "lat": 36.820024, "lon": 10.139791, "horaires_count": 30},
    {"id": "st-6-r", "stop_id": 6, "name": "14 JANVIER 2011 RETOUR", "lat": 36.823507, "lon": 10.141813, "horaires_count": 30},
    {"id": "st-7-r", "stop_id": 7, "name": "CAMPUS RETOUR", "lat": 36.825350, "lon": 10.144100, "horaires_count": 30},
    {"id": "st-8-r", "stop_id": 8, "name": "CLINIQUE TAOUFIK RETOUR", "lat": 36.832198, "lon": 10.154312, "horaires_count": 30},
    {"id": "st-9-r", "stop_id": 9, "name": "TERMINUS MINISTÉRE DES AFFAIRES ETRANGERES ( L 36 B )", "lat": 36.829562, "lon": 10.159038, "horaires_count": 30},
]

# ---------------------------------------------------------
# LINE 38B (bus_847)
# ---------------------------------------------------------
stops_38b_aller = [
    {"id": "st-1", "stop_id": 1, "name": "TERMINUS TUNIS MARINE BUS", "lat": 36.800384, "lon": 10.190388, "horaires_count": 30},
    {"id": "st-2", "stop_id": 2, "name": "JEANS JAURES", "lat": 36.801618, "lon": 10.183899, "horaires_count": 30},
    {"id": "st-3", "stop_id": 3, "name": "STEG JEANS JAURES ALLER", "lat": 36.805500, "lon": 10.181998, "horaires_count": 30},
    {"id": "st-4", "stop_id": 4, "name": "PASSAGE JEANS JAURES ALLER", "lat": 36.806911, "lon": 10.181536, "horaires_count": 30},
    {"id": "st-5", "stop_id": 5, "name": "LA FAYETTE ALLER", "lat": 36.810562, "lon": 10.180724, "horaires_count": 30},
    {"id": "st-6", "stop_id": 6, "name": "PLACE JEANS DARK ALLER", "lat": 36.818357, "lon": 10.179579, "horaires_count": 30},
    {"id": "st-7", "stop_id": 7, "name": "PLACE PASTEUR ALLER", "lat": 36.823094, "lon": 10.177674, "horaires_count": 30},
    {"id": "st-8", "stop_id": 8, "name": "CHEDLY ZOUITEN", "lat": 36.829621, "lon": 10.170550, "horaires_count": 30},
    {"id": "st-9", "stop_id": 9, "name": "MUNICIPALITÉ MUTUELLE VILLE", "lat": 36.833778, "lon": 10.167208, "horaires_count": 30},
    {"id": "st-10", "stop_id": 10, "name": "RX", "lat": 36.838000, "lon": 10.165300, "horaires_count": 30},
    {"id": "st-11", "stop_id": 11, "name": "SONED", "lat": 36.835931, "lon": 10.160730, "horaires_count": 30},
    {"id": "st-12", "stop_id": 12, "name": "CLINIQUE TAOUFIK ALLER", "lat": 36.832431, "lon": 10.154153, "horaires_count": 30},
    {"id": "st-13", "stop_id": 13, "name": "FACULTÉ DE DROIT", "lat": 36.830720, "lon": 10.150380, "horaires_count": 30},
    {"id": "st-14", "stop_id": 14, "name": "FACULTÉ DES SCIENCES DE TUNIS", "lat": 36.832833, "lon": 10.148073, "horaires_count": 30},
    {"id": "st-15", "stop_id": 15, "name": "CARREFOUR", "lat": 36.836543, "lon": 10.144694, "horaires_count": 30},
    {"id": "st-16", "stop_id": 16, "name": "MAISON DES MAMANS", "lat": 36.835397, "lon": 10.138117, "horaires_count": 30},
    {"id": "st-17", "stop_id": 17, "name": "FOYER OMRANE SUPÉRIEUR", "lat": 36.836190, "lon": 10.132044, "horaires_count": 30},
    {"id": "st-18", "stop_id": 18, "name": "TERMINUS OMRANE SUPÉRIEUR L 78 + 38 B", "lat": 36.836859, "lon": 10.129029, "horaires_count": 30},
]

stops_38b_retour = [
    {"id": "st-1-r", "stop_id": 1, "name": "TERMINUS OMRANE SUPÉRIEUR L 78 + 38 B", "lat": 36.836859, "lon": 10.129029, "horaires_count": 30},
    {"id": "st-2-r", "stop_id": 2, "name": "FOYER OMRANE SUPÉRIEUR", "lat": 36.836190, "lon": 10.132044, "horaires_count": 30},
    {"id": "st-3-r", "stop_id": 3, "name": "MAISON DES MAMANS", "lat": 36.835397, "lon": 10.138117, "horaires_count": 30},
    {"id": "st-4-r", "stop_id": 4, "name": "CARREFOUR", "lat": 36.836543, "lon": 10.144694, "horaires_count": 30},
    {"id": "st-5-r", "stop_id": 5, "name": "FACULTÉ DES SCIENCES DE TUNIS", "lat": 36.832833, "lon": 10.148073, "horaires_count": 30},
    {"id": "st-6-r", "stop_id": 6, "name": "FACULTÉ DE DROIT", "lat": 36.830720, "lon": 10.150160, "horaires_count": 30},
    {"id": "st-7-r", "stop_id": 7, "name": "CLINIQUE TAOUFIK RETOUR", "lat": 36.832309, "lon": 10.154203, "horaires_count": 30},
    {"id": "st-8-r", "stop_id": 8, "name": "SONED", "lat": 36.835836, "lon": 10.160810, "horaires_count": 30},
    {"id": "st-9-r", "stop_id": 9, "name": "RX", "lat": 36.835486, "lon": 10.166438, "horaires_count": 30},
    {"id": "st-10-r", "stop_id": 10, "name": "MUNICIPALITÉ MUTUELLE VILLE", "lat": 36.833770, "lon": 10.167180, "horaires_count": 30},
    {"id": "st-11-r", "stop_id": 11, "name": "CHEDLY ZOUITEN", "lat": 36.829621, "lon": 10.170550, "horaires_count": 30},
    {"id": "st-12-r", "stop_id": 12, "name": "PLACE PASTEUR ALLER", "lat": 36.823108, "lon": 10.177685, "horaires_count": 30},
    {"id": "st-13-r", "stop_id": 13, "name": "PLACE JEANS DARK ALLER", "lat": 36.819920, "lon": 10.181580, "horaires_count": 30},
    {"id": "st-14-r", "stop_id": 14, "name": "LA FAYETTE ALLER", "lat": 36.810986, "lon": 10.184607, "horaires_count": 30},
    {"id": "st-15-r", "stop_id": 15, "name": "PASSAGE JEANS JAURES ALLER", "lat": 36.807310, "lon": 10.185221, "horaires_count": 30},
    {"id": "st-16-r", "stop_id": 16, "name": "STEG JEANS JAURES ALLER", "lat": 36.805868, "lon": 10.185461, "horaires_count": 30},
    {"id": "st-17-r", "stop_id": 17, "name": "JEANS JAURES", "lat": 36.803375, "lon": 10.185868, "horaires_count": 30},
    {"id": "st-18-r", "stop_id": 18, "name": "TERMINUS TUNIS MARINE BUS", "lat": 36.800384, "lon": 10.190388, "horaires_count": 30},
]

routes = {
    "bus_846_0": stops_36b_aller,
    "bus_846_1": stops_36b_retour,
    "bus_847_0": stops_38b_aller,
    "bus_847_1": stops_38b_retour,
}

shapes_result = {}

def haversine(c1, c2):
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def check_loops(pts, min_crow=40, min_along=400):
    pref = [0.0]
    for m in range(len(pts)-1):
        pref.append(pref[-1] + haversine(pts[m], pts[m+1]))
    loops = []
    for i in range(len(pts)):
        for j in range(i + 10, len(pts)):
            along = pref[j] - pref[i]
            if along < min_along:
                continue
            crow = haversine(pts[i], pts[j])
            if crow < min_crow:
                loops.append((i, j, crow, along, pts[i]))
    return loops

for rkey, stops in routes.items():
    coords = ";".join([f"{s['lon']},{s['lat']}" for s in stops])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'TransitBuilder'})) as resp:
        data = json.loads(resp.read())
        r = data['routes'][0]
        pts = [[round(p[1], 5), round(p[0], 5)] for p in r['geometry']['coordinates']]
        shapes_result[rkey] = pts
        loops = check_loops(pts)
        print(f"Shape {rkey}: {len(pts)} pts, {r['distance']:.0f}m, loops: {len(loops)}")

shapes_result["bus_846"] = shapes_result["bus_846_0"]
shapes_result["bus_847"] = shapes_result["bus_847_0"]

# Save to shapes_to_apply.json
with open('scripts/shapes_to_apply.json', 'w', encoding='utf-8') as f:
    json.dump(shapes_result, f, indent=2)

# Save stops to apply
stops_to_apply = {
    "bus_846": {
        "stops_aller": stops_36b_aller,
        "stops_retour": stops_36b_retour
    },
    "bus_847": {
        "stops_aller": stops_38b_aller,
        "stops_retour": stops_38b_retour
    }
}
with open('scripts/stops_to_apply.json', 'w', encoding='utf-8') as f:
    json.dump(stops_to_apply, f, indent=2)

print("\nReady! Both shapes_to_apply.json and stops_to_apply.json created.")

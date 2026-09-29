import json
import math

def get_distance(p1, p2):
    R = 6371000
    dLat = math.radians(p2[0] - p1[0])
    dLon = math.radians(p2[1] - p1[1])
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(p1[0])) * math.cos(math.radians(p2[0])) * math.sin(dLon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

rw_path = r"C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson"
with open(rw_path, encoding='utf-8', errors='replace') as f:
    rw = json.load(f)

# Locations to test
test_locs = {
    "Metlaoui": (34.3157, 8.4164),
    "Redeyef": (34.3882, 8.1529),
    "Om El Arais": (34.4870, 8.2773),
    "Tabeddit": (34.4364, 8.2593),
    "Aguila": (34.3796, 8.7684),
    "Mdhilla": (34.2920, 8.7251),
    "Gafsa": (34.425, 8.784),
    "Bir Bourekba": (36.438, 10.591),
    "Nabeul": (36.456, 10.737)
}

features = rw['features']
print(f"Total railway features: {len(features)}")

for loc_name, pt in test_locs.items():
    nearby_tracks = 0
    min_dist = float('inf')
    for f in features:
        coords = f.get('geometry', {}).get('coordinates', [])
        # coordinates in geojson are [lon, lat]
        for c in coords:
            d = get_distance(pt, (c[1], c[0]))
            if d < min_dist:
                min_dist = d
            if d < 1000:
                nearby_tracks += 1
                break
    print(f"Location {loc_name}: closest railway track is {min_dist:.1f}m away (nearby tracks: {nearby_tracks})")

import json
import csv
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. Investigate Fej Etameur
print("=== INVESTIGATING Fej Etameur ===")
with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\stations.csv', 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if any(k in row.get('name', '').lower() or k in row.get('name_fr', '').lower() for k in ['fej', 'etameur', 'dahmani', 'mesria', 'gouraia']):
            print(f"CSV: {row.get('name')} | {row.get('name_fr')} | ({row['lat']}, {row['lon']})")

# Let's inspect railways near Fej Etameur (lat ~35.878, lon ~8.708)
with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson', 'r', encoding='utf-8') as f:
    rw = json.load(f)

print("\nRailways near Fej Etameur (lat 35.85 - 35.92, lon 8.65 - 8.75):")
fej_tracks = 0
for feat in rw['features']:
    geom = feat.get('geometry', {})
    coords = geom.get('coordinates', [])
    t = geom.get('type')
    coords_list = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in coords_list:
        in_bbox = False
        for p in line:
            if 35.85 <= p[1] <= 35.95 and 8.65 <= p[0] <= 8.75:
                in_bbox = True
                break
        if in_bbox:
            fej_tracks += 1
            print(f"  Track {feat.get('properties', {}).get('name')}: pts={len(line)}, start=({line[0][1]}, {line[0][0]}), end=({line[-1][1]}, {line[-1][0]})")

print(f"Total track features near Fej: {fej_tracks}")

# 2. Investigate Sidi Abid -> Gargour (near Sfax, lat ~34.6 to 34.7, lon ~10.6 to 10.75)
print("\n=== INVESTIGATING Sidi Abid -> Gargour ===")
for row in csv.DictReader(open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\stations.csv', 'r', encoding='utf-8-sig')):
    if any(k in row.get('name', '').lower() or k in row.get('name_fr', '').lower() for k in ['sidi abid', 'gargour', 'mahres', 'sfax']):
        print(f"CSV: {row.get('name')} | {row.get('name_fr')} | ({row['lat']}, {row['lon']})")

# Let's check tracks between Sidi Abid (34.68, 10.70) and Gargour (34.61, 10.58)
gargour_tracks = 0
for feat in rw['features']:
    geom = feat.get('geometry', {})
    coords = geom.get('coordinates', [])
    t = geom.get('type')
    coords_list = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
    for line in coords_list:
        in_bbox = False
        for p in line:
            if 34.55 <= p[1] <= 34.75 and 10.55 <= p[0] <= 10.75:
                in_bbox = True
                break
        if in_bbox:
            gargour_tracks += 1
            print(f"  Track: {feat.get('properties', {}).get('name')} {feat.get('properties', {}).get('ref')}: pts={len(line)}, start=({line[0][1]}, {line[0][0]}), end=({line[-1][1]}, {line[-1][0]})")

print(f"Total track features near Sfax-Gargour: {gargour_tracks}")

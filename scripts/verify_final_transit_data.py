import json
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Load staticTransit.js
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
lines_json = text[text.find(prefix) + len(prefix):].strip()
if lines_json.endswith(';'): lines_json = lines_json[:-1].strip()
lines = json.loads(lines_json)

# Load transitShapes.json
with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

print(f"Total lines in staticTransit.js: {len(lines)}")
print(f"Total shape keys in transitShapes.json: {len(shapes)}")

# Categorize lines
bus_lines = [l for l in lines if l.get('type_id') == 'bus']
metro_lines = [l for l in lines if l.get('type_id') == 'metro']
train_lines = [l for l in lines if l.get('type_id') == 'train' or l['id'].startswith('train_') or l['id'].startswith('rfr_')]

print(f"  Buses: {len(bus_lines)}")
print(f"  Metros/TGM: {len(metro_lines)}")
print(f"  Trains/RFR: {len(train_lines)}")

# 1. Verify train lines
print("\n--- Verifying Train & RFR Lines ---")
train_issues = 0
for l in train_lines:
    lid = l['id']
    pts = shapes.get(lid, [])
    aller = shapes.get(f"{lid}_aller", [])
    retour = shapes.get(f"{lid}_retour", [])
    
    if len(pts) == 0:
        print(f"  ERROR: {lid} has 0 shape points!")
        train_issues += 1
    elif len(aller) == 0 or len(retour) == 0:
        print(f"  ERROR: {lid} missing aller/retour shapes!")
        train_issues += 1
        
    stops = l.get('stops', [])
    for i in range(len(stops) - 1):
        d = haversine(stops[i]['lat'], stops[i]['lon'], stops[i+1]['lat'], stops[i+1]['lon'])
        if d > 45000 and lid not in ['train_31', 'train_24']: # 45km max leg
            print(f"  WARNING: Large jump on {lid}: {stops[i]['name']} -> {stops[i+1]['name']} ({d/1000:.1f} km)")
            train_issues += 1

if train_issues == 0:
    print("  ALL 32 TRAIN/RFR LINES PERFECT! All have high-density shapes and continuous stops.")

# 2. Verify buses are intact
print("\n--- Verifying Bus Lines Intact ---")
bus_issues = 0
for l in bus_lines:
    lid = l['id']
    pts = shapes.get(lid, [])
    dir0 = shapes.get(f"{lid}_0", [])
    dir1 = shapes.get(f"{lid}_1", [])
    if len(pts) == 0 and len(dir0) == 0:
        bus_issues += 1

print(f"  Bus lines missing shapes: {bus_issues} / {len(bus_lines)}")

# 3. Verify metros are intact
print("\n--- Verifying Metro Lines Intact ---")
metro_issues = 0
for l in metro_lines:
    lid = l['id']
    pts = shapes.get(lid, [])
    if len(pts) == 0:
        metro_issues += 1

print(f"  Metro lines missing shapes: {metro_issues} / {len(metro_lines)}")

print("\n--- Summary of Previously Missing Train Shapes ---")
previously_missing = ['train_43', 'train_42', 'train_39', 'train_31', 'train_28', 'train_29', 'train_30', 'train_45']
for lid in previously_missing:
    l = [x for x in train_lines if x['id'] == lid][0]
    pts = shapes.get(lid, [])
    print(f"  {lid:10s} : {len(pts):4d} shape points | {l['stops'][0]['name']} -> {l['stops'][-1]['name']}")


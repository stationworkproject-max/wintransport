import json
import csv
import math

def get_distance(p1, p2):
    R = 6371000
    dLat = math.radians(p2[0] - p1[0])
    dLon = math.radians(p2[1] - p1[1])
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(p1[0])) * math.cos(math.radians(p2[0])) * math.sin(dLon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Load stations from CSV
stations_csv = {}
with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\stations.csv', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row.get('name', '').strip()
        name_fr = row.get('name_fr', '').strip()
        lat = float(row['lat']) if row.get('lat') else None
        lon = float(row['lon']) if row.get('lon') else None
        if lat and lon:
            if name: stations_csv[name.lower()] = (lat, lon, name)
            if name_fr: stations_csv[name_fr.lower()] = (lat, lon, name_fr)

print(f"Loaded {len(stations_csv)} station name aliases from stations.csv")

# Load staticTransit.js
with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])
train_lines = [l for l in lines if l.get('type_id') in ['train', 'rfr']]
shapes = json.load(open('src/data/transitShapes.json', encoding='utf-8'))

print("\n=== TRAIN LINES STATUS IN PROJECT ===")
for l in train_lines:
    bid = l['id']
    sname = l['short_name']
    lname = ''.join([c for c in l['long_name'] if ord(c) < 128])
    shape = shapes.get(bid, [])
    stops = l.get('stops', [])
    
    # Check if shape is straight line or missing
    is_missing = len(shape) == 0
    is_straight = False
    if len(shape) > 1 and len(shape) <= len(stops) + 1:
        is_straight = True
        
    print(f"Line {bid} ({sname} - {lname}): {len(stops)} stops, shape points: {len(shape)}, missing: {is_missing}, straight: {is_straight}")
    
    # Check stations
    mismatches = []
    for s in stops:
        s_name = s.get('name', '').strip().lower()
        s_lat = s.get('lat')
        s_lon = s.get('lon')
        
        # Match with CSV
        match = stations_csv.get(s_name)
        if not match:
            # Try fuzzy match
            clean_s = s_name.replace('gare de ', '').replace('gare ', '').replace('voyageurs', '').replace('voy', '').strip()
            match = stations_csv.get(clean_s)
            
        if match:
            c_lat, c_lon, orig_name = match
            d = get_distance((s_lat, s_lon), (c_lat, c_lon))
            if d > 300: # shifted by >300m
                mismatches.append((s.get('name'), round(d), (s_lat, s_lon), (c_lat, c_lon)))
                
    if mismatches:
        print(f"  -> {len(mismatches)} stations shifted > 300m:")
        for m in mismatches[:5]:
            print(f"     * {m[0]}: current {m[2]} vs real {m[3]} (shift {m[1]}m)")

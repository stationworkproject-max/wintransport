import json

railways_path = r"C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson"
stations_path = r"C:\Users\AymenFrd\Desktop\MapTrans\Train\stations.geojson"

with open(railways_path, encoding='utf-8', errors='replace') as f:
    rw_data = json.load(f)

print(f"=== RAILWAYS.GEOJSON ===")
print(f"Type: {rw_data.get('type')}")
rw_features = rw_data.get('features', [])
print(f"Total railway features: {len(rw_features)}")
if rw_features:
    print("Sample railway feature properties:", rw_features[0].get('properties'))
    print("Sample railway geometry type:", rw_features[0].get('geometry', {}).get('type'))
    # List all unique properties across all railway features
    all_keys = set()
    for feat in rw_features:
        all_keys.update(feat.get('properties', {}).keys())
    print("All railway property keys:", all_keys)
    
    # Check sample lines/names/tags
    sample_tags = []
    for feat in rw_features[:10]:
        sample_tags.append(feat.get('properties'))
    for idx, p in enumerate(sample_tags[:5]):
        p_clean = {k: ''.join([c for c in str(v) if ord(c) < 128]) for k, v in p.items()}
        print(f"  [{idx+1}] {p_clean}")

with open(stations_path, encoding='utf-8', errors='replace') as f:
    st_data = json.load(f)

print(f"\n=== STATIONS.GEOJSON ===")
print(f"Type: {st_data.get('type')}")
st_features = st_data.get('features', [])
print(f"Total station features: {len(st_features)}")
if st_features:
    p0 = {k: ''.join([c for c in str(v) if ord(c) < 128]) for k, v in st_features[0].get('properties', {}).items()}
    print("Sample station feature properties:", p0)
    print("Sample station geometry type:", st_features[0].get('geometry', {}).get('type'))
    all_st_keys = set()
    for feat in st_features:
        all_st_keys.update(feat.get('properties', {}).keys())
    print("All station property keys:", all_st_keys)
    for feat in st_features[:10]:
        p = feat.get('properties', {})
        name = ''.join([c for c in str(p.get('name') or p.get('nom') or '') if ord(c) < 128])
        print(f"  Station: {name} (keys: {list(p.keys())})")

# Now check train lines in staticTransit.js
with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])
train_lines = [l for l in lines if l.get('type_id') in ['train', 'rfr']]
print(f"\n=== PROJECT TRAIN & RFR LINES ===")
print(f"Total train lines in staticTransit.js: {len(train_lines)}")
shapes = json.load(open('src/data/transitShapes.json', encoding='utf-8'))
for l in train_lines:
    shape = shapes.get(l['id'], [])
    name_clean = ''.join([c for c in str(l['long_name']) if ord(c) < 128])
    print(f"Line {l['id']} ({l['short_name']} - {name_clean}): {len(l.get('stops', []))} stops, shape points: {len(shape)}")

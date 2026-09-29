import json

rw_path = r"C:\Users\AymenFrd\Desktop\MapTrans\Train\railways.geojson"
with open(rw_path, encoding='utf-8', errors='replace') as f:
    rw = json.load(f)

features = rw['features']
print(f"Total railway tracks: {len(features)}")

# Check types of railways:
types = set(f.get('properties', {}).get('railway') for f in features)
print(f"Railway types: {types}")

def clean_str(s):
    return ''.join([c for c in str(s) if ord(c) < 128])

# Check operators:
operators = set(clean_str(f.get('properties', {}).get('operator')) for f in features)
print(f"Operators: {operators}")

# Check usage:
usages = set(clean_str(f.get('properties', {}).get('usage')) for f in features)
print(f"Usages: {usages}")

# Check gauges:
gauges = set(clean_str(f.get('properties', {}).get('gauge')) for f in features)
print(f"Gauges: {gauges}")

# Check names and refs:
refs = set(clean_str(f.get('properties', {}).get('ref')) for f in features if f.get('properties', {}).get('ref'))
names = set(clean_str(f.get('properties', {}).get('name')) for f in features if f.get('properties', {}).get('name'))
print(f"Unique refs: {refs}")
print(f"Unique names count: {len(names)}")
print("Sample refs/names:", list(refs)[:10], list(names)[:10])

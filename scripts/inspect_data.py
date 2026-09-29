import json
import re

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Match lines
# { "id": "bus_104", ... "short_name": "104", "long_name": ... }
bus_lines = []
pattern = re.compile(r'\{\s*"id":\s*"([^"]+)",\s*"route_id":\s*"([^"]+)",\s*"type_id":\s*"bus",\s*"short_name":\s*"([^"]+)",\s*"long_name":\s*"([^"]+)"')
for match in pattern.finditer(content):
    bus_lines.append({
        "id": match.group(1),
        "route_id": match.group(2),
        "short_name": match.group(3),
        "long_name": match.group(4)
    })

print(f"Total bus lines in staticTransit.js: {len(bus_lines)}")
print("Sample bus lines:", bus_lines[:10])

# Check shapes in transitShapes.json
with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

print(f"Total shapes in transitShapes.json: {len(shapes)}")
sample_shape_keys = list(shapes.keys())[:30]
print("Sample shape keys:", sample_shape_keys)

# How many bus lines actually have shapes in transitShapes.json?
with_shape = []
without_shape = []
with_dir_shape = []
for bl in bus_lines:
    has_base = bl["id"] in shapes and len(shapes[bl["id"]]) > 1
    has_dir0 = f"{bl['id']}_0" in shapes and len(shapes[f"{bl['id']}_0"]) > 1
    has_dir1 = f"{bl['id']}_1" in shapes and len(shapes[f"{bl['id']}_1"]) > 1
    if has_base or has_dir0 or has_dir1:
        with_shape.append(bl["id"])
    else:
        without_shape.append(bl["id"])
    if has_dir0 or has_dir1:
        with_dir_shape.append(bl["id"])

print(f"Bus lines with shapes: {len(with_shape)} / {len(bus_lines)}")
print(f"Bus lines with directional shapes (_0 or _1): {len(with_dir_shape)}")
print(f"Bus lines WITHOUT shapes: {len(without_shape)}")
if without_shape:
    print("Sample lines without shapes:", without_shape[:20])

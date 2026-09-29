import json
import re

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

test_ids = ['bus_772', 'bus_703', 'bus_773', 'bus_704', 'bus_705', 'bus_889']
for tid in test_ids:
    has_base = tid in shapes
    has_0 = f"{tid}_0" in shapes
    has_1 = f"{tid}_1" in shapes
    len_base = len(shapes[tid]) if has_base else 0
    len_0 = len(shapes[f"{tid}_0"]) if has_0 else 0
    len_1 = len(shapes[f"{tid}_1"]) if has_1 else 0
    print(f"{tid}: base={len_base}, _0={len_0}, _1={len_1}")

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r'\{\s*"id":\s*"(bus_[^"]+)",\s*"route_id":\s*"([^"]+)",\s*"type_id":\s*"bus",\s*"short_name":\s*"([^"]+)"')
all_bus = pattern.findall(text)

empty_shapes = []
for bid, rid, sname in all_bus:
    pts0 = shapes.get(f"{bid}_0", shapes.get(bid, []))
    pts1 = shapes.get(f"{bid}_1", [])
    if len(pts0) < 2:
        empty_shapes.append((bid, sname, len(pts0), len(pts1)))

print(f"Bus lines with less than 2 points in shape: {len(empty_shapes)}")
if empty_shapes:
    print("Empty shapes:", empty_shapes)

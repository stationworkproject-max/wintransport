import json
import re

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r'\{\s*"id":\s*"(bus_[^"]+)",\s*"route_id":\s*"([^"]+)",\s*"type_id":\s*"bus",\s*"short_name":\s*"([^"]+)",\s*"long_name":\s*"([^"]+)"')
all_bus = pattern.findall(text)

issues = []
for bid, rid, sname, lname in all_bus:
    shape0 = shapes.get(f"{bid}_0", shapes.get(bid, []))
    shape1 = shapes.get(f"{bid}_1", [])
    
    # check valid coords
    valid0 = True
    if len(shape0) < 2:
        valid0 = False
    else:
        for pt in shape0:
            if not (35.0 < pt[0] < 38.0 and 8.0 < pt[1] < 12.0):
                valid0 = False
                break
                
    valid1 = True
    if len(shape1) < 2:
        valid1 = False
    else:
        for pt in shape1:
            if not (35.0 < pt[0] < 38.0 and 8.0 < pt[1] < 12.0):
                valid1 = False
                break
                
    if not valid0 or not valid1:
        issues.append((bid, sname, valid0, len(shape0), valid1, len(shape1)))

print(f"Total bus lines checked: {len(all_bus)}")
print(f"Lines with shape issues: {len(issues)}")
for iss in issues[:30]:
    print(iss)

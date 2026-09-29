import re

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r'\{\s*"id":\s*"(bus_[^"]+)",\s*"route_id":\s*"([^"]+)",\s*"type_id":\s*"bus",\s*"short_name":\s*"([^"]+)",\s*"long_name":\s*"([^"]+)"')
all_bus = pattern.findall(text)

print(f"Total bus lines in staticTransit: {len(all_bus)}")
short_names = [b[2] for b in all_bus]
print("Bus short names (first 50):", short_names[:50])

# Check for lines like 23, 104, 35, 3D, 20, 116, 44A, 44B
for q in ['23', '104', '35', '3D', '20', '116', '44A', '44B', '14A', '14C']:
    matches = [b for b in all_bus if b[2].upper() == q.upper()]
    print(f"Query '{q}': matches = {matches}")

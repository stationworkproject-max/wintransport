import subprocess
import json
import re
import os

print("Restoring pristine bilingual transit data from commit 9820fe4...")

cmd = ['git', 'show', '9820fe4:src/data/staticTransit.js']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()
if p.returncode != 0:
    raise RuntimeError(f"Git error: {err.decode('utf-8', errors='ignore')}")

clean_content = out.decode('utf-8', errors='ignore')

# Verify clean_content contains all lines
m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);', clean_content, re.DOTALL)
if not m:
    raise ValueError("Could not parse STATIC_LINES from commit 9820fe4")

lines = json.loads(m.group(1))
print(f"Loaded {len(lines)} lines from clean commit 9820fe4.")

# Check bus lines
buses = [l for l in lines if l.get('type_id') == 'bus']
print(f"Total bus lines: {len(buses)}")
mourouj = sum(1 for b in buses if any('GROS' in s.get('name', '').upper() for s in b.get('stops', [])[:3]))
print(f"Bus lines with GROS in first 3 stops: {mourouj} (Expected: 2)")

# Write to src/data/staticTransit.js
static_path = os.path.join('src', 'data', 'staticTransit.js')
with open(static_path, 'w', encoding='utf-8') as f:
    f.write(clean_content)
print(f"Successfully restored {static_path} ({os.path.getsize(static_path)} bytes)")

# Load current transitShapes.json
shapes_path = os.path.join('src', 'data', 'transitShapes.json')
with open(shapes_path, 'r', encoding='utf-8') as f:
    shapes = json.load(f)
print(f"Loaded {len(shapes)} shapes from {shapes_path}")

# Update public/studio_data.js
studio_data_path = os.path.join('public', 'studio_data.js')
studio_data = {
    'lines': lines,
    'shapes': shapes
}
with open(studio_data_path, 'w', encoding='utf-8') as f:
    f.write('window.STUDIO_DATA = ' + json.dumps(studio_data, ensure_ascii=False) + ';\n')
print(f"Successfully updated {studio_data_path} ({os.path.getsize(studio_data_path)} bytes)")

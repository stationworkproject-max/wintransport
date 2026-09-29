import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
lines_json = text[text.find(prefix) + len(prefix):].strip()
if lines_json.endswith(';'): lines_json = lines_json[:-1].strip()
lines = json.loads(lines_json)

target_lines = [l for l in lines if '36b' in l.get('short_name', '').lower() or '36b' in l.get('id', '').lower() or '38b' in l.get('short_name', '').lower() or '38b' in l.get('id', '').lower() or '36 b' in l.get('short_name', '').lower() or '38 b' in l.get('short_name', '').lower()]

print(f"Found {len(target_lines)} matching lines:")
for l in target_lines:
    print(f"\nID: {l['id']} | Short: {l.get('short_name')} | Long: {l.get('long_name')}")
    print(f"  Stops count: {len(l.get('stops', []))}")
    print(f"  stops_aller: {len(l.get('stops_aller', []))}")
    print(f"  stops_retour: {len(l.get('stops_retour', []))}")
    print(f"  directions: {l.get('directions')}")

import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
idx = text.find(prefix)
lines = json.loads(text[idx + len(prefix):text.rfind(']') + 1])

for l in lines:
    if l.get('type_id') in ['rfr', 'metro', 'tgm', 'train']:
        print(f"id={l['id']:12s} | type={l.get('type_id'):6s} | name={l.get('short_name'):5s} | color={l.get('color'):8s} | stops={len(l.get('stops', []))}")

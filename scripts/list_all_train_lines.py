import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
idx = text.find(prefix)
lines_json = text[idx + len(prefix):].strip()
if lines_json.endswith(';'):
    lines_json = lines_json[:-1].strip()

lines = json.loads(lines_json)
print(f"Total lines in staticTransit.js: {len(lines)}")

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

train_lines = []
for line in lines:
    lid = line['id']
    is_train = (line.get('type_id') == 'train' or lid.startswith('train_') or lid.startswith('rfr_'))
    if is_train:
        shape_pts = shapes.get(lid, [])
        train_lines.append({
            'id': lid,
            'short_name': line.get('short_name', ''),
            'long_name': line.get('long_name', ''),
            'stops_count': len(line.get('stops', [])),
            'shape_pts': len(shape_pts),
            'first_stop': line.get('stops', [{}])[0].get('name') if line.get('stops') else None,
            'last_stop': line.get('stops', [{}])[-1].get('name') if line.get('stops') else None,
        })

print(f"\nTotal train/RFR lines: {len(train_lines)}")
for tl in train_lines:
    print(f"  {tl['id']:12s} | {tl['short_name']:6s} | {tl['stops_count']:2d} stops | {tl['shape_pts']:4d} pts | {tl['first_stop']} -> {tl['last_stop']} ({tl['long_name']})")

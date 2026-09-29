import json

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'export const STATIC_LINES = '
idx = text.find(prefix)
if idx != -1:
    lines_json_str = text[idx + len(prefix):].strip()
    if lines_json_str.endswith(';'):
        lines_json_str = lines_json_str[:-1].strip()
    static_lines = json.loads(lines_json_str)
    print(f"Successfully loaded {len(static_lines)} static lines.")
    
    train_lines = [l for l in static_lines if l.get('type_id') == 'train' or l['id'].startswith('train_') or l['id'].startswith('rfr_')]
    print(f"Found {len(train_lines)} train/rfr lines.")
    for l in train_lines:
        stops_cnt = len(l.get('stops', []))
        print(f"  {l['id']}: {l.get('short_name')} - {l.get('long_name')} ({stops_cnt} stops)")
else:
    print("Could not find prefix")

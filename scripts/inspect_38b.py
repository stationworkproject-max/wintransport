import json

with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
idx = text.find('export const STATIC_LINES = ')
lines = json.loads(text[idx + len('export const STATIC_LINES = '):].strip()[:-1])
bus_38b = [l for l in lines if l['short_name'] == '38B'][0]

print('=== 38B ALLER STOPS ===')
for i, s in enumerate(bus_38b['stops']):
    name = ''.join([c for c in s.get('name', '') if ord(c) < 128])
    print(f"[{i+1}] {s.get('stop_id')}: {name} - ({s.get('lat')}, {s.get('lon')})")

print('\n=== 38B RETOUR STOPS ===')
for i, s in enumerate(bus_38b.get('stops_retour', [])):
    name = ''.join([c for c in s.get('name', '') if ord(c) < 128])
    print(f"[{i+1}] {s.get('stop_id')}: {name} - ({s.get('lat')}, {s.get('lon')})")

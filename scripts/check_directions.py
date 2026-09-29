from parse_static_transit import static_lines

for lid in ['train_18', 'train_21', 'train_23', 'train_24', 'train_5', 'train_20']:
    l = [x for x in static_lines if x['id'] == lid][0]
    print(f"{lid:10s} : name='{l['long_name']}', directions={l.get('directions')}")
    stops = l.get('stops', [])
    print(f"  First stop: {stops[0]['name']}, Last stop: {stops[-1]['name']}")

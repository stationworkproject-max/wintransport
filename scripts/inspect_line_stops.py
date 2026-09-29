import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from parse_static_transit import static_lines

for lid in ['train_18', 'train_21', 'train_24', 'train_15', 'train_20']:
    l = [x for x in static_lines if x['id'] == lid][0]
    print(f"\n================== {lid}: {l['short_name']} - {l['long_name']} ==================")
    stops = l.get('stops', [])
    for idx, s in enumerate(stops):
        print(f"  {idx+1:2d}. {s['name']:30s} ({s['lat']:.5f}, {s['lon']:.5f}) [stop_id={s.get('stop_id')}]")

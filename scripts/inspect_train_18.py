import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from parse_static_transit import static_lines

l = [x for x in static_lines if x['id'] == 'train_18'][0]
print(f"train_18: {l['short_name']} - {l['long_name']}")
for idx, s in enumerate(l.get('stops', [])):
    print(f"  {idx+1:2d}. {s['name']:30s} ({s['lat']:.5f}, {s['lon']:.5f}) [stop_id={s.get('stop_id')}]")

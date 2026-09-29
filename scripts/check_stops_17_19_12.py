import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from parse_static_transit import static_lines

for lid in ['train_17', 'rfr_19', 'train_12']:
    l = [x for x in static_lines if x['id'] == lid][0]
    print(f"\n================ {lid}: {l['long_name']} (directions: {l.get('directions')}) ================")
    for i, s in enumerate(l['stops']):
        print(f"  {i+1:2d}. {s['name']:28s} ({s['lat']:.4f}, {s['lon']:.4f})")

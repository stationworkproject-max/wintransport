import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from parse_static_transit import static_lines

def analyze_line(lid):
    l = [x for x in static_lines if x['id'] == lid][0]
    stops = l['stops']
    print(f"\n================ {lid}: {l['long_name']} ================")
    for i, s in enumerate(stops):
        print(f"  {i+1:2d}. {s['name']:25s} lat={s['lat']:.4f}, lon={s['lon']:.4f}")

for lid in ['train_21', 'train_23', 'train_24', 'train_5', 'train_20']:
    analyze_line(lid)

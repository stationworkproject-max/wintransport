import json, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    lines = json.loads(re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', f.read(), re.DOTALL).group(1))

sample_ids = ['bus_846', 'bus_847', 'bus_772', 'bus_703', 'metro_50']
for sid in sample_ids:
    line = next((l for l in lines if l['id'] == sid), None)
    if line:
        print(f"\n==========================================")
        print(f"ID: {line['id']}")
        print(f"Short: {line.get('short_name')} | AR: {line.get('short_name_ar')}")
        print(f"Long FR: {line.get('long_name_fr')}")
        print(f"Long AR: {line.get('long_name_ar')}")
        print(f"Directions FR: {line.get('directions_fr')}")
        print(f"Directions AR: {line.get('directions_ar')}")
        aller = line.get('stops_aller', line.get('stops', []))
        if aller:
            s1 = aller[0]
            print(f"  First stop: FR='{s1.get('name_fr')}' | AR='{s1.get('name_ar')}' ({s1.get('lat')}, {s1.get('lon')})")
            s_last = aller[-1]
            print(f"  Last stop:  FR='{s_last.get('name_fr')}' | AR='{s_last.get('name_ar')}' ({s_last.get('lat')}, {s_last.get('lon')})")

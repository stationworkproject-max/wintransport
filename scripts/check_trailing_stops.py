import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from parse_static_transit import static_lines

def check_line(lid, term_name):
    l = [x for x in static_lines if x['id'] == lid][0]
    stops = l.get('stops', [])
    names = [s['name'] for s in stops]
    try:
        idx = names.index(term_name)
        main_stops = stops[:idx+1]
        trailing_stops = stops[idx+1:]
        print(f"\n{lid} ({l['long_name']}):")
        print(f"  Main run to {term_name}: {len(main_stops)} stops")
        print(f"  Trailing stops ({len(trailing_stops)}): {[s['name'] for s in trailing_stops]}")
        # check if trailing stops already appear in main_stops
        main_names = set(s['name'] for s in main_stops)
        for ts in trailing_stops:
            print(f"    '{ts['name']}' in main run? {ts['name'] in main_names}")
    except ValueError:
        print(f"Terminus {term_name} not found in {lid}")

check_line('train_18', 'Sfax')
check_line('train_21', 'Gabes')
check_line('train_23', 'Sousse Voyageurs')
check_line('train_24', 'Tozeur')
check_line('train_5', 'Dahmani')
check_line('train_20', 'Kalaa Khasba')

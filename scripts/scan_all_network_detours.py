import json
import urllib.request
import math
import time

def get_distance(p1, p2):
    R = 6371000
    dLat = math.radians(p2[0] - p1[0])
    dLon = math.radians(p2[1] - p1[1])
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(p1[0])) * math.cos(math.radians(p2[0])) * math.sin(dLon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

with open('src/data/staticTransit.js', encoding='utf-8') as f:
    text = f.read()
idx = text.find('export const STATIC_LINES = ')
lines = json.loads(text[idx + len('export const STATIC_LINES = '):].strip()[:-1])
bus_lines = [l for l in lines if l.get('type_id') == 'bus']

print(f"Loaded {len(bus_lines)} bus lines. Scanning for detours (ratio > 1.4 or detour > 250m)...")

detour_reports = []

for idx_b, line in enumerate(bus_lines):
    bid = line['id']
    sname = line['short_name']
    
    for dir_idx, dir_name in [(0, 'Aller'), (1, 'Retour')]:
        stops = line.get('stops_retour') if dir_idx == 1 and line.get('stops_retour') else line.get('stops', [])
        if len(stops) < 2:
            continue
            
        coords = [(s['lat'], s['lon']) for s in stops]
        coords_str = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in coords[:65]])
        url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=false"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DetourScanner/1.0'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
                if data.get('code') != 'Ok' or not data.get('routes'):
                    continue
                legs = data['routes'][0]['legs']
                for i, leg in enumerate(legs):
                    st = get_distance(coords[i], coords[i+1])
                    d_routed = leg['distance']
                    ratio = d_routed / max(st, 30)
                    detour = d_routed - st
                    
                    # Detect detour: ratio > 1.5 and detour > 250m
                    if ratio > 1.45 and detour > 250:
                        detour_reports.append({
                            'bid': bid,
                            'line': sname,
                            'dir': dir_name,
                            'leg_idx': i + 1,
                            'from_stop': stops[i].get('name'),
                            'to_stop': stops[i+1].get('name'),
                            'from_id': stops[i].get('stop_id'),
                            'to_id': stops[i+1].get('stop_id'),
                            'straight': int(st),
                            'routed': int(d_routed),
                            'detour': int(detour),
                            'ratio': round(ratio, 2)
                        })
            time.sleep(0.06)
        except Exception as e:
            pass
            
    if (idx_b + 1) % 25 == 0:
        print(f"  Progress: {idx_b + 1}/{len(bus_lines)} lines scanned. Found {len(detour_reports)} detours so far.")

print(f"\nScan complete! Found {len(detour_reports)} total detours across the network.")
with open('scripts/detour_reports.json', 'w', encoding='utf-8') as f:
    json.dump(detour_reports, f, indent=2, ensure_ascii=False)

# Group by line
by_line = {}
for r in detour_reports:
    k = f"{r['line']} ({r['bid']})"
    if k not in by_line: by_line[k] = []
    by_line[k].append(r)

print(f"Total lines affected: {len(by_line)}")
for k, v in list(by_line.items())[:15]:
    print(f"\nLine {k} has {len(v)} detour legs:")
    for d in v:
        print(f"  [{d['dir']} Leg {d['leg_idx']}->{d['leg_idx']+1}] {d['from_stop']} -> {d['to_stop']}: straight {d['straight']}m, routed {d['routed']}m (+{d['detour']}m, {d['ratio']}x)")

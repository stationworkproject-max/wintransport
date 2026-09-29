import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

from parse_static_transit import static_lines
train_lines = [l for l in static_lines if l.get('type_id') == 'train' or l['id'].startswith('train_') or l['id'].startswith('rfr_')]

for l in train_lines:
    lid = l['id']
    lname = l.get('long_name', '')
    stops = l.get('stops', [])
    
    # Check distances between consecutive stops
    big_jumps = []
    for i in range(len(stops) - 1):
        s1 = stops[i]
        s2 = stops[i+1]
        d = haversine(s1['lat'], s1['lon'], s2['lat'], s2['lon'])
        if d > 50000: # Jump > 50km between consecutive stops!
            big_jumps.append((i, s1['name'], s2['name'], d))
            
    if big_jumps:
        print(f"\nLine {lid}: {lname} (stops: {len(stops)}) has {len(big_jumps)} big jumps:")
        for idx, s1, s2, d in big_jumps:
            print(f"  Step {idx+1}->{idx+2}: {s1} -> {s2} ({d/1000:.1f} km)")

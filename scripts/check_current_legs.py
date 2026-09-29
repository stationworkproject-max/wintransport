import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Read staticTransit.js stops for bus_846 and bus_847
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

def get_line_stops(line_id):
    pos = text.find(f'"{line_id}"')
    chunk = text[pos:pos+15000]
    # parse stops_aller
    aller_start = chunk.find('"stops_aller": [')
    aller_end = chunk.find('],', aller_start) + 1
    stops_aller = json.loads(chunk[aller_start + 15:aller_end])
    
    retour_start = chunk.find('"stops_retour": [')
    retour_end = chunk.find(']', retour_start) + 1
    stops_retour = json.loads(chunk[retour_start + 16:retour_end])
    return stops_aller, stops_retour

lines = ['bus_846', 'bus_847']

for lid in lines:
    aller, retour = get_line_stops(lid)
    for name, stops in [(f"{lid} ALLER", aller), (f"{lid} RETOUR", retour)]:
        print(f"\n==========================================")
        print(f"=== {name} ({len(stops)} stops) ===")
        print(f"==========================================")
        coords = ";".join([f"{s['lon']},{s['lat']}" for s in stops])
        url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=false"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
                data = json.loads(resp.read())
                route = data['routes'][0]
                print(f"Total OSRM Distance: {route['distance']:.0f}m")
                for i, leg in enumerate(route['legs']):
                    s1 = stops[i]
                    s2 = stops[i+1]
                    d_crow = 1000 * (((s1['lat']-s2['lat'])*111)**2 + ((s1['lon']-s2['lon'])*89)**2)**0.5
                    ratio = leg['distance'] / max(1.0, d_crow)
                    detour = ""
                    if ratio > 1.8 and leg['distance'] > 300:
                        detour = f" *** DETOUR / LOOP *** (ratio={ratio:.2f})"
                    print(f"  Stop {s1.get('stop_id', i+1):2d} -> {s2.get('stop_id', i+2):2d} ({s1['name'][:22]:22s} -> {s2['name'][:22]:22s}): {leg['distance']:5.0f}m [crow: {d_crow:4.0f}m]{detour}")
        except Exception as e:
            print(f"Error: {e}")

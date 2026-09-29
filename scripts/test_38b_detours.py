import json
import urllib.request
import math

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
bus_38b = [l for l in lines if l['short_name'] == '38B'][0]

print('--- ROUTING 38B ALLER ---')
coords_aller = [(s['lat'], s['lon']) for s in bus_38b['stops']]
coords_str = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in coords_aller])
url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=false"
req = urllib.request.Request(url, headers={'User-Agent': 'Test38B'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    legs = data['routes'][0]['legs']
    for i, leg in enumerate(legs):
        straight = get_distance(coords_aller[i], coords_aller[i+1])
        r = leg['distance'] / max(straight, 30)
        flag = " *** BIG DETOUR ***" if r > 1.4 or leg['distance'] > straight + 200 else ""
        print(f"Leg {i+1}->{i+2} ({bus_38b['stops'][i]['name'][:15]} -> {bus_38b['stops'][i+1]['name'][:15]}): straight={straight:.0f}m, routed={leg['distance']:.0f}m, ratio={r:.2f}{flag}")

print('\n--- ROUTING 38B RETOUR ---')
coords_ret = [(s['lat'], s['lon']) for s in bus_38b['stops_retour']]
coords_str_r = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in coords_ret])
url_r = f"https://router.project-osrm.org/route/v1/driving/{coords_str_r}?overview=false"
req_r = urllib.request.Request(url_r, headers={'User-Agent': 'Test38B'})
with urllib.request.urlopen(req_r) as resp:
    data = json.loads(resp.read())
    legs = data['routes'][0]['legs']
    for i, leg in enumerate(legs):
        straight = get_distance(coords_ret[i], coords_ret[i+1])
        r = leg['distance'] / max(straight, 30)
        flag = " *** BIG DETOUR ***" if r > 1.4 or leg['distance'] > straight + 200 else ""
        print(f"Leg {i+1}->{i+2} ({bus_38b['stops_retour'][i]['name'][:15]} -> {bus_38b['stops_retour'][i+1]['name'][:15]}): straight={straight:.0f}m, routed={leg['distance']:.0f}m, ratio={r:.2f}{flag}")

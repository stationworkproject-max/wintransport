import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_term = (36.829562, 10.159038) # Terminus Ministere
p_taoufik_raw_aller = (36.831696, 10.152933) # Clinique Taoufik in 36B Aller
p_taoufik_raw_retour = (36.832198, 10.154312) # Clinique Taoufik in 36B Retour
p_campus = (36.825350, 10.144100)

print("--- Testing 36B Aller: Terminus -> Taoufik -> Campus ---")
url1 = f"https://router.project-osrm.org/route/v1/driving/{p_term[1]},{p_term[0]};{p_taoufik_raw_aller[1]},{p_taoufik_raw_aller[0]};{p_campus[1]},{p_campus[0]}?overview=false"
with urllib.request.urlopen(urllib.request.Request(url1, headers={'User-Agent': 'Test'})) as resp:
    d = json.loads(resp.read())
    r = d['routes'][0]
    print(f"Aller total: {r['distance']:.0f}m | Leg 1: {r['legs'][0]['distance']:.0f}m, Leg 2: {r['legs'][1]['distance']:.0f}m")

print("\n--- Testing 36B Retour: Campus -> Taoufik -> Terminus ---")
# Test both raw_aller and raw_retour
for label, p_t in [("p_taoufik_raw_aller", p_taoufik_raw_aller), ("p_taoufik_raw_retour", p_taoufik_raw_retour)]:
    url2 = f"https://router.project-osrm.org/route/v1/driving/{p_campus[1]},{p_campus[0]};{p_t[1]},{p_t[0]};{p_term[1]},{p_term[0]}?overview=false"
    with urllib.request.urlopen(urllib.request.Request(url2, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"Retour with {label} ({p_t[0]}, {p_t[1]}): Total {r['distance']:.0f}m | Leg 1: {r['legs'][0]['distance']:.0f}m, Leg 2: {r['legs'][1]['distance']:.0f}m")

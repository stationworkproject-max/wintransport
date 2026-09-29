import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Test placing 36B Retour stations properly on Avenue Mohamed Bouazizi eastbound:
p6 = (36.823507, 10.141813) # 14 Janvier
# Campus Eastbound:
p7_options = [
    ("Current p7", 36.825112, 10.143985),
    ("Bouazizi Eastbound p7", 36.825250, 10.144000),
    ("Bouazizi Eastbound p7 v2", 36.825300, 10.144100),
]
# Clinique Taoufik Eastbound:
p8_options = [
    ("Current p8", 36.832198, 10.154312),
    ("Bouazizi Eastbound p8", 36.832309, 10.154203),
    ("Bouazizi Eastbound p8 v2", 36.832200, 10.154000),
]
p9 = (36.829562, 10.159038) # Terminus Ministere

for l7, lat7, lon7 in p7_options:
    for l8, lat8, lon8 in p8_options:
        coords = f"{p6[1]},{p6[0]};{lon7},{lat7};{lon8},{lat8};{p9[1]},{p9[0]}"
        url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&steps=true"
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
            data = json.loads(resp.read())
            r = data['routes'][0]
            legs = r['legs']
            d67 = legs[0]['distance']
            d78 = legs[1]['distance']
            d89 = legs[2]['distance']
            print(f"Option: {l7} + {l8} -> Total: {r['distance']:.0f}m | 6->7: {d67:.0f}m, 7->8: {d78:.0f}m, 8->9: {d89:.0f}m")

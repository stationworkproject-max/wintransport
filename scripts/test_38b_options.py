import urllib.request
import json

# Let's inspect the OSRM route geometry from Stop 10 to Stop 13 on 38B
c10 = (36.838561, 10.166151) # RX
c11 = (36.835735, 10.160893) # SONED
c12 = (36.832491, 10.154094) # CLINIQUE TAOUFIK
c13 = (36.83072, 10.15038)   # FACULTE DE DROIT

# Let's see what happens if we route:
# 1) Direct c10 -> c13
# 2) c10 -> c11 -> c13
# 3) c10 -> c12 -> c13
# 4) c10 -> c11 -> c12 -> c13

for label, pts in [
    ("c10 -> c13 (direct)", [c10, c13]),
    ("c10 -> c11 -> c13", [c10, c11, c13]),
    ("c10 -> c12 -> c13", [c10, c12, c13]),
    ("c10 -> c11 -> c12 -> c13", [c10, c11, c12, c13])
]:
    coords_str = ';'.join([f"{p[1]:.5f},{p[0]:.5f}" for p in pts])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=false"
    req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read())['routes'][0]['distance']
        print(f"{label}: distance = {d:.0f}m")

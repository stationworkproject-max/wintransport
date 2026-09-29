import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Aller stations:
# 11: SONED
# 12: CLINIQUE TAOUFIK
# 13: FACULTE DE DROIT
aller_11 = (36.835932, 10.160730) # SONED
aller_12 = (36.832431, 10.154153) # CLINIQUE TAOUFIK
aller_13 = (36.830720, 10.150380) # FACULTE DE DROIT

# Retour stations:
# 6: FACULTE DE DROIT
# 7: CLINIQUE TAOUFIK
# 8: SONED
# 9: RX
retour_6 = (36.830720, 10.150160) # FACULTE DE DROIT
retour_7 = (36.832311, 10.154201) # CLINIQUE TAOUFIK
retour_8 = (36.835544, 10.160251) # SONED
retour_9 = (36.835486, 10.166438) # RX

print("=== ALLER: 11 (SONED) -> 12 (TAOUFIK) -> 13 (DROIT) ===")
url = f"https://router.project-osrm.org/route/v1/driving/{aller_11[1]},{aller_11[0]};{aller_12[1]},{aller_12[0]};{aller_13[1]},{aller_13[0]}?overview=full&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    d = json.loads(resp.read())
    print(f"Total distance: {d['routes'][0]['distance']:.0f}m")
    for i, leg in enumerate(d['routes'][0]['legs']):
        print(f"  Leg {i+11}->{i+12}: {leg['distance']:.0f}m")
        for st in leg['steps']:
            name = st.get('name', 'unnamed')
            print(f"    {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):10s} on '{name}' ({st['distance']:.0f}m)")

print("\n=== RETOUR: 6 (DROIT) -> 7 (TAOUFIK) -> 8 (SONED) -> 9 (RX) ===")
url = f"https://router.project-osrm.org/route/v1/driving/{retour_6[1]},{retour_6[0]};{retour_7[1]},{retour_7[0]};{retour_8[1]},{retour_8[0]};{retour_9[1]},{retour_9[0]}?overview=full&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    d = json.loads(resp.read())
    print(f"Total distance: {d['routes'][0]['distance']:.0f}m")
    for i, leg in enumerate(d['routes'][0]['legs']):
        print(f"  Leg {i+6}->{i+7}: {leg['distance']:.0f}m")
        for st in leg['steps']:
            name = st.get('name', 'unnamed')
            print(f"    {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):10s} on '{name}' ({st['distance']:.0f}m)")

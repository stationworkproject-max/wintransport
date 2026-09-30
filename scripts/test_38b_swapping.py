import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Test 38B stops between Fac de Droit, Taoufik, Soned, RX, Mutuelleville

fac_droit = (36.83072, 10.15038)
taoufik_nb = (36.832198, 10.154312) # Northbound / towards Mutuelle
taoufik_sb = (36.831696, 10.152933) # Southbound / towards Fac de Droit
soned = (36.836053, 10.160626)
rx_aller = (36.838, 10.1653)
rx_retour = (36.835486, 10.166438)
mutuelle = (36.833778, 10.167208)

def test_route(name, pts):
    coords_str = ";".join([f"{p[1]:.6f},{p[0]:.6f}" for p in pts])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=false"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get('code') == 'Ok':
                print(f"  {name}: {data['routes'][0]['distance']}m")
            else:
                print(f"  {name}: {data.get('code')}")
    except Exception as e:
        print(f"  {name}: {e}")

print("--- 38B ALLER (Mutuelleville -> RX -> SONED -> Taoufik -> Fac de Droit) ---")
test_route("With taoufik_nb (current)", [mutuelle, rx_aller, soned, taoufik_nb, fac_droit])
test_route("With taoufik_sb (swapped)", [mutuelle, rx_aller, soned, taoufik_sb, fac_droit])

print("\n--- 38B RETOUR (Fac de Droit -> Taoufik -> SONED -> RX -> Mutuelleville) ---")
test_route("With taoufik_sb (current)", [fac_droit, taoufik_sb, soned, rx_retour, mutuelle])
test_route("With taoufik_nb (swapped)", [fac_droit, taoufik_nb, soned, rx_retour, mutuelle])

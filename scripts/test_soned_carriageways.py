import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p_taoufik_nb = (36.832198, 10.154312)
p_taoufik_sb = (36.831696, 10.152933)
rx_aller = (36.838, 10.1653)
rx_retour = (36.835486, 10.166438)

soned_nb = (36.836019, 10.161154)
soned_sb = (36.835594, 10.160092)

def test_leg(p1, p2, name):
    url = f"https://router.project-osrm.org/route/v1/driving/{p1[1]:.6f},{p1[0]:.6f};{p2[1]:.6f},{p2[0]:.6f}?overview=false"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read())['routes'][0]['distance']
        print(f"  {name}: {d}m")

print("--- RETOUR: Taoufik NB -> SONED NB -> RX Retour ---")
test_leg(p_taoufik_nb, soned_nb, "Taoufik NB -> Soned NB")
test_leg(soned_nb, rx_retour, "Soned NB -> RX Retour")

print("\n--- ALLER: RX Aller -> SONED SB -> Taoufik SB ---")
test_leg(rx_aller, soned_sb, "RX Aller -> Soned SB")
test_leg(soned_sb, p_taoufik_sb, "Soned SB -> Taoufik SB")

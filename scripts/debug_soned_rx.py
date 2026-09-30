import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

fac_droit = (36.83072, 10.15038)
taoufik_nb = (36.832198, 10.154312)
soned = (36.836053, 10.160626)
rx_aller = (36.838, 10.1653)
rx_retour = (36.835486, 10.166438)
mutuelle = (36.833778, 10.167208)

def osrm_steps(p1, p2, label):
    url = f"https://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?steps=true&overview=false"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    leg = data['routes'][0]['legs'][0]
    print(f"\n{label} -> total: {leg['distance']}m")
    for s in leg['steps']:
        print(f"  {s.get('name', 'unnamed')} ({s['maneuver']['type']}) -> {s['distance']}m")

osrm_steps(fac_droit, taoufik_nb, "Fac de Droit -> Taoufik Northbound")
osrm_steps(taoufik_nb, soned, "Taoufik Northbound -> SONED")
osrm_steps(soned, rx_retour, "SONED -> RX Retour")
osrm_steps(soned, rx_aller, "SONED -> RX Aller")
osrm_steps(rx_retour, mutuelle, "RX Retour -> Mutuelleville")
osrm_steps(rx_aller, mutuelle, "RX Aller -> Mutuelleville")

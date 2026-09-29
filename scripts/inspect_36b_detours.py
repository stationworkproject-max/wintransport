import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Detour 1: Terminus Affaires Etrangeres (36.829562, 10.159038) -> Clinique Taoufik (36.831657, 10.152977)
# Let's inspect where Clinique Taoufik on 36B Aller should be!
print("=== Detour 1: Terminus -> Clinique Taoufik on 36B ===")
p_term = (36.829562, 10.159038)
p_taoufik_aller = (36.832431, 10.154153) # Westbound Bouazizi (towards Campus)
p_taoufik_cur = (36.831657, 10.152977)   # Current in 36B Aller

for p, label in [(p_taoufik_cur, "Current 36B Aller stop 2"), (p_taoufik_aller, "Westbound Bouazizi Taoufik")]:
    url = f"https://router.project-osrm.org/route/v1/driving/{p_term[1]},{p_term[0]};{p[1]},{p[0]}?overview=full&steps=true"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
        d = json.loads(resp.read())
        r = d['routes'][0]
        print(f"\n{label} -> distance: {r['distance']:.0f}m")
        for st in r['legs'][0]['steps']:
            print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):10s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

# Detour 2: 14 Janvier 2011 -> Foyer Bardo 2
print("\n=== Detour 2: 14 Janvier 2011 -> Foyer Bardo 2 ===")
p_14j_aller = (36.823508, 10.141495)
p_14j_retour = (36.823507, 10.141813)
p_bardo2_aller = (36.818349, 10.141493)
p_bardo2_retour = (36.818640, 10.141400)

for p1, l1 in [(p_14j_aller, "14 Janvier cur"), (p_14j_retour, "14 Janvier other side")]:
    for p2, l2 in [(p_bardo2_aller, "Foyer Bardo 2 cur"), (p_bardo2_retour, "Foyer Bardo 2 other side")]:
        url = f"https://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&steps=true"
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
            d = json.loads(resp.read())
            r = d['routes'][0]
            print(f"{l1} -> {l2}: {r['distance']:.0f}m")

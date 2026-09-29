import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Let's inspect all ways connecting Mutuelleville to Avenue Mohamed Bouazizi
# 1. Via Rue Khaled Ibn Walid / Rue Azzouz Rebai
# 2. Via Avenue Jugurtha -> interchange
# 3. Via Rue Chedly Zouiten -> Avenue de la Ligue des Etats Arabes

points = [
    # Station 8 Chedly Zouiten: (36.829621, 10.170550)
    # Station 9 Mutuelleville: (36.833778, 10.167208)
    # SONED: (36.835931, 10.160730)
]

# Let's see: from Station 9 Mutuelleville (36.833778, 10.167208), what happens if we route to different points near the interchange?
# Let's check where the U-turn occurred in:
# depart on Avenue Jugurtha (592m)
# straight on Rue Mohieddine Klibi (284m)
# U-TURN on Rue Mohieddine Klibi (191m)
# turn slight right (122m)
# turn right (33m)
# roundabout (19m + 41m)
# merge on Avenue Mohamed Bouazizi (348m)

# Why did it do U-TURN on Mohieddine Klibi?
# Because the exit to the interchange ramp was on the SOUTHBOUND side of Mohieddine Klibi!
# Is Mohieddine Klibi a divided dual-carriageway with two one-way lanes?
# YES! Mohieddine Klibi has a Northbound lane and a Southbound lane!
# The ramp to Avenue Mohamed Bouazizi connects to the SOUTHBOUND lane of Mohieddine Klibi!
# When coming from Avenue Jugurtha, you enter the NORTHBOUND lane of Mohieddine Klibi.
# So you have to drive up to the crossover/roundabout to get to the Southbound lane to take the ramp!
print("Checking Mohieddine Klibi interchange geometry...")
url = "https://router.project-osrm.org/route/v1/driving/10.167208,36.833778;10.160730,36.835931?overview=full&geometries=geojson&steps=true"
with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Test'})) as resp:
    d = json.loads(resp.read())
    leg = d['routes'][0]['legs'][0]
    for st in leg['steps']:
        print(f"  {st['maneuver']['type']:10s} {st['maneuver'].get('modifier', ''):10s} on '{st.get('name', '')}' ({st['distance']:.0f}m)")

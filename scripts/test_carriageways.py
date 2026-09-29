import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Test points along Avenue Mohamed Bouazizi:
# From East (RX interchange) to West (Faculte de Droit):
p_rx_west = (36.838104, 10.165197)
p_soned_west = (36.835931, 10.160730)
p_taoufik_west = (36.832431, 10.154153)
p_droit_west = (36.830720, 10.150380)

# Westbound sequence (Aller)
coords_west = f"{p_rx_west[1]},{p_rx_west[0]};{p_soned_west[1]},{p_soned_west[0]};{p_taoufik_west[1]},{p_taoufik_west[0]};{p_droit_west[1]},{p_droit_west[0]}"
url = f"https://router.project-osrm.org/route/v1/driving/{coords_west}?overview=false"
req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    print("=== WESTBOUND ROUTE (RX -> SONED -> Taoufik -> Droit) ===")
    route = data['routes'][0]
    print(f"Total distance: {route['distance']:.0f}m")
    for i, leg in enumerate(route['legs']):
        print(f"  Leg {i+1}: {leg['distance']:.0f}m")

# Now Eastbound sequence (Retour: Droit -> Taoufik -> SONED -> RX):
# Let's test the other carriageway!
# Opposite carriageway coordinates:
p_taoufik_east = (36.832309, 10.154203)
p_soned_east = (36.835836, 10.160810)
p_rx_east = (36.838149, 10.165289)

coords_east = f"{p_droit_west[1]},{p_droit_west[0]};{p_taoufik_east[1]},{p_taoufik_east[0]};{p_soned_east[1]},{p_soned_east[0]};{p_rx_east[1]},{p_rx_east[0]}"
url = f"https://router.project-osrm.org/route/v1/driving/{coords_east}?overview=false"
req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    print("\n=== EASTBOUND ROUTE (Droit -> Taoufik -> SONED -> RX) ===")
    route = data['routes'][0]
    print(f"Total distance: {route['distance']:.0f}m")
    for i, leg in enumerate(route['legs']):
        print(f"  Leg {i+1}: {leg['distance']:.0f}m")

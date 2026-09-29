import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def query_nearest(lat, lon, label):
    print(f"\n==================== {label} ({lat:.6f}, {lon:.6f}) ====================")
    url = f"https://router.project-osrm.org/nearest/v1/driving/{lon},{lat}?number=6"
    req = urllib.request.Request(url, headers={'User-Agent': 'TestTransit/1.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        for i, wp in enumerate(data.get('waypoints', [])):
            w_lon, w_lat = wp['location']
            w_dist = wp['distance']
            w_name = wp.get('name', 'unnamed')
            print(f"  #{i+1}: ({w_lat:.6f}, {w_lon:.6f}) - dist={w_dist:.1f}m - name='{w_name}'")

# Check SONED, Clinique Taoufik, RX, Faculte de Droit
query_nearest(36.835932, 10.160730, "SONED (Aller)")
query_nearest(36.835544, 10.160251, "SONED (Retour)")
query_nearest(36.832431, 10.154153, "CLINIQUE TAOUFIK (Aller)")
query_nearest(36.832198, 10.154312, "CLINIQUE TAOUFIK (Retour)")
query_nearest(36.838100, 10.165200, "RX (Aller)")
query_nearest(36.835486, 10.166438, "RX (Retour)")

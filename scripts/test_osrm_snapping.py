import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def check_nearest(name, lat, lon):
    url = f"https://router.project-osrm.org/nearest/v1/driving/{lon},{lat}?number=3"
    req = urllib.request.Request(url, headers={'User-Agent': 'WhereAmI/1.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print(f"\n--- {name} ({lat}, {lon}) ---")
            for wp in data.get('waypoints', []):
                print(f"  Road: '{wp.get('name')}', Dist: {wp.get('distance'):.1f}m, Snapped: {wp.get('location')}")
    except Exception as e:
        print(f"Error for {name}: {e}")

check_nearest("Campus Aller (buses.geojson)", 36.8251118, 10.1439852)
check_nearest("Campus Retour (buses.geojson)", 36.8253694, 10.1438886)
check_nearest("14 Janvier Aller (buses.geojson)", 36.823507, 10.1418129)
check_nearest("14 Janvier Retour (buses.geojson)", 36.823507, 10.1414964)
check_nearest("Clinique Taoufik Aller (buses.geojson)", 36.8321978, 10.154312)
check_nearest("Clinique Taoufik Retour (buses.geojson)", 36.8316956, 10.1529334)
check_nearest("SONED", 36.8360529, 10.1606257)

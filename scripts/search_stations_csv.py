import csv
import sys

# Set stdout encoding
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\AymenFrd\Desktop\MapTrans\Train\stations.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows in stations.csv: {len(rows)}")
for r in rows:
    name = r.get('name', '')
    name_fr = r.get('name_fr', '')
    if any(k in name.lower() or k in name_fr.lower() for k in ['tunis', 'barcelone', 'sousse', 'sfax', 'gabes', 'redeyef', 'metlaoui']):
        print(f"  lat={r['lat']}, lon={r['lon']} | name='{name}' | name_fr='{name_fr}'")

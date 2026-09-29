import os
import glob
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = r'C:\Users\AymenFrd\Desktop\MapTrans\arcgis_export'
files = os.listdir(p)
print(f"Total files in arcgis_export: {len(files)}")
matches = [f for f in files if '36' in f or '38' in f or '846' in f or '847' in f]
print("Matching files:")
for m in matches:
    print(" ", m)

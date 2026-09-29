import urllib.request
import json
import math
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# STEP 1: Define corrected stops for bus_846 (36B) and bus_847 (38B)
# ============================================================

stops_846_aller = [
    {"id": "st-1", "stop_id": 1, "name": "TERMINUS MINISTÉRE DES AFFAIRES ETRANGERES ( L 36 B )", "lat": 36.830000, "lon": 10.157500, "horaires_count": 30},
    {"id": "st-2", "stop_id": 2, "name": "CLINIQUE TAOUFIK RETOUR", "lat": 36.831696, "lon": 10.152933, "horaires_count": 30},
    {"id": "st-3", "stop_id": 3, "name": "CAMPUS RETOUR", "lat": 36.825369, "lon": 10.143889, "horaires_count": 30},
    {"id": "st-4", "stop_id": 4, "name": "14 JANVIER 2011 RETOUR", "lat": 36.823508, "lon": 10.141495, "horaires_count": 30},
    {"id": "st-5", "stop_id": 5, "name": "FOYER BARDO 2 RETOUR", "lat": 36.818349, "lon": 10.141493, "horaires_count": 30},
    {"id": "st-6", "stop_id": 6, "name": "FOYER BARDO 1 RETOUR", "lat": 36.813941, "lon": 10.146199, "horaires_count": 30},
    {"id": "st-7", "stop_id": 7, "name": "CAFÉ EL HAJ RETOUR", "lat": 36.812810, "lon": 10.144989, "horaires_count": 30},
    {"id": "st-8", "stop_id": 8, "name": "TOUTA BARDO", "lat": 36.808844, "lon": 10.137977, "horaires_count": 30},
]

stops_846_retour = [
    {"id": "st-1-r", "stop_id": 1, "name": "TOUTA BARDO", "lat": 36.808844, "lon": 10.137977, "horaires_count": 30},
    {"id": "st-2-r", "stop_id": 2, "name": "CAFÉ EL HAJ ALLER", "lat": 36.812835, "lon": 10.145171, "horaires_count": 30},
    {"id": "st-3-r", "stop_id": 3, "name": "FOYER BARDO 1 ALLER", "lat": 36.814154, "lon": 10.146217, "horaires_count": 30},
    {"id": "st-4-r", "stop_id": 4, "name": "FOYER BARDO 2 ALLER", "lat": 36.81864, "lon": 10.1414, "horaires_count": 30},
    {"id": "st-5-r", "stop_id": 5, "name": "CENTER DE FORMATION RAS TABIA ALLER", "lat": 36.820024, "lon": 10.139791, "horaires_count": 30},
    {"id": "st-6-r", "stop_id": 6, "name": "14 JANVIER 2011 ALLER", "lat": 36.823507, "lon": 10.141813, "horaires_count": 30},
    {"id": "st-7-r", "stop_id": 7, "name": "CAMPUS ALLER", "lat": 36.825350, "lon": 10.144100, "horaires_count": 30},
    {"id": "st-8-r", "stop_id": 8, "name": "CLINIQUE TAOUFIK ALLER", "lat": 36.832198, "lon": 10.154312, "horaires_count": 30},
    {"id": "st-9-r", "stop_id": 9, "name": "TERMINUS MINISTÉRE DES AFFAIRES ETRANGERES ( L 36 B )", "lat": 36.829562, "lon": 10.159038, "horaires_count": 30},
]

stops_847_aller = [
    {"id": "st-1", "stop_id": 1, "name": "TERMINUS TUNIS MARINE BUS", "lat": 36.800384, "lon": 10.190388, "horaires_count": 30},
    {"id": "st-2", "stop_id": 2, "name": "JEANS JAURES", "lat": 36.801618, "lon": 10.183899, "horaires_count": 30},
    {"id": "st-3", "stop_id": 3, "name": "STEG JEANS JAURES ALLER", "lat": 36.8055, "lon": 10.181998, "horaires_count": 30},
    {"id": "st-4", "stop_id": 4, "name": "PASSAGE JEANS JAURES ALLER", "lat": 36.806911, "lon": 10.181536, "horaires_count": 30},
    {"id": "st-5", "stop_id": 5, "name": "LA FAYETTE ALLER", "lat": 36.810562, "lon": 10.180724, "horaires_count": 30},
    {"id": "st-6", "stop_id": 6, "name": "PLACE JEANS DARK ALLER", "lat": 36.818357, "lon": 10.179579, "horaires_count": 30},
    {"id": "st-7", "stop_id": 7, "name": "PLACE PASTEUR ALLER", "lat": 36.823094, "lon": 10.177674, "horaires_count": 30},
    {"id": "st-8", "stop_id": 8, "name": "CHEDLY ZOUITEN", "lat": 36.829621, "lon": 10.17055, "horaires_count": 30},
    {"id": "st-9", "stop_id": 9, "name": "MUNICIPALITÉ MUTUELLE VILLE", "lat": 36.833778, "lon": 10.167208, "horaires_count": 30},
    {"id": "st-10", "stop_id": 10, "name": "RX", "lat": 36.838000, "lon": 10.165300, "horaires_count": 30},
    {"id": "st-11", "stop_id": 11, "name": "SONED", "lat": 36.835931, "lon": 10.16073, "horaires_count": 30},
    {"id": "st-12", "stop_id": 12, "name": "CLINIQUE TAOUFIK ALLER", "lat": 36.832431, "lon": 10.154153, "horaires_count": 30},
    {"id": "st-13", "stop_id": 13, "name": "FACULTÉ DE DROIT", "lat": 36.83072, "lon": 10.15038, "horaires_count": 30},
    {"id": "st-14", "stop_id": 14, "name": "FACULTÉ DES SCIENCES DE TUNIS", "lat": 36.832833, "lon": 10.148073, "horaires_count": 30},
    {"id": "st-15", "stop_id": 15, "name": "CARREFOUR", "lat": 36.836543, "lon": 10.144694, "horaires_count": 30},
    {"id": "st-16", "stop_id": 16, "name": "MAISON DES MAMANS", "lat": 36.835397, "lon": 10.138117, "horaires_count": 30},
    {"id": "st-17", "stop_id": 17, "name": "FOYER OMRANE SUPÉRIEUR", "lat": 36.83619, "lon": 10.132044, "horaires_count": 30},
    {"id": "st-18", "stop_id": 18, "name": "TERMINUS OMRANE SUPÉRIEUR L 78 + 38 B", "lat": 36.836859, "lon": 10.129029, "horaires_count": 30},
]

stops_847_retour = [
    {"id": "st-1-r", "stop_id": 1, "name": "TERMINUS OMRANE SUPÉRIEUR L 78 + 38 B", "lat": 36.836859, "lon": 10.129029, "horaires_count": 30},
    {"id": "st-2-r", "stop_id": 2, "name": "FOYER OMRANE SUPÉRIEUR", "lat": 36.83619, "lon": 10.132044, "horaires_count": 30},
    {"id": "st-3-r", "stop_id": 3, "name": "MAISON DES MAMANS", "lat": 36.835397, "lon": 10.138117, "horaires_count": 30},
    {"id": "st-4-r", "stop_id": 4, "name": "CARREFOUR", "lat": 36.836543, "lon": 10.144694, "horaires_count": 30},
    {"id": "st-5-r", "stop_id": 5, "name": "FACULTÉ DES SCIENCES DE TUNIS", "lat": 36.832833, "lon": 10.148073, "horaires_count": 30},
    {"id": "st-6-r", "stop_id": 6, "name": "FACULTÉ DE DROIT", "lat": 36.83072, "lon": 10.15016, "horaires_count": 30},
    {"id": "st-7-r", "stop_id": 7, "name": "CLINIQUE TAOUFIK ALLER", "lat": 36.832309, "lon": 10.154203, "horaires_count": 30},
    {"id": "st-8-r", "stop_id": 8, "name": "SONED", "lat": 36.835836, "lon": 10.16081, "horaires_count": 30},
    {"id": "st-9-r", "stop_id": 9, "name": "RX", "lat": 36.835486, "lon": 10.166438, "horaires_count": 30},
    {"id": "st-10-r", "stop_id": 10, "name": "MUNICIPALITÉ MUTUELLE VILLE", "lat": 36.83377, "lon": 10.16718, "horaires_count": 30},
    {"id": "st-11-r", "stop_id": 11, "name": "CHEDLY ZOUITEN", "lat": 36.829621, "lon": 10.17055, "horaires_count": 30},
    {"id": "st-12-r", "stop_id": 12, "name": "PLACE PASTEUR ALLER", "lat": 36.823108, "lon": 10.177685, "horaires_count": 30},
    {"id": "st-13-r", "stop_id": 13, "name": "PLACE JEANS DARK ALLER", "lat": 36.81992, "lon": 10.18158, "horaires_count": 30},
    {"id": "st-14-r", "stop_id": 14, "name": "LA FAYETTE ALLER", "lat": 36.810986, "lon": 10.184607, "horaires_count": 30},
    {"id": "st-15-r", "stop_id": 15, "name": "PASSAGE JEANS JAURES ALLER", "lat": 36.80731, "lon": 10.185221, "horaires_count": 30},
    {"id": "st-16-r", "stop_id": 16, "name": "STEG JEANS JAURES ALLER", "lat": 36.805868, "lon": 10.185461, "horaires_count": 30},
    {"id": "st-17-r", "stop_id": 17, "name": "JEANS JAURES", "lat": 36.803375, "lon": 10.185868, "horaires_count": 30},
    {"id": "st-18-r", "stop_id": 18, "name": "TERMINUS TUNIS MARINE BUS", "lat": 36.800384, "lon": 10.190388, "horaires_count": 30},
]

# ============================================================
# STEP 2: Generate OSRM shapes
# ============================================================

route_configs = {
    "bus_846_0": stops_846_aller,
    "bus_846_1": stops_846_retour,
    "bus_847_0": stops_847_aller,
    "bus_847_1": stops_847_retour,
}

shapes = {}
for rkey, stops in route_configs.items():
    coords = ";".join([f"{s['lon']},{s['lat']}" for s in stops])
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'TransitBuilder'})) as resp:
        data = json.loads(resp.read())
        r = data['routes'][0]
        pts = [[round(p[1], 5), round(p[0], 5)] for p in r['geometry']['coordinates']]
        shapes[rkey] = pts
        print(f"Generated {rkey}: {len(pts)} pts, {r['distance']:.0f}m")

shapes["bus_846"] = shapes["bus_846_0"]
shapes["bus_847"] = shapes["bus_847_0"]

# ============================================================
# STEP 3: Read staticTransit.js and replace stops_aller/stops_retour
# ============================================================

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_stops_section(content, line_id, section_name, new_stops):
    """Replace stops_aller or stops_retour section in the JS file."""
    pos = content.find(f'"id": "{line_id}"')
    if pos == -1:
        print(f"ERROR: Could not find {line_id}")
        return content
    
    # Find the section
    search_start = pos
    section_key = f'"{section_name}": ['
    section_pos = content.find(section_key, search_start)
    if section_pos == -1:
        print(f"ERROR: Could not find {section_name} for {line_id}")
        return content
    
    # Find the matching closing bracket
    bracket_start = section_pos + len(section_key)
    depth = 1
    i = bracket_start
    while i < len(content) and depth > 0:
        if content[i] == '[':
            depth += 1
        elif content[i] == ']':
            depth -= 1
        i += 1
    bracket_end = i  # position after the ]
    
    # Build replacement JSON
    stops_json_lines = []
    for s in new_stops:
        stops_json_lines.append('      ' + json.dumps(s))
    replacement = section_key + '\n' + ',\n'.join(stops_json_lines) + '\n    ]'
    
    content = content[:section_pos] + replacement + content[bracket_end:]
    print(f"Replaced {section_name} for {line_id} ({len(new_stops)} stops)")
    return content

content = replace_stops_section(content, "bus_846", "stops_aller", stops_846_aller)
content = replace_stops_section(content, "bus_846", "stops_retour", stops_846_retour)
content = replace_stops_section(content, "bus_847", "stops_aller", stops_847_aller)
content = replace_stops_section(content, "bus_847", "stops_retour", stops_847_retour)

with open('src/data/staticTransit.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("staticTransit.js updated successfully!")

# ============================================================
# STEP 4: Update transitShapes.json
# ============================================================

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    all_shapes = json.load(f)

for key in shapes:
    old_count = len(all_shapes.get(key, []))
    all_shapes[key] = shapes[key]
    print(f"Shape {key}: {old_count} -> {len(shapes[key])} pts")

with open('src/data/transitShapes.json', 'w', encoding='utf-8') as f:
    json.dump(all_shapes, f)
print("transitShapes.json updated successfully!")

# ============================================================
# STEP 5: Verify total shape count is unchanged
# ============================================================
print(f"\nTotal shapes in transitShapes.json: {len(all_shapes)}")

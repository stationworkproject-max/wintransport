import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(text[text.find('export const STATIC_LINES = ') + len('export const STATIC_LINES = '):].strip()[:-1])

with open('src/data/transitShapes.json', 'r') as f:
    shapes = json.load(f)

bus_36b = [l for l in lines if l['id'] == 'bus_846'][0]
bus_38b = [l for l in lines if l['id'] == 'bus_847'][0]

html = """<!DOCTYPE html>
<html>
<head>
  <title>Inspect 36B and 38B</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body { margin:0; padding:0; font-family:sans-serif; }
    #map { width:100vw; height:100vh; }
    .control-box {
      position: absolute; top: 10px; right: 10px; z-index: 1000;
      background: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.3);
      max-width: 300px; font-size: 13px;
    }
  </style>
</head>
<body>
<div id="map"></div>
<div class="control-box">
  <b>Inspect Lines 36B and 38B</b>
  <p>Toggle layers using the top-right layer control to see existing shapes and stations.</p>
</div>
<script>
  var map = L.map('map').setView([36.825, 10.155], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

  var overlayMaps = {};
"""

colors = {
    'bus_846_0': '#2563eb', # Blue
    'bus_846_1': '#06b6d4', # Cyan
    'bus_847_0': '#dc2626', # Red
    'bus_847_1': '#f97316', # Orange
}

for bid, bname, l in [('bus_846', '36B', bus_36b), ('bus_847', '38B', bus_38b)]:
    for dir_idx, dir_name in [(0, 'Aller'), (1, 'Retour')]:
        key = f"{bid}_{dir_idx}"
        pts = shapes.get(key, [])
        stops = l.get('stops_aller' if dir_idx == 0 else 'stops_retour', l['stops'])
        
        html += f"""
  // Layer group for {bname} {dir_name}
  var lg_{key} = L.layerGroup();
  
  var line_{key} = L.polyline({json.dumps(pts)}, {{
    color: '{colors[key]}',
    weight: 5,
    opacity: 0.8
  }}).addTo(lg_{key});
  
  var stops_{key} = {json.dumps(stops)};
  stops_{key}.forEach(function(s, idx) {{
    var m = L.circleMarker([s.lat, s.lon], {{
      radius: 6,
      color: '#fff',
      fillColor: '{colors[key]}',
      fillOpacity: 1,
      weight: 2
    }}).bindPopup('<b>' + (idx+1) + '. ' + s.name + '</b><br>{bname} {dir_name}');
    m.addTo(lg_{key});
  }});
  
  overlayMaps['{bname} {dir_name} ({len(pts)} pts)'] = lg_{key};
  lg_{key}.addTo(map);
"""

html += """
  L.control.layers(null, overlayMaps, { collapsed: false }).addTo(map);
</script>
</body>
</html>
"""

with open('visualize_36b_38b.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Saved visualize_36b_38b.html")

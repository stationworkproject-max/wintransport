import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()
lines = json.loads(re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', text, re.DOTALL).group(1))

with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

test_line_ids = ['bus_846', 'bus_847', 'bus_848', 'bus_772', 'bus_703']
test_lines = [l for l in lines if l['id'] in test_line_ids]

html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>WinTransport - Corrected Bus Lines & Bilingual Stations</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; }}
    #map {{ width: 100vw; height: 100vh; }}
    .panel {{
      position: absolute; top: 14px; left: 14px; z-index: 1000;
      background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px);
      padding: 16px 20px; border-radius: 16px; border: 1px solid rgba(51, 65, 85, 0.8);
      box-shadow: 0 10px 30px rgba(0,0,0,0.5); max-width: 360px;
    }}
    .panel h2 {{ margin: 0 0 6px 0; font-size: 16px; color: #60a5fa; display: flex; align-items: center; justify-content: space-between; }}
    .panel p {{ margin: 0 0 12px 0; font-size: 12px; color: #94a3b8; line-height: 1.4; }}
    .lang-btn {{
      background: #2563eb; color: white; border: none; padding: 4px 10px; border-radius: 8px;
      font-weight: bold; font-size: 11px; cursor: pointer;
    }}
    .line-card {{
      background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(51, 65, 85, 0.6);
      padding: 10px 12px; border-radius: 10px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s;
    }}
    .line-card:hover {{ background: rgba(51, 65, 85, 0.9); border-color: #3b82f6; }}
    .badge {{
      display: inline-block; padding: 2px 8px; border-radius: 6px; font-weight: 800; font-size: 11px; color: white; margin-right: 6px;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="panel">
    <h2>
      <span>🚌 Bus Bilingual Inspector</span>
      <button class="lang-btn" id="toggleLang">عربي / FR</button>
    </h2>
    <p id="desc">Visualisation des lignes de bus corrigées (36B, 38B, 104, 10) avec arrêts routiers Aller/Retour et noms bilingues Français/Arabe.</p>
    <div id="linesList"></div>
  </div>

  <script>
    var currentLang = 'fr';
    var linesData = {json.dumps(test_lines, ensure_ascii=False)};
    var shapesData = {json.dumps({k: shapes[k] for k in shapes if any(k.startswith(tid) for tid in test_line_ids)}, ensure_ascii=False)};

    var map = L.map('map', {{ zoomControl: false }}).setView([36.815, 10.155], 13);
    L.control.zoom({{ position: 'bottomright' }}).addTo(map);

    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }}).addTo(map);

    var layerGroup = L.layerGroup().addTo(map);

    function renderLine(line, dirIdx) {{
      layerGroup.clearLayers();
      var isAr = currentLang === 'ar';
      var dirKey = line.id + '_' + dirIdx;
      var pts = shapesData[dirKey] || shapesData[line.id] || [];

      // Draw polyline
      if (pts.length > 1) {{
        var casing = L.polyline(pts, {{ color: '#ffffff', weight: 8, opacity: 0.7 }}).addTo(layerGroup);
        var poly = L.polyline(pts, {{ color: line.color, weight: 5, opacity: 1 }}).addTo(layerGroup);
        map.fitBounds(poly.getBounds(), {{ padding: [60, 60] }});
      }}

      // Directional stops
      var stops = dirIdx === 1 ? (line.stops_retour || line.stops) : (line.stops_aller || line.stops);
      var dirName = isAr ? (line.directions_ar ? line.directions_ar[dirIdx] : '') : (line.directions_fr ? line.directions_fr[dirIdx] : '');

      stops.forEach(function(s, idx) {{
        var isFirst = idx === 0;
        var isLast = idx === stops.length - 1;
        var stopName = isAr ? (s.name_ar || s.name) : (s.name_fr || s.name);
        var markerHtml = '<div style="width:24px;height:24px;background:' + line.color + ';border:2px solid white;border-radius:50%;color:white;font-weight:900;font-size:10px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.4);">' + (idx+1) + '</div>';

        var icon = L.divIcon({{ html: markerHtml, className: '', iconSize: [24, 24], iconAnchor: [12, 12] }});
        var marker = L.marker([s.lat, s.lon], {{ icon: icon }}).addTo(layerGroup);

        var tooltipHtml = '<div dir="' + (isAr ? 'rtl' : 'ltr') + '">' +
          '<b>' + (isAr ? 'المحطة ' : 'Arrêt ') + (idx+1) + ' : ' + stopName + '</b><br/>' +
          '<span style="font-size:11px;color:#cbd5e1;">' + (isFirst ? (isAr ? '🏁 انطلاق' : '🏁 Départ') : isLast ? (isAr ? '🛑 نهاية الخط' : '🛑 Terminus') : '') + ' • ' + dirName + '</span>' +
          '</div>';

        marker.bindTooltip(tooltipHtml, {{ direction: 'top', offset: [0, -8] }});
      }});
    }}

    function updateUI() {{
      var list = document.getElementById('linesList');
      list.innerHTML = '';
      var isAr = currentLang === 'ar';

      document.getElementById('desc').innerText = isAr
        ? 'عرض خطوط الحافلات المصححة (36B, 38B, 104, 10) مع محطات الطريق المزدوج ذهاب/إياب والأسماء بالعربية والفرنسية.'
        : 'Visualisation des lignes de bus corrigées (36B, 38B, 104, 10) avec arrêts routiers Aller/Retour et noms bilingues Français/Arabe.';

      linesData.forEach(function(l) {{
        var shortName = isAr ? (l.short_name_ar || l.short_name) : l.short_name;
        var longName = isAr ? (l.long_name_ar || l.long_name) : (l.long_name_fr || l.long_name);
        var dirAller = isAr ? (l.directions_ar ? l.directions_ar[0] : 'ذهاب') : (l.directions_fr ? l.directions_fr[0] : 'Aller');
        var dirRetour = isAr ? (l.directions_ar ? l.directions_ar[1] : 'إياب') : (l.directions_fr ? l.directions_fr[1] : 'Retour');

        var card = document.createElement('div');
        card.className = 'line-card';
        card.innerHTML = 
          '<div>' +
            '<span class="badge" style="background:' + l.color + '">' + shortName + '</span>' +
            '<b>' + longName + '</b>' +
          '</div>' +
          '<div style="margin-top:6px;display:flex;gap:6px;">' +
            '<button style="flex:1;background:#334155;color:white;border:none;border-radius:6px;padding:4px;font-size:11px;cursor:pointer;" onclick="renderLine(linesData.find(x => x.id===\\'' + l.id + '\\'), 0)">' + (isAr ? '▶ ذهاب: ' : '▶ Aller: ') + dirAller + '</button>' +
            '<button style="flex:1;background:#334155;color:white;border:none;border-radius:6px;padding:4px;font-size:11px;cursor:pointer;" onclick="renderLine(linesData.find(x => x.id===\\'' + l.id + '\\'), 1)">' + (isAr ? '◀ إياب: ' : '◀ Retour: ') + dirRetour + '</button>' +
          '</div>';
        list.appendChild(card);
      }});
    }}

    document.getElementById('toggleLang').onclick = function() {{
      currentLang = currentLang === 'fr' ? 'ar' : 'fr';
      updateUI();
      if (linesData.length > 0) renderLine(linesData[0], 0);
    }};

    updateUI();
    renderLine(linesData[0], 0);
  </script>
</body>
</html>
"""

with open('buses_map.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved buses_map.html successfully!")

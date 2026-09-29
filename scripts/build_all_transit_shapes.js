import fs from 'fs';

async function buildAllTransitShapes() {
  console.log('Loading OSM shapes...');
  const shapes = JSON.parse(fs.readFileSync('scripts/osm_transit_shapes.json', 'utf8'));

  // Let's add RFR A and SNCFT trains from Tunismapper
  const tunismapperRoutes = [
    { route_id: 19, key: 'rfr_19' }, // RFR Ligne A
    { route_id: 1, key: 'train_1' },  // SNCFT
    { route_id: 3, key: 'train_3' },  // SNCFT
    { route_id: 4, key: 'train_4' },  // SNCFT Tunis-Bizerte
  ];

  for (const r of tunismapperRoutes) {
    try {
      console.log(`Fetching Tunismapper shape for route ${r.route_id}...`);
      const res = await fetch(`https://www.tunismapper.com/ligne_details.php?route_id=${r.route_id}`, {
        headers: { 'User-Agent': 'Mozilla/5.0' }
      });
      const text = await res.text();
      const match = text.match(/var shapes\s*=\s*(\[[\s\S]*?\]);/);
      if (match) {
        const rawShapes = JSON.parse(match[1]);
        if (rawShapes && rawShapes.length > 0 && rawShapes[0].length > 0) {
          // Decimate to keep ~1 point every 3 points so it stays light
          const pts = [];
          const rawPts = rawShapes[0];
          for (let i = 0; i < rawPts.length; i += 3) {
            pts.push([parseFloat(rawPts[i].shape_pt_lat), parseFloat(rawPts[i].shape_pt_lon)]);
          }
          shapes[r.key] = pts;
          console.log(`Added ${r.key} with ${pts.length} points (from ${rawPts.length})`);
        }
      }
    } catch (e) {
      console.error(`Error route ${r.route_id}:`, e.message);
    }
  }

  // Create mapping by static line ID
  // metro_50, metro_51, metro_52, metro_53, metro_54, metro_55, metro_56 (TGM), rfr_19, rfr_46, rfr_47, train_1, train_3, train_4
  const finalShapesByLineId = {
    'metro_50': shapes['metro_1'],
    'metro_51': shapes['metro_2'],
    'metro_52': shapes['metro_3'],
    'metro_53': shapes['metro_4'],
    'metro_54': shapes['metro_5'],
    'metro_55': shapes['metro_6'],
    'metro_56': shapes['tgm'],
    'rfr_19': shapes['rfr_19'],
    'rfr_46': shapes['rfr_D'],
    'rfr_47': shapes['rfr_E'],
    'train_1': shapes['train_1'],
    'train_3': shapes['train_3'],
    'train_4': shapes['train_4'],
  };

  fs.writeFileSync('src/data/transitShapes.json', JSON.stringify(finalShapesByLineId));
  console.log('Saved src/data/transitShapes.json successfully!');
}

buildAllTransitShapes();

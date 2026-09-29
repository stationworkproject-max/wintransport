import fs from 'fs';

async function extractTransitGeometries() {
  console.log('Fetching OpenStreetMap exact rail/tram traces for Grand Tunis...');
  const query = `[out:json][timeout:30];
  (
    relation["route"~"tram|light_rail|train"](36.7,10.0,36.9,10.4);
  );
  out geom;`;

  const url = 'https://overpass-api.de/api/interpreter?data=' + encodeURIComponent(query);
  const res = await fetch(url, { headers: { 'User-Agent': 'WinTransportTN/1.0' } });
  const data = await res.json();

  console.log(`Received ${data.elements?.length || 0} relations from OSM`);

  const lineShapes = {};

  data.elements?.forEach(el => {
    const ref = el.tags?.ref || '';
    const name = el.tags?.name || '';
    const route = el.tags?.route || '';
    
    // Extract continuous coordinates from ways
    const coords = [];
    el.members?.forEach(m => {
      if (m.type === 'way' && m.geometry) {
        m.geometry.forEach(pt => {
          coords.push([pt.lat, pt.lon]);
        });
      }
    });

    if (coords.length > 0) {
      console.log(`Relation ${el.id} [${ref}] "${name}" -> ${coords.length} points`);
      let key = null;
      if (ref === '1') key = 'metro_1';
      else if (ref === '2') key = 'metro_2';
      else if (ref === '3') key = 'metro_3';
      else if (ref === '4') key = 'metro_4';
      else if (ref === '5') key = 'metro_5';
      else if (ref === '6') key = 'metro_6';
      else if (ref === 'E') key = 'rfr_E';
      else if (ref === 'D') key = 'rfr_D';
      else if (name.includes('المرسى') || name.includes('حلق الوادي')) key = 'tgm';
      else if (name.includes('الرياض') || name.includes('برج السدرية')) key = 'train_banlieue_sud';

      if (key) {
        if (!lineShapes[key]) lineShapes[key] = [];
        lineShapes[key].push(...coords);
      }
    }
  });

  console.log('Identified network shapes keys:', Object.keys(lineShapes));
  fs.writeFileSync('scripts/osm_transit_shapes.json', JSON.stringify(lineShapes, null, 2));
  console.log('Saved to scripts/osm_transit_shapes.json');
}

extractTransitGeometries();

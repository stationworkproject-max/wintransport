import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { STATIC_LINES } from '../src/data/staticTransit.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');
const STATIC_PATH = path.join(ROOT, 'src/data/staticTransit.js');
const SHAPES_PATH = path.join(ROOT, 'src/data/transitShapes.json');

const line3D = STATIC_LINES.find(x => x.short_name === '3D');
if (!line3D) {
  console.error('Bus 3D not found');
  process.exit(1);
}

// Remove the two bogus stops that Tunismapper confused:
// "Mosquée Avenue Chebbi" (in Manouba) and "Lycee Chebi" (in Mornaguia)
const cleanStops = line3D.stops.filter(s => {
  const n = s.name.toLowerCase();
  return !n.includes('chebbi') && !n.includes('chebi');
});

console.log(`Cleaned Bus 3D from ${line3D.stops.length} to ${cleanStops.length} stops:`);
cleanStops.forEach((s, i) => console.log(`  ${i+1}. ${s.name} (${s.lat}, ${s.lon})`));

async function osrmRoute(stops) {
  const coords = stops.map(s => `${s.lon},${s.lat}`).join(';');
  const url = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`;
  const res = await fetch(url);
  const data = await res.json();
  if (!data.routes || !data.routes[0]) throw new Error('OSRM error');
  return {
    coords: data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon]),
    distanceKm: (data.routes[0].distance / 1000).toFixed(2)
  };
}

const aller = await osrmRoute(cleanStops);
console.log(`\nAller shape: ${aller.coords.length} points, distance: ${aller.distanceKm} km`);

const retour = await osrmRoute([...cleanStops].reverse());
console.log(`Retour shape: ${retour.coords.length} points, distance: ${retour.distanceKm} km`);

// Update transitShapes.json
const shapes = JSON.parse(fs.readFileSync(SHAPES_PATH, 'utf8'));
shapes['bus_851'] = aller.coords;
shapes['bus_851_0'] = aller.coords;
shapes['bus_851_1'] = retour.coords;
fs.writeFileSync(SHAPES_PATH, JSON.stringify(shapes));
console.log('✅ transitShapes.json updated for bus_851');

// Update staticTransit.js
let staticContent = fs.readFileSync(STATIC_PATH, 'utf8');
const idMarker = '"id": "bus_851"';
const idIdx = staticContent.indexOf(idMarker);
if (idIdx !== -1) {
  const stopsStart = staticContent.indexOf('"stops": [', idIdx);
  if (stopsStart !== -1) {
    let depth = 0;
    let i = stopsStart + 9;
    let inStr = false;
    let escape = false;
    let stopsEnd = -1;

    while (i < staticContent.length) {
      const ch = staticContent[i];
      if (escape) { escape = false; i++; continue; }
      if (ch === '\\' && inStr) { escape = true; i++; continue; }
      if (ch === '"') { inStr = !inStr; i++; continue; }
      if (!inStr) {
        if (ch === '[') depth++;
        else if (ch === ']') {
          depth--;
          if (depth === 0) { stopsEnd = i + 1; break; }
        }
      }
      i++;
    }

    if (stopsEnd !== -1) {
      const indent = '      ';
      const stopsJson = '[\n' + cleanStops.map(s => 
        indent + '{\n' +
        indent + `  "id": "${s.id}",\n` +
        indent + `  "stop_id": ${s.stop_id},\n` +
        indent + `  "name": "${s.name.replace(/"/g, '\\"')}",\n` +
        indent + `  "lat": ${s.lat},\n` +
        indent + `  "lon": ${s.lon},\n` +
        indent + `  "horaires_count": ${s.horaires_count || 0}\n` +
        indent + '}'
      ).join(',\n') + '\n    ]';

      staticContent = staticContent.substring(0, stopsStart + 9) + stopsJson + staticContent.substring(stopsEnd);
      fs.writeFileSync(STATIC_PATH, staticContent);
      console.log('✅ staticTransit.js updated for bus_851');
    }
  }
}

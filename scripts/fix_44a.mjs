import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { STATIC_LINES } from '../src/data/staticTransit.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');
const STATIC_PATH = path.join(ROOT, 'src/data/staticTransit.js');
const SHAPES_PATH = path.join(ROOT, 'src/data/transitShapes.json');

const line44A = STATIC_LINES.find(x => x.id === 'bus_884');
if (!line44A) {
  console.log('44A not found');
  process.exit(1);
}

// 44A is "Les Abattoirs - Kalaate Al Andalouss"
// Stops 1-13 were bogus South-Tunis stops (Barcelone, Djebel Jelloud, Sidi Fathallah)
const northStops = line44A.stops.filter(s => s.lat > 36.85);

// Add Les Abattoirs stop at the beginning
const abattoirsStop = {
  id: "st-7243",
  stop_id: 7243,
  name: "Les Abattoirs",
  lat: 36.8601659,
  lon: 10.1981876,
  horaires_count: 10
};

const cleanStops = [abattoirsStop, ...northStops];
console.log(`Cleaned 44A from ${line44A.stops.length} to ${cleanStops.length} stops:`);
cleanStops.slice(0, 5).forEach((s, i) => console.log(`  ${i+1}. ${s.name} (${s.lat}, ${s.lon})`));

function chunk(arr, size) {
  const chunks = [];
  for (let i = 0; i < arr.length; i += size - 1) {
    chunks.push(arr.slice(i, Math.min(i + size, arr.length)));
    if (i + size >= arr.length) break;
  }
  return chunks;
}

async function osrmRoute(stopSubset) {
  const coords = stopSubset.map(s => `${s.lon},${s.lat}`).join(';');
  const url = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`;
  const res = await fetch(url);
  const data = await res.json();
  if (!data.routes || !data.routes[0]) throw new Error('OSRM error');
  return data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon]);
}

async function buildShape(stops) {
  const chunks = chunk(stops, 14);
  let full = [];
  for (let i = 0; i < chunks.length; i++) {
    const segment = await osrmRoute(chunks[i]);
    if (i === 0) full = full.concat(segment);
    else full = full.concat(segment.slice(1));
    if (i < chunks.length - 1) await new Promise(r => setTimeout(r, 200));
  }
  return full;
}

const aller = await buildShape(cleanStops);
console.log(`Aller shape: ${aller.length} pts`);
const retour = await buildShape([...cleanStops].reverse());
console.log(`Retour shape: ${retour.length} pts`);

// Update transitShapes.json
const shapes = JSON.parse(fs.readFileSync(SHAPES_PATH, 'utf8'));
shapes['bus_884'] = aller;
shapes['bus_884_0'] = aller;
shapes['bus_884_1'] = retour;
fs.writeFileSync(SHAPES_PATH, JSON.stringify(shapes));
console.log('✅ transitShapes.json updated for bus_884');

// Update staticTransit.js
let staticContent = fs.readFileSync(STATIC_PATH, 'utf8');
const idMarker = '"id": "bus_884"';
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
      console.log('✅ staticTransit.js updated for bus_884');
    }
  }
}

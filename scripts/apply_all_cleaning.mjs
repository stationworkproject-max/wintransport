import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { STATIC_LINES } from '../src/data/staticTransit.js';
import { cleanLineStops } from './smart_stop_cleaner.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');
const STATIC_PATH = path.join(ROOT, 'src/data/staticTransit.js');
const SHAPES_PATH = path.join(ROOT, 'src/data/transitShapes.json');

const shapes = JSON.parse(fs.readFileSync(SHAPES_PATH, 'utf8'));

// OSRM helper
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
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (!data.routes || !data.routes[0]) throw new Error('No route');
    return data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon]);
  } catch {
    return stopSubset.map(s => [s.lat, s.lon]);
  }
}

async function buildShape(stops) {
  if (stops.length < 2) return stops.map(s => [s.lat, s.lon]);
  const chunks = chunk(stops, 14);
  let fullShape = [];
  for (let i = 0; i < chunks.length; i++) {
    const segment = await osrmRoute(chunks[i]);
    if (i === 0) fullShape = fullShape.concat(segment);
    else fullShape = fullShape.concat(segment.slice(1));
    if (i < chunks.length - 1) await new Promise(r => setTimeout(r, 200));
  }
  return fullShape;
}

// 1. Identify which lines need cleaning
const busLines = STATIC_LINES.filter(l => l.type_id === 'bus');
const linesToFix = [];

for (const line of busLines) {
  const cleaned = cleanLineStops(line.id, line.short_name, line.stops);
  const isDifferent = cleaned.length !== line.stops.length || 
                      cleaned.some((s, idx) => s.id !== line.stops[idx]?.id);
  if (isDifferent) {
    linesToFix.push({ line, cleaned });
  }
}

console.log(`\nLines to fix: ${linesToFix.length}`);

// 2. Read full staticTransit.js content
let staticContent = fs.readFileSync(STATIC_PATH, 'utf8');

for (let k = 0; k < linesToFix.length; k++) {
  const { line, cleaned } = linesToFix[k];
  console.log(`\n[${k+1}/${linesToFix.length}] Processing ${line.short_name} (${line.id}) - ${cleaned.length} stops...`);

  // Patch in staticTransit.js
  const idMarker = `"id": "${line.id}"`;
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
        const stopsJson = '[\n' + cleaned.map(s => 
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
      }
    }
  }

  // Regenerate shapes with OSRM
  console.log(`  Routing Aller shape...`);
  const allerShape = await buildShape(cleaned);
  await new Promise(r => setTimeout(r, 250));

  console.log(`  Routing Retour shape...`);
  const retourShape = await buildShape([...cleaned].reverse());
  await new Promise(r => setTimeout(r, 250));

  shapes[line.id] = allerShape;
  shapes[`${line.id}_0`] = allerShape;
  shapes[`${line.id}_1`] = retourShape;

  console.log(`  ✅ Done (Aller: ${allerShape.length} pts, Retour: ${retourShape.length} pts)`);
}

// 3. Save staticTransit.js and transitShapes.json
fs.writeFileSync(STATIC_PATH, staticContent);
fs.writeFileSync(SHAPES_PATH, JSON.stringify(shapes));

console.log('\n========================================');
console.log('✅ Successfully applied smart cleaning to all lines!');
console.log('✅ staticTransit.js and transitShapes.json updated!');
console.log('========================================');

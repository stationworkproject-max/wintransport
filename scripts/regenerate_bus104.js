/**
 * Regenerates bus_772 (Bus 104) shapes in transitShapes.json
 * Uses OSRM to route between the corrected stops (no fake waypoints)
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Read current stops from staticTransit.js
const staticContent = fs.readFileSync(
  path.join(__dirname, '../src/data/staticTransit.js'),
  'utf8'
);

// Parse bus_772 stops using regex
const bus772Match = staticContent.match(/"id":\s*"bus_772"[\s\S]*?"stops":\s*(\[[\s\S]*?\])\s*\}/);
if (!bus772Match) {
  console.error('Could not find bus_772 in staticTransit.js');
  process.exit(1);
}

const stops = JSON.parse(bus772Match[1]);
console.log(`Found ${stops.length} stops for bus_772`);
stops.forEach((s, i) => console.log(`  ${i+1}. ${s.name} (${s.lat}, ${s.lon})`));

// Chunk stops for OSRM (max 15 per request)
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
  if (!res.ok) throw new Error(`OSRM error: ${res.status}`);
  const data = await res.json();
  
  if (!data.routes || !data.routes[0]) throw new Error('No route returned');
  return data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon]);
}

async function buildShape(stops) {
  const chunks = chunk(stops, 15);
  console.log(`  Splitting into ${chunks.length} chunks`);
  
  let fullShape = [];
  for (let i = 0; i < chunks.length; i++) {
    console.log(`  Fetching chunk ${i+1}/${chunks.length} (${chunks[i].length} stops)...`);
    const segment = await osrmRoute(chunks[i]);
    if (i === 0) {
      fullShape = fullShape.concat(segment);
    } else {
      // Skip first point to avoid duplicate at junction
      fullShape = fullShape.concat(segment.slice(1));
    }
    if (i < chunks.length - 1) {
      await new Promise(r => setTimeout(r, 200));
    }
  }
  return fullShape;
}

async function main() {
  console.log('\nGenerating Aller (0) shape...');
  const allerShape = await buildShape(stops);
  
  await new Promise(r => setTimeout(r, 500));
  
  console.log('\nGenerating Retour (1) shape...');
  const retourShape = await buildShape([...stops].reverse());

  // Load current transitShapes.json
  const shapesPath = path.join(__dirname, '../src/data/transitShapes.json');
  const shapes = JSON.parse(fs.readFileSync(shapesPath, 'utf8'));

  // Update the three keys
  shapes['bus_772'] = allerShape;
  shapes['bus_772_0'] = allerShape;
  shapes['bus_772_1'] = retourShape;

  fs.writeFileSync(shapesPath, JSON.stringify(shapes, null, 0));
  console.log(`\n✅ Updated transitShapes.json`);
  console.log(`   bus_772   → ${allerShape.length} points`);
  console.log(`   bus_772_0 → ${allerShape.length} points`);
  console.log(`   bus_772_1 → ${retourShape.length} points`);
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});

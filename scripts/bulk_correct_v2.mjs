/**
 * BULK BUS LINE CORRECTOR v2
 * 
 * Source: https://tunismapper.com/ligne_details.php?route_id={route_id}
 * Extracts: var stops = [{name, lat, lon, stop_id, horaires}]
 * 
 * Phase 1: Fetch stops for all 190 bus lines from tunismapper
 * Phase 2: Update staticTransit.js with fresh stops
 * Phase 3: Regenerate OSRM shapes for all updated lines
 * 
 * Run: node scripts/bulk_correct_v2.mjs
 * Can be re-run safely - skips already-processed lines (tracked in log file)
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');

// ─── CONFIG ────────────────────────────────────────────────────────────────
const TUNISMAPPER_BASE = 'https://tunismapper.com/ligne_details.php?route_id=';
const OSRM_API = 'https://router.project-osrm.org/route/v1/driving';
const FETCH_DELAY = 600;       // delay between tunismapper fetches (be polite)
const OSRM_DELAY = 200;        // delay between OSRM chunks
const OSRM_CHUNK = 13;         // stops per chunk (max 15, overlap 1)
const SHAPES_PATH = path.join(ROOT, 'src/data/transitShapes.json');
const STATIC_PATH = path.join(ROOT, 'src/data/staticTransit.js');
const LOG_PATH = path.join(ROOT, 'scripts/bulk_v2_log.json');
const SAVE_EVERY = 5;          // save progress every N lines

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// ─── FETCH STOP DATA FROM TUNISMAPPER ──────────────────────────────────────
async function fetchTunismapperStops(routeId) {
  const url = `${TUNISMAPPER_BASE}${routeId}`;
  const headers = { 
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0',
    'Accept': 'text/html'
  };
  
  const res = await fetch(url, { headers, signal: AbortSignal.timeout(20000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const html = await res.text();
  
  // Extract: var stops = [...]
  const stopsMatch = html.match(/var stops\s*=\s*(\[[\s\S]*?\]);(?=\s*\n|\s*var )/);
  if (!stopsMatch) {
    // Try alternate pattern
    const altMatch = html.match(/var stops\s*=\s*(\[[\s\S]*?\])\s*;/);
    if (!altMatch) throw new Error('No stops variable found in page');
    return parseStops(altMatch[1]);
  }
  return parseStops(stopsMatch[1]);
}

function parseStops(stopsJson) {
  const raw = JSON.parse(stopsJson);
  return raw
    .map(s => ({
      id: `st-${s.stop_id}`,
      stop_id: parseInt(s.stop_id),
      name: s.name,
      lat: parseFloat(s.lat),
      lon: parseFloat(s.lon),
      horaires_count: Array.isArray(s.horaires) ? s.horaires.length : 0
    }))
    .filter(s => !isNaN(s.lat) && !isNaN(s.lon) && s.lat !== 0 && s.lon !== 0);
}

// ─── OSRM SHAPE BUILDING ───────────────────────────────────────────────────
function chunkWithOverlap(stops, size) {
  if (stops.length <= size + 1) return [stops];
  const chunks = [];
  for (let i = 0; i < stops.length - 1; i += size) {
    chunks.push(stops.slice(i, Math.min(i + size + 1, stops.length)));
    if (i + size + 1 >= stops.length) break;
  }
  return chunks;
}

async function buildOsrmShape(stops) {
  if (stops.length < 2) return stops.map(s => [s.lat, s.lon]);
  
  const chunks = chunkWithOverlap(stops, OSRM_CHUNK);
  let fullShape = [];
  
  for (let i = 0; i < chunks.length; i++) {
    const coords = chunks[i].map(s => `${s.lon},${s.lat}`).join(';');
    const url = `${OSRM_API}/${coords}?overview=full&geometries=geojson`;
    
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(15000) });
      if (!res.ok) throw new Error(`OSRM ${res.status}`);
      const data = await res.json();
      if (!data.routes?.[0]) throw new Error('No OSRM route');
      const segment = data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon]);
      fullShape = i === 0 ? segment : [...fullShape, ...segment.slice(1)];
    } catch {
      // Fallback: straight segments
      const fallback = chunks[i].map(s => [s.lat, s.lon]);
      fullShape = i === 0 ? fallback : [...fullShape, ...fallback.slice(1)];
    }
    
    if (i < chunks.length - 1) await sleep(OSRM_DELAY);
  }
  
  return fullShape;
}

// ─── STATIC FILE PATCHING ──────────────────────────────────────────────────
// Find bus line block in staticTransit.js and replace its stops
function patchLineStops(content, busId, newStops) {
  // Find the block starting with the id
  const idMarker = `"id": "${busId}"`;
  const idIdx = content.indexOf(idMarker);
  if (idIdx === -1) return { content, changed: false };
  
  // Find the "stops": [ ... ] block within this line entry
  // Start searching from the id position
  const stopsStart = content.indexOf('"stops": [', idIdx);
  if (stopsStart === -1) return { content, changed: false };
  
  // Find the matching closing bracket
  let depth = 0;
  let i = stopsStart + 9; // skip '"stops": '
  let inStr = false;
  let escape = false;
  let stopsEnd = -1;
  
  while (i < content.length) {
    const ch = content[i];
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
  
  if (stopsEnd === -1) return { content, changed: false };
  
  // Make sure we're still within this line entry (not a different line)
  // The next "id": "bus_ should be after stopsEnd
  const nextBusId = content.indexOf('"id": "bus_', idIdx + 1);
  if (nextBusId !== -1 && stopsEnd > nextBusId) {
    return { content, changed: false }; // Something is wrong
  }
  
  // Build new stops JSON
  const indent = '      ';
  const stopsJson = '[\n' + newStops.map(s => 
    indent + '{\n' +
    indent + `  "id": "${s.id}",\n` +
    indent + `  "stop_id": ${s.stop_id},\n` +
    indent + `  "name": "${s.name.replace(/"/g, '\\"')}",\n` +
    indent + `  "lat": ${s.lat},\n` +
    indent + `  "lon": ${s.lon},\n` +
    indent + `  "horaires_count": ${s.horaires_count}\n` +
    indent + '}'
  ).join(',\n') + '\n    ]';
  
  const oldStopsBlock = content.substring(stopsStart + 9, stopsEnd); // +9 to skip '"stops": '
  const newContent = content.substring(0, stopsStart + 9) + stopsJson + content.substring(stopsEnd);
  
  // Check if actually changed
  const changed = oldStopsBlock !== stopsJson;
  return { content: newContent, changed };
}

// ─── EXTRACT ALL BUS LINES FROM STATIC FILE ────────────────────────────────
function extractBusLines(content) {
  const lines = [];
  // Match id and route_id in proximity
  const regex = /"id":\s*"(bus_(\d+))"(?:[\s\S]*?)"route_id":\s*"(\d+)"/g;
  let m;
  while ((m = regex.exec(content)) !== null) {
    // Verify the route_id matches the numeric part of the id
    lines.push({
      id: m[1],
      numericId: m[2],
      routeId: m[3]
    });
  }
  return lines;
}

// ─── MAIN ───────────────────────────────────────────────────────────────────
async function main() {
  console.log('═══════════════════════════════════════════════════════');
  console.log('  BULK BUS LINE CORRECTOR v2 — tunismapper.com source');
  console.log('═══════════════════════════════════════════════════════\n');

  let content = fs.readFileSync(STATIC_PATH, 'utf8');
  const shapes = JSON.parse(fs.readFileSync(SHAPES_PATH, 'utf8'));
  
  // Load or init progress log
  let log = {};
  if (fs.existsSync(LOG_PATH)) {
    try { log = JSON.parse(fs.readFileSync(LOG_PATH, 'utf8')); } catch {}
  }
  
  const busLines = extractBusLines(content);
  console.log(`Found ${busLines.length} bus lines\n`);

  const results = { success: 0, skipped: 0, failed: 0, unchanged: 0 };
  let contentDirty = false;
  let shapesDirty = false;
  let processedSinceLastSave = 0;

  for (let i = 0; i < busLines.length; i++) {
    const { id, routeId } = busLines[i];
    const progress = `[${String(i+1).padStart(3)}/${busLines.length}]`;

    // Skip if already done
    if (log[id]?.status === 'success') {
      process.stdout.write(`${progress} ✓ ${id} (skipped)\n`);
      results.skipped++;
      continue;
    }

    process.stdout.write(`${progress} Fetching ${id} (route ${routeId})... `);
    
    await sleep(FETCH_DELAY);
    
    try {
      const stops = await fetchTunismapperStops(routeId);
      
      if (!stops || stops.length < 2) {
        console.log(`⚠️  Only ${stops?.length ?? 0} stops`);
        log[id] = { status: 'insufficient', routeId, stopCount: stops?.length ?? 0 };
        results.failed++;
        continue;
      }
      
      process.stdout.write(`${stops.length} stops → OSRM... `);
      
      // Patch static file
      const patch = patchLineStops(content, id, stops);
      if (patch.changed) {
        content = patch.content;
        contentDirty = true;
      }
      
      // Build OSRM shapes
      const allerShape = await buildOsrmShape(stops);
      await sleep(300);
      const retourShape = await buildOsrmShape([...stops].reverse());
      
      shapes[id] = allerShape;
      shapes[`${id}_0`] = allerShape;
      shapes[`${id}_1`] = retourShape;
      shapesDirty = true;
      
      console.log(`✅ (${allerShape.length} pts)`);
      
      log[id] = { 
        status: 'success', routeId, 
        stopCount: stops.length, 
        changed: patch.changed 
      };
      results.success++;
      processedSinceLastSave++;
      
    } catch (err) {
      console.log(`❌ ${err.message}`);
      log[id] = { status: 'error', routeId, error: err.message };
      results.failed++;
    }
    
    // Save progress periodically
    if (processedSinceLastSave >= SAVE_EVERY) {
      fs.writeFileSync(STATIC_PATH, content);
      fs.writeFileSync(SHAPES_PATH, JSON.stringify(shapes));
      fs.writeFileSync(LOG_PATH, JSON.stringify(log, null, 2));
      console.log(`\n  💾 Saved (${i+1}/${busLines.length} processed)\n`);
      processedSinceLastSave = 0;
    }
  }

  // Final save
  if (contentDirty) {
    fs.writeFileSync(STATIC_PATH, content);
    console.log('\n✅ staticTransit.js saved');
  }
  if (shapesDirty) {
    fs.writeFileSync(SHAPES_PATH, JSON.stringify(shapes));
    console.log('✅ transitShapes.json saved');
  }
  fs.writeFileSync(LOG_PATH, JSON.stringify(log, null, 2));

  console.log('\n═══════════════════════════════════════════════════════');
  console.log('  DONE');
  console.log(`  ✅ Updated:  ${results.success}`);
  console.log(`  ⏭  Skipped: ${results.skipped}`);
  console.log(`  ❌ Failed:  ${results.failed}`);
  console.log('═══════════════════════════════════════════════════════');
}

main().catch(err => {
  console.error('\nFATAL:', err);
  process.exit(1);
});

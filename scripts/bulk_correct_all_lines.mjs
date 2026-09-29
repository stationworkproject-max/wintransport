/**
 * BULK BUS LINE CORRECTOR
 * 
 * Phase 1: Fetch fresh stop data from tunismapper.com for all 190 bus lines
 * Phase 2: Update staticTransit.js with fresh stops
 * Phase 3: Regenerate OSRM shapes for all lines
 * 
 * Run: node scripts/bulk_correct_all_lines.mjs
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');

// ─── CONFIG ────────────────────────────────────────────────────────────────
const TUNISMAPPER_API = 'https://tunismapper.com/api';
const OSRM_API = 'https://router.project-osrm.org/route/v1/driving';
const DELAY_MS = 300;          // delay between API calls
const OSRM_CHUNK = 14;         // stops per OSRM request (max 15 = 14+1 overlap)
const SHAPES_PATH = path.join(ROOT, 'src/data/transitShapes.json');
const STATIC_PATH = path.join(ROOT, 'src/data/staticTransit.js');
const LOG_PATH = path.join(ROOT, 'scripts/bulk_correct_log.json');

// ─── UTILITIES ──────────────────────────────────────────────────────────────
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, { ...opts, signal: AbortSignal.timeout(15000) });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

// ─── TUNISMAPPER: fetch stops for a route ───────────────────────────────────
async function fetchRouteStops(routeId) {
  // Try the main route endpoint
  const url = `${TUNISMAPPER_API}/route/${routeId}/stops`;
  try {
    const data = await fetchJSON(url);
    if (data && Array.isArray(data.stops) && data.stops.length > 0) {
      return data.stops.map(s => ({
        id: `st-${s.stop_id}`,
        stop_id: s.stop_id,
        name: s.stop_name || s.name,
        lat: parseFloat(s.stop_lat || s.lat),
        lon: parseFloat(s.stop_lon || s.lon),
        horaires_count: s.horaires_count || 0
      })).filter(s => s.lat && s.lon && !isNaN(s.lat) && !isNaN(s.lon));
    }
  } catch (e) {
    // fallback to alternate endpoint
  }
  
  // Try alternate endpoint format
  try {
    const url2 = `${TUNISMAPPER_API}/routes/${routeId}`;
    const data2 = await fetchJSON(url2);
    const stops = data2.stops || data2.route?.stops || [];
    if (stops.length > 0) {
      return stops.map(s => ({
        id: `st-${s.stop_id}`,
        stop_id: s.stop_id,
        name: s.stop_name || s.name,
        lat: parseFloat(s.stop_lat || s.lat),
        lon: parseFloat(s.stop_lon || s.lon),
        horaires_count: s.horaires_count || 0
      })).filter(s => s.lat && s.lon && !isNaN(s.lat) && !isNaN(s.lon));
    }
  } catch (e2) {
    throw new Error(`Both endpoints failed for route ${routeId}: ${e2.message}`);
  }
  
  return null;
}

// ─── OSRM: build polyline shape for a stop list ────────────────────────────
function chunkStops(stops, size) {
  const chunks = [];
  for (let i = 0; i < stops.length; i += size) {
    // Overlap by 1 to avoid gaps
    const end = Math.min(i + size + 1, stops.length);
    chunks.push(stops.slice(i, end));
    if (end === stops.length) break;
  }
  return chunks;
}

async function buildOsrmShape(stops) {
  if (stops.length < 2) return stops.map(s => [s.lat, s.lon]);
  
  const chunks = chunkStops(stops, OSRM_CHUNK);
  let fullShape = [];
  
  for (let i = 0; i < chunks.length; i++) {
    const coords = chunks[i].map(s => `${s.lon},${s.lat}`).join(';');
    const url = `${OSRM_API}/${coords}?overview=full&geometries=geojson`;
    
    try {
      const data = await fetchJSON(url);
      if (!data.routes?.[0]) throw new Error('No route');
      const segment = data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon]);
      
      if (i === 0) {
        fullShape = segment;
      } else {
        // Skip first point to avoid duplicate junction
        fullShape = fullShape.concat(segment.slice(1));
      }
    } catch (e) {
      // Fallback: straight lines between stops in this chunk
      const fallback = chunks[i].map(s => [s.lat, s.lon]);
      if (i === 0) fullShape = fallback;
      else fullShape = fullShape.concat(fallback.slice(1));
    }
    
    if (i < chunks.length - 1) await sleep(150);
  }
  
  return fullShape;
}

// ─── EXTRACT all bus lines from staticTransit.js ───────────────────────────
function extractBusLines(content) {
  const lines = [];
  // Match each bus entry block
  const entryRegex = /\{\s*"id":\s*"(bus_\d+)"[\s\S]*?"route_id":\s*"(\d+)"[\s\S]*?"short_name":\s*"([^"]+)"[\s\S]*?"stops":\s*\[[\s\S]*?\]\s*\}/g;
  let m;
  while ((m = entryRegex.exec(content)) !== null) {
    lines.push({
      id: m[1],
      routeId: m[2],
      shortName: m[3],
      matchStart: m.index,
      matchEnd: m.index + m[0].length,
      fullMatch: m[0]
    });
  }
  return lines;
}

// ─── REPLACE stops block in a line entry ────────────────────────────────────
function replaceStops(lineEntry, newStops) {
  const stopsJson = JSON.stringify(newStops, null, 2)
    .split('\n').map((l, i) => i === 0 ? l : '    ' + l).join('\n');
  return lineEntry.replace(/"stops":\s*\[[\s\S]*?\](?=\s*\})/, `"stops": ${stopsJson}`);
}

// ─── MAIN ───────────────────────────────────────────────────────────────────
async function main() {
  console.log('═══════════════════════════════════════════════════');
  console.log('  BULK BUS LINE CORRECTOR');
  console.log('═══════════════════════════════════════════════════\n');

  // Load current data
  let content = fs.readFileSync(STATIC_PATH, 'utf8');
  const shapes = JSON.parse(fs.readFileSync(SHAPES_PATH, 'utf8'));
  
  // Extract all bus lines
  const busLines = extractBusLines(content);
  console.log(`Found ${busLines.length} bus lines to process\n`);

  // Load existing log (to resume if interrupted)
  let log = {};
  if (fs.existsSync(LOG_PATH)) {
    try { log = JSON.parse(fs.readFileSync(LOG_PATH, 'utf8')); } catch {}
  }

  const results = { success: [], failed: [], skipped: [], unchanged: [] };
  let contentModified = false;
  let shapesModified = false;

  // Process each bus line
  for (let i = 0; i < busLines.length; i++) {
    const line = busLines[i];
    const progress = `[${i+1}/${busLines.length}]`;
    
    // Skip if already successfully processed in a previous run
    if (log[line.id]?.status === 'success') {
      console.log(`${progress} ✓ SKIP ${line.shortName} (${line.id}) - already done`);
      results.skipped.push(line.id);
      continue;
    }

    process.stdout.write(`${progress} Fetching Bus ${line.shortName} (route ${line.routeId})... `);
    
    try {
      await sleep(DELAY_MS);
      const freshStops = await fetchRouteStops(line.routeId);
      
      if (!freshStops || freshStops.length < 2) {
        console.log(`⚠️  No data (${freshStops?.length ?? 0} stops)`);
        log[line.id] = { status: 'no_data', shortName: line.shortName };
        results.failed.push({ id: line.id, reason: 'no_data' });
        continue;
      }

      console.log(`${freshStops.length} stops`);

      // Find current stops count for comparison  
      const currentStopsMatch = line.fullMatch.match(/"stops":\s*\[([\s\S]*?)\](?=\s*\})/);
      const currentStopCount = (currentStopsMatch?.[1].match(/"stop_id"/g) || []).length;
      
      // Update static file content
      // Re-find position in current content (since content may have changed)
      const currentIdx = content.indexOf(line.fullMatch);
      if (currentIdx === -1) {
        // Try finding by id
        const idIdx = content.indexOf(`"id": "${line.id}"`);
        if (idIdx === -1) {
          console.log(`  ⚠️  Could not locate in file, skipping`);
          continue;
        }
      }

      const updatedEntry = replaceStops(line.fullMatch, freshStops);
      if (updatedEntry !== line.fullMatch) {
        content = content.replace(line.fullMatch, updatedEntry);
        // Update fullMatch for any subsequent reference
        line.fullMatch = updatedEntry;
        contentModified = true;
      }

      // Generate OSRM shapes
      process.stdout.write(`  → Generating shapes... `);
      const allerShape = await buildOsrmShape(freshStops);
      await sleep(200);
      const retourShape = await buildOsrmShape([...freshStops].reverse());
      
      shapes[line.id] = allerShape;
      shapes[`${line.id}_0`] = allerShape;
      shapes[`${line.id}_1`] = retourShape;
      shapesModified = true;
      
      console.log(`✅ ${allerShape.length} pts aller, ${retourShape.length} pts retour`);
      
      log[line.id] = { 
        status: 'success', 
        shortName: line.shortName,
        stopCount: freshStops.length,
        prevStopCount: currentStopCount
      };
      results.success.push(line.id);
      
    } catch (err) {
      console.log(`❌ ${err.message}`);
      log[line.id] = { status: 'error', shortName: line.shortName, error: err.message };
      results.failed.push({ id: line.id, reason: err.message });
    }
    
    // Save progress every 10 lines
    if ((i + 1) % 10 === 0) {
      fs.writeFileSync(STATIC_PATH, content);
      fs.writeFileSync(SHAPES_PATH, JSON.stringify(shapes));
      fs.writeFileSync(LOG_PATH, JSON.stringify(log, null, 2));
      console.log(`\n  💾 Progress saved (${i+1}/${busLines.length})\n`);
    }
  }

  // Final save
  if (contentModified) {
    fs.writeFileSync(STATIC_PATH, content);
    console.log('\n✅ staticTransit.js saved');
  }
  if (shapesModified) {
    fs.writeFileSync(SHAPES_PATH, JSON.stringify(shapes));
    console.log('✅ transitShapes.json saved');
  }
  fs.writeFileSync(LOG_PATH, JSON.stringify(log, null, 2));

  // Summary
  console.log('\n═══════════════════════════════════════════════════');
  console.log('  SUMMARY');
  console.log('═══════════════════════════════════════════════════');
  console.log(`  ✅ Success:   ${results.success.length}`);
  console.log(`  ⏭  Skipped:  ${results.skipped.length}`);
  console.log(`  ❌ Failed:   ${results.failed.length}`);
  if (results.failed.length > 0) {
    console.log('\n  Failed lines:');
    results.failed.forEach(f => console.log(`    - ${f.id}: ${f.reason}`));
  }
}

main().catch(err => {
  console.error('\nFATAL:', err);
  process.exit(1);
});

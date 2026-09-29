/**
 * TEST: Run bulk corrector on just 3 lines to verify it works
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');

const TUNISMAPPER_BASE = 'https://tunismapper.com/ligne_details.php?route_id=';
const OSRM_API = 'https://router.project-osrm.org/route/v1/driving';
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function fetchTunismapperStops(routeId) {
  const url = `${TUNISMAPPER_BASE}${routeId}`;
  const headers = { 
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0',
  };
  const res = await fetch(url, { headers, signal: AbortSignal.timeout(20000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const html = await res.text();
  
  // Match var stops = [...]
  const m = html.match(/var stops\s*=\s*(\[[\s\S]*?\]);?\s*\n/);
  if (!m) {
    // Try without newline constraint
    const m2 = html.match(/var stops\s*=\s*(\[[\s\S]*?\])\s*;/);
    if (!m2) {
      // Save for debug
      fs.writeFileSync(`scripts/debug_${routeId}.html`, html.substring(0, 5000));
      throw new Error('No stops variable found');
    }
    return JSON.parse(m2[1]).map(s => ({
      id: `st-${s.stop_id}`,
      stop_id: parseInt(s.stop_id),
      name: s.name,
      lat: parseFloat(s.lat),
      lon: parseFloat(s.lon),
      horaires_count: Array.isArray(s.horaires) ? s.horaires.length : 0
    })).filter(s => !isNaN(s.lat) && !isNaN(s.lon));
  }
  return JSON.parse(m[1]).map(s => ({
    id: `st-${s.stop_id}`,
    stop_id: parseInt(s.stop_id),
    name: s.name,
    lat: parseFloat(s.lat),
    lon: parseFloat(s.lon),
    horaires_count: Array.isArray(s.horaires) ? s.horaires.length : 0
  })).filter(s => !isNaN(s.lat) && !isNaN(s.lon));
}

// Test on 3 lines: bus_772 (104), bus_723 (35), bus_711 (20)
const TEST_LINES = [
  { id: 'bus_772', routeId: '772', shortName: '104' },
  { id: 'bus_723', routeId: '723', shortName: '35' },
  { id: 'bus_711', routeId: '711', shortName: '20' },
];

for (const line of TEST_LINES) {
  try {
    console.log(`\nFetching ${line.shortName} (route ${line.routeId})...`);
    await sleep(500);
    const stops = await fetchTunismapperStops(line.routeId);
    console.log(`  ✅ ${stops.length} stops`);
    stops.forEach((s, i) => console.log(`    ${i+1}. [${s.stop_id}] ${s.name} (${s.lat}, ${s.lon})`));
  } catch (e) {
    console.log(`  ❌ ${e.message}`);
  }
}

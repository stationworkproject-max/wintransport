/**
 * Find tunismapper's backend API endpoints and extract route-specific stop data
 */

async function tryEndpoints() {
  const base = 'https://tunismapper.com/backend/api';
  const headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' };
  
  const endpoints = [
    // Search stops
    `${base}/searchStops.php?q=Tunis Marine`,
    `${base}/searchStops.php?q=104`,
    
    // Try route-specific endpoints
    `${base}/getRouteStops.php?route_id=772`,
    `${base}/getStops.php?route=772`,
    `${base}/route.php?id=772`,
    `${base}/ligne.php?id=772`,
    `${base}/stops.php?route=772`,
    `${base}/horaires.php?route=772`,
    `${base}/route_stops.php?route=772`,
    `${base}/getLine.php?id=772`,
    
    // GTFS-style
    `https://tunismapper.com/backend/gtfs/stop_times.txt`,
    `https://tunismapper.com/backend/gtfs/trips.txt`,
    `https://tunismapper.com/backend/data/routes.json`,
    `https://tunismapper.com/backend/data/stops.json`,
  ];
  
  for (const url of endpoints) {
    try {
      const res = await fetch(url, { headers, signal: AbortSignal.timeout(8000) });
      console.log(`[${res.status}] ${url}`);
      if (res.status === 200) {
        const body = await res.text();
        console.log('  → BODY:', body.substring(0, 300));
      }
    } catch (e) {
      console.log(`[ERR] ${url}: ${e.message}`);
    }
  }
}

// Also look at what's in the big script for the station filtering
import fs from 'fs';
const script = fs.readFileSync('scripts/tunismapper_bigscript.js', 'utf8');

// Find arrays that look like stop_id sequences for specific routes
// Look for the part of the script that has station IDs  
// We know the stations array starts with {stop_id:172,...}
// But the route page shows only the stops FOR that route
// So there must be a second variable after stations

const stationsEnd = script.indexOf('const stations') + script.match(/const stations\s*=\s*\[[\s\S]*?\];/)[0].length;
console.log('\n\nContent AFTER stations array:');
console.log(script.substring(stationsEnd, stationsEnd + 3000));

tryEndpoints().catch(console.error);

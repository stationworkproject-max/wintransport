/**
 * Find route-specific stop assignments in tunismapper HTML
 */
import fs from 'fs';

const html = fs.readFileSync('scripts/tunismapper_route772.html', 'utf8');

// Look for mapStations assignment - it likely contains the filtered stops
const mapStationsMatch = html.match(/const mapStations\s*=\s*([\s\S]*?)(?=const\s|<\/script>)/);
if (mapStationsMatch) {
  console.log('mapStations:', mapStationsMatch[1].substring(0, 500));
}

// Look for polyline/route trace data
const polylineMatch = html.match(/L\.polyline\((\[[\s\S]*?\])/);
if (polylineMatch) {
  console.log('\nPolyline data found:', polylineMatch[1].substring(0, 200));
}

// Look for the route-specific stop list embedded in some other variable
// Search for arrays of stop_ids
const stopIdArrays = html.match(/\[\s*\d+\s*(?:,\s*\d+\s*){3,}\]/g) || [];
console.log('\nNumeric arrays (potential stop_id lists):', stopIdArrays.slice(0, 5));

// Look for route trace coordinates
const coordPattern = html.match(/\[\s*36\.\d+\s*,\s*10\.\d+\s*\]/g) || [];
console.log('\nCoordinate pairs found:', coordPattern.length);
if (coordPattern.length > 0) console.log('Sample:', coordPattern.slice(0, 3));

// Search for script blocks
const scriptBlocks = html.match(/<script[^>]*>([\s\S]*?)<\/script>/g) || [];
console.log('\nTotal script blocks:', scriptBlocks.length);

// Find the script that has route-specific data
for (let i = 0; i < scriptBlocks.length; i++) {
  const script = scriptBlocks[i];
  if (script.includes('772') && script.length > 500) {
    console.log(`\nScript block ${i} mentions route 772 (${script.length} chars):`);
    console.log(script.substring(0, 1000));
    break;
  }
}

// Look for selectedRoute or similar
const selectedMatch = html.match(/selected[Rr]oute\s*=\s*['"]\d+['"]|currentRoute\s*=\s*\d+|routeId\s*=\s*\d+/);
console.log('\nSelected route variable:', selectedMatch?.[0]);

// Look for the route stops in HTML data attributes
const dataRoute = html.match(/data-route(?:-id)?\s*=\s*["']772["']/);
console.log('\nData route attr:', dataRoute?.[0]);

// Find where 7225 appears and look for surrounding stop list context
const all7225 = [];
let pos = 0;
while ((pos = html.indexOf('7225', pos)) !== -1) {
  all7225.push(pos);
  pos += 1;
}
console.log('\nPositions of "7225" in HTML:', all7225.slice(0, 10));
// Check each for context
for (const p of all7225.slice(0, 5)) {
  console.log(`\n  At ${p}:`, html.substring(p-50, p+100));
}

/**
 * Find how tunismapper maps route_id to specific stops
 * Looking for route/stop mapping table embedded in JS
 */
import fs from 'fs';

const html = fs.readFileSync('scripts/tunismapper_route772.html', 'utf8');

// Find the big script block (block 11)
const scriptBlocks = html.match(/<script[^>]*>([\s\S]*?)<\/script>/g) || [];
const bigScript = scriptBlocks[11]; // the one with 772

// Look for route-stop mapping: route_id mapped to array of stop_ids
// Search for patterns like {route_id: 772, stops: [...]} or route:772
const route772Context = [];
let searchPos = 0;
while (true) {
  const pos = bigScript.indexOf('772', searchPos);
  if (pos === -1) break;
  route772Context.push({ pos, context: bigScript.substring(Math.max(0, pos-80), pos+200) });
  searchPos = pos + 1;
  if (route772Context.length > 20) break;
}

console.log(`Found ${route772Context.length} occurrences of "772" in script:`);
route772Context.forEach((c, i) => {
  console.log(`\n[${i}] at ${c.pos}:`);
  console.log(c.context);
});

// Look for route_stops array or similar
const routeStopsPatterns = [
  /const route_stops\s*=\s*(\[[\s\S]*?\])\s*;/,
  /const horaires\s*=\s*(\[[\s\S]*?\])\s*;/,
  /const line_stops\s*=\s*(\[[\s\S]*?\])\s*;/,
  /route_id.*?772[\s\S]{0,500}stop/,
  /772.*?stop_ids.*?(\[[\d,\s]+\])/,
];

for (const pattern of routeStopsPatterns) {
  const m = bigScript.match(pattern);
  if (m) {
    console.log('\nFound pattern:', pattern.toString().substring(0, 50));
    console.log(m[0].substring(0, 300));
  }
}

// Search for a horaires/schedules variable that might link routes to stops
const horairesMatch = bigScript.match(/const horaires\s*=\s*([\s\S]*?)(?=\nconst |\n<\/script>)/);
if (horairesMatch) {
  console.log('\nHoraires variable found:', horairesMatch[1].substring(0, 500));
}

// Look for any arrays that contain specifically the stop IDs we know are on bus 104
// Known stop IDs: 7225, 7436, 7363, 7235, 7841, 7391, 7392, 7802, 7182
const knownIds = [7225, 7436, 7363, 7235, 7841, 7391, 7802, 7182, 7183];
const knownIdStr = knownIds.map(String);

// Find any JSON array containing multiple of these IDs in sequence
for (const id of knownIdStr) {
  const idx = bigScript.indexOf(`"route_id":${id}`) || bigScript.indexOf(`"route_id":"${id}"`);
  if (idx > 0) {
    console.log(`\nFound route reference for ${id}:`, bigScript.substring(idx-50, idx+200));
  }
}

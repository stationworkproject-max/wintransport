import fs from 'fs';
const content = fs.readFileSync('src/data/staticTransit.js', 'utf8');

// Extract all bus lines: id, short_name, route_id, stop count
const busLineRegex = /"id":\s*"(bus_(\d+))"[\s\S]*?"route_id":\s*"(\d+)"[\s\S]*?"short_name":\s*"([^"]+)"[\s\S]*?"stops":\s*\[([\s\S]*?)(?=\]\s*\})/g;

const results = [];
let m;
while ((m = busLineRegex.exec(content)) !== null) {
  const id = m[1];
  const routeId = m[3];
  const shortName = m[4];
  const stopsBlock = m[5];
  const stopCount = (stopsBlock.match(/"stop_id"/g) || []).length;
  results.push({ id, routeId, shortName, stopCount });
}

console.log(`Total bus lines found: ${results.length}`);
results.forEach(r => console.log(`${r.routeId}\t${r.shortName}\t${r.id}\t${r.stopCount} stops`));

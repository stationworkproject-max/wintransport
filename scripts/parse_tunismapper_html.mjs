/**
 * Parse tunismapper.com HTML page for a route and extract stop data
 * The site embeds: const stations = [...] and const routes = [...]
 */
import fs from 'fs';

const html = fs.readFileSync('scripts/tunismapper_route772.html', 'utf8');

// Extract the stations array
const stationsMatch = html.match(/const stations\s*=\s*(\[[\s\S]*?\]);/);
const routesMatch = html.match(/const routes\s*=\s*(\[[\s\S]*?\]);/);
const stopsMatch = html.match(/const stops\s*=\s*(\[[\s\S]*?\]);/);
const routeStopsMatch = html.match(/const route_stops\s*=\s*(\[[\s\S]*?\]);/);

console.log('Found stations:', !!stationsMatch, stationsMatch ? stationsMatch[1].length + ' chars' : '');
console.log('Found routes:', !!routesMatch, routesMatch ? routesMatch[1].length + ' chars' : '');
console.log('Found stops:', !!stopsMatch, stopsMatch ? stopsMatch[1].length + ' chars' : '');
console.log('Found route_stops:', !!routeStopsMatch, routeStopsMatch ? routeStopsMatch[1].length + ' chars' : '');

if (stationsMatch) {
  const stations = JSON.parse(stationsMatch[1]);
  console.log(`\nTotal stations: ${stations.length}`);
  console.log('Sample station:', stations[0]);
}

// Look for all const/var/let assignments
const assignments = html.match(/(?:const|var|let)\s+(\w+)\s*=/g) || [];
console.log('\nAll JS variable assignments:', [...new Set(assignments)]);

// Also search for line-specific data
const lineData = html.match(/route_id["\s:]+772[\s\S]{0,2000}/);
if (lineData) {
  console.log('\nRoute 772 specific data:', lineData[0].substring(0, 500));
}

// Search for arrays that contain our known stops
const knownStop = '7225'; // Terminus Tunis Marine Bus stop_id
const idx = html.indexOf(knownStop);
if (idx > 0) {
  console.log('\nContext around stop 7225:', html.substring(idx - 100, idx + 300));
}

/**
 * Fetch station details to find which routes serve each stop
 * Then reverse-engineer: for each route, which stops does it serve?
 */
import fs from 'fs';

// Test with a known stop on bus 104
const testStops = [7225, 7436, 7363, 7802, 7182]; // Bus 104 stops

async function getStationDetails(stopId) {
  const url = `https://tunismapper.com/station_details.php?id=${stopId}`;
  const headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' };
  
  const res = await fetch(url, { headers, signal: AbortSignal.timeout(10000) });
  return { status: res.status, body: await res.text() };
}

// First try one stop
const result = await getStationDetails(7225);
console.log(`station_details.php?id=7225 → Status: ${result.status}, Size: ${result.body.length}`);

if (result.status === 200) {
  // Look for route/line references
  const routeRefs = result.body.match(/route[^<"]{0,100}/gi) || [];
  const lineRefs = result.body.match(/ligne[^<"]{0,100}/gi) || [];
  const num104 = result.body.includes('104');
  const num772 = result.body.includes('772');
  
  console.log('Contains "104":', num104);
  console.log('Contains "772":', num772);
  console.log('\nRoute references:', routeRefs.slice(0, 5));
  console.log('Line references:', lineRefs.slice(0, 5));
  
  // Save for inspection
  fs.writeFileSync('scripts/station_7225.html', result.body);
  console.log('\nSaved to station_7225.html');
  
  // Show relevant section
  const idx104 = result.body.indexOf('104');
  if (idx104 > 0) {
    console.log('\nContext around "104":', result.body.substring(idx104-200, idx104+300));
  }
}

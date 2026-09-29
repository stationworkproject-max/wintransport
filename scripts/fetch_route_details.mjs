/**
 * Fetch ligne_details.php?route_id=772 to get Bus 104's actual stops
 * Also probe backend/api/bus_routes.php
 */
import fs from 'fs';

const headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' };

// Fetch the per-route detail page
const res = await fetch('https://tunismapper.com/ligne_details.php?route_id=772', { headers });
console.log(`ligne_details.php?route_id=772 → ${res.status}, ${res.headers.get('content-type')}`);
const html = await res.text();
console.log(`Size: ${html.length} bytes`);
fs.writeFileSync('scripts/ligne_details_route772.html', html);

// Extract stops from this page
const scriptBlocks = html.match(/<script[^>]*>([\s\S]*?)<\/script>/g) || [];
console.log(`Script blocks: ${scriptBlocks.length}`);
scriptBlocks.forEach((s, i) => {
  const inner = s.replace(/<script[^>]*>/, '').trim();
  if (inner.length > 500) {
    console.log(`\nScript ${i} (${inner.length} chars):`);
    console.log(inner.substring(0, 1500));
    console.log('---END---');
  }
});

// Look for stop IDs
const stopIds = html.match(/stop_id[^"'\d]*(\d+)/g) || [];
const coords = html.match(/[\d.]{6,}\s*,\s*[\d.]{6,}/g) || [];
console.log('\nStop IDs:', stopIds.slice(0, 10));
console.log('Coords:', coords.slice(0, 10));

// Also test the bus_routes API
console.log('\n\n--- Testing bus_routes.php API ---');
const apiRes = await fetch('https://tunismapper.com/backend/api/bus_routes.php?limit=5&offset=0&q=104', { headers });
console.log(`bus_routes API → ${apiRes.status}`);
if (apiRes.status === 200) {
  const apiData = await apiRes.json();
  console.log('Response:', JSON.stringify(apiData, null, 2).substring(0, 500));
}

// Test without search to see all
const apiRes2 = await fetch('https://tunismapper.com/backend/api/bus_routes.php?limit=5&offset=0&q=', { headers });
console.log(`bus_routes API (all) → ${apiRes2.status}`);
if (apiRes2.status === 200) {
  const data = await apiRes2.json();
  console.log('Total:', data.total);
  console.log('Data sample:', JSON.stringify(data.data?.[0], null, 2));
}

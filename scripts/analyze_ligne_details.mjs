/**
 * Deep analyze ligne_details.php?id=772 
 */
import fs from 'fs';

const html = fs.readFileSync('scripts/ligne_details_772.html', 'utf8');
console.log(`Total size: ${html.length} bytes`);

// Find script blocks
const scripts = html.match(/<script[^>]*>([\s\S]*?)<\/script>/g) || [];
console.log(`Script blocks: ${scripts.length}`);

scripts.forEach((s, i) => {
  const inner = s.replace(/<script[^>]*>/, '').trim();
  if (inner.length > 200) {
    console.log(`\nScript ${i} (${inner.length} chars):`);
    console.log(inner.substring(0, 800));
    console.log('---');
  }
});

// Find the route trace (polyline) data
const polyline = html.match(/polyline[\s\S]{0,500}/i);
if (polyline) console.log('\nPolyline reference:', polyline[0]);

// Look for L.polyline calls
const lPolyline = html.match(/L\.polyline\([\s\S]{0,300}/);
if (lPolyline) console.log('\nLeaflet polyline:', lPolyline[0]);

// Look for stop markers
const lMarker = html.match(/L\.marker[\s\S]{0,200}/);
if (lMarker) console.log('\nLeaflet marker:', lMarker[0]);

// Look for arrays with coordinates
const coordArrays = html.match(/\[\s*\[?\s*3[56]\.\d+\s*,\s*1[01]\.\d+\s*\]?\s*[,\]]/g) || [];
console.log('\nCoordinate pairs:', coordArrays.slice(0, 10));

// Extract text content (stop names)
const textContent = html.replace(/<[^>]+>/g, '\n').replace(/\s+/g, ' ').trim();
const stopSections = textContent.match(/(?:arrêt|station|stop)[^.]{0,200}/gi) || [];
console.log('\nStop text references:', stopSections.slice(0, 5));

// Show middle portion of HTML
console.log('\n\nMiddle of HTML (around position 30000-33000):');
console.log(html.substring(30000, 33000));

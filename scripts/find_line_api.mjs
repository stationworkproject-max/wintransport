/**
 * Find the correct URL pattern for per-line stop data
 * and discover the API that ligne_details calls to load bus lines
 */
import fs from 'fs';

// Look at the Script 7 more carefully - it loads bus lines via AJAX
const html = fs.readFileSync('scripts/ligne_details_772.html', 'utf8');
const scripts = html.match(/<script[^>]*>([\s\S]*?)<\/script>/g) || [];
const script7 = scripts[7];
console.log('FULL SCRIPT 7:');
console.log(script7.replace(/<script[^>]*>/, '').substring(0, 5000));

// Also check the JSON-LD schema which listed 235 lines with their URLs
const jsonLd = scripts[0].replace(/<script[^>]*>/, '').replace(/<\/script>/, '');
try {
  const schema = JSON.parse(jsonLd);
  const items = schema['@graph']?.[0]?.potentialAction || schema['@graph'];
  // Find itemListElement
  const graph = schema['@graph'];
  for (const item of (graph || [])) {
    if (item['@type'] === 'ItemList') {
      console.log('\nItemList found with', item.numberOfItems, 'items');
      // Show first 5 items
      const elems = item.itemListElement || [];
      console.log('First 5 items:', JSON.stringify(elems.slice(0, 5), null, 2));
      console.log('...');
      console.log('Bus 104 items:', elems.filter(e => JSON.stringify(e).includes('104')).slice(0, 3));
      break;
    }
  }
} catch (e) {
  console.log('JSON-LD parse error:', e.message);
  console.log('Raw JSON-LD:', jsonLd.substring(0, 500));
}

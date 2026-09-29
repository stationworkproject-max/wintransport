/**
 * Parse tunismapper itineraire.php?route=772 to extract ordered stop list
 */
import fs from 'fs';

async function fetchAndParse(routeId) {
  const headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' };
  
  // Fetch itineraire page
  const res = await fetch(`https://tunismapper.com/itineraire.php?route=${routeId}`, { 
    headers, signal: AbortSignal.timeout(15000) 
  });
  const html = await res.text();
  console.log(`itineraire.php?route=${routeId} → ${res.status}, ${html.length} bytes`);
  
  fs.writeFileSync(`scripts/itineraire_${routeId}.html`, html);
  
  // Also fetch ligne_details
  const res2 = await fetch(`https://tunismapper.com/ligne_details.php?id=${routeId}`, { 
    headers, signal: AbortSignal.timeout(15000) 
  });
  const html2 = await res2.text();
  console.log(`ligne_details.php?id=${routeId} → ${res2.status}, ${html2.length} bytes`);
  fs.writeFileSync(`scripts/ligne_details_${routeId}.html`, html2);

  // Now parse the itineraire page for stop data
  console.log('\n--- ITINERAIRE PAGE ---');
  
  // Look for script variables
  const scriptMatches = html.match(/<script[^>]*>([\s\S]*?)<\/script>/g) || [];
  console.log(`Script blocks: ${scriptMatches.length}`);
  scriptMatches.forEach((s, i) => {
    const inner = s.replace(/<script[^>]*>/, '').trim();
    if (inner.length > 100) {
      console.log(`\nScript ${i} (${inner.length} chars):`);
      console.log(inner.substring(0, 500));
    }
  });
  
  // Look for stop data in HTML
  const stopIds = html.match(/stop_id[^}]*}/g) || [];
  const coords = html.match(/\d+\.\d{4,}\s*,\s*\d+\.\d{4,}/g) || [];
  const jsonBlocks = html.match(/\{[^{}]*lat[^{}]*lon[^{}]*\}/g) || [];
  
  console.log('\nStop id refs:', stopIds.slice(0, 5));
  console.log('Coords found:', coords.slice(0, 5));
  console.log('JSON with lat/lon:', jsonBlocks.slice(0, 3));
  
  // Look for ordered list items
  const listItems = html.match(/<li[^>]*>[^<]{10,100}<\/li>/g) || [];
  console.log('\nList items (stops?):', listItems.slice(0, 10));
  
  // Look for table rows
  const tableRows = html.match(/<tr[^>]*>[\s\S]*?<\/tr>/g) || [];
  console.log('\nTable rows:', tableRows.slice(0, 5).map(r => r.replace(/<[^>]+>/g, ' ').trim().substring(0, 100)));

  console.log('\n--- LIGNE DETAILS PAGE ---');
  const listItems2 = html2.match(/<li[^>]*>[^<]{10,200}<\/li>/g) || [];
  console.log('List items:', listItems2.slice(0, 10));
  const stopIds2 = html2.match(/stop_id[^}]*}/g) || [];
  console.log('Stop ids:', stopIds2.slice(0, 5));
  
  // Look for ordered stop sequence
  const orderedStops = html2.match(/(?:order|sequence|seq|position|pos)[^\d]*(\d+)[^}]*stop[^}]*/gi) || [];
  console.log('Ordered stops:', orderedStops.slice(0, 5));
}

await fetchAndParse('772').catch(console.error);

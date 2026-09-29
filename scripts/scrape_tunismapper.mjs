/**
 * Scrape tunismapper.com for a specific bus route page and extract stop data
 * The site seems to embed JSON data in the HTML or uses inline scripts
 */
async function scrapePage(routeId) {
  const headers = { 
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0',
    'Accept': 'text/html,application/xhtml+xml'
  };
  
  // Try different URL patterns the site might use
  const urlsToTry = [
    `https://tunismapper.com/route/${routeId}`,
    `https://tunismapper.com/ligne/${routeId}`,
    `https://tunismapper.com/bus/${routeId}`,
    `https://tunismapper.com/lignes/${routeId}`,
    `https://tunismapper.com/?route=${routeId}`,
    `https://tunismapper.com/?line=${routeId}`,
    `https://tunismapper.com/?ligne=${routeId}`,
  ];
  
  for (const url of urlsToTry) {
    const res = await fetch(url, { headers });
    if (res.status === 200) {
      const html = await res.text();
      console.log(`\n✓ Found at: ${url} (${html.length} bytes)`);
      
      // Look for stop data patterns: lat/lon arrays, JSON objects with coordinates
      const jsonBlocks = html.match(/\{[^{}]*"lat":[^{}]*"lon":[^{}]*\}/g) || [];
      const coordArrays = html.match(/\[\s*[\d.]+\s*,\s*[\d.]+\s*\]/g) || [];
      const stops = html.match(/stop_id[^}]+}/gi) || [];
      
      console.log(`  JSON blocks with lat/lon: ${jsonBlocks.length}`);
      console.log(`  Coord arrays: ${coordArrays.length}`);
      console.log(`  Stop references: ${stops.length}`);
      
      if (jsonBlocks.length > 0) {
        console.log('\n  First 3 stop blocks:');
        jsonBlocks.slice(0, 3).forEach(b => console.log(' ', b));
      }
      
      // Look for JavaScript variable assignments with route data
      const varMatches = html.match(/var\s+\w+\s*=\s*(\[[\s\S]{20,5000}?\])/g) || [];
      const letMatches = html.match(/(?:let|const)\s+\w+\s*=\s*(\[[\s\S]{20,5000}?\])/g) || [];
      console.log(`\n  JS var assignments: ${varMatches.length}`);
      console.log(`  JS let/const assignments: ${letMatches.length}`);
      
      // Check for AJAX/fetch calls
      const fetchCalls = html.match(/fetch\(['"](https?:\/\/[^'"]+)['"]/g) || [];
      const ajaxUrls = html.match(/(?:url|href)\s*:\s*['"](\/[^'"]+)['"]/g) || [];
      console.log(`\n  Fetch calls: ${fetchCalls}`);
      console.log(`  AJAX URLs: ${ajaxUrls.slice(0, 5)}`);
      
      // Save the full HTML for inspection
      const fs = (await import('fs')).default;
      fs.writeFileSync(`scripts/tunismapper_route${routeId}.html`, html);
      console.log(`\n  Saved full HTML to scripts/tunismapper_route${routeId}.html`);
      return;
    }
  }
  
  console.log('All URL patterns returned non-200. Trying main page with route param...');
  
  // Main page
  const mainRes = await fetch('https://tunismapper.com', { headers });
  const mainHtml = await mainRes.text();
  const fs = (await import('fs')).default;
  fs.writeFileSync('scripts/tunismapper_main.html', mainHtml);
  console.log(`Saved main page (${mainHtml.length} bytes) to scripts/tunismapper_main.html`);
}

scrapePage('772').catch(console.error);

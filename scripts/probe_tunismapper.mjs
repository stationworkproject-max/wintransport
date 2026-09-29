/**
 * Discover tunismapper.com API endpoints by scraping the page HTML and JS
 */
async function main() {
  const headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' };
  
  // Fetch main page
  const res = await fetch('https://tunismapper.com', { headers });
  const html = await res.text();
  
  // Find JS bundle files  
  const jsMatches = html.match(/src="([^"]*\.js[^"]*)"/g) || [];
  console.log('JS files found:', jsMatches.slice(0, 10));
  
  // Try fetching a bus route page directly
  const routeRes = await fetch('https://tunismapper.com/lines/772', { headers });
  console.log('\nRoute page /lines/772 status:', routeRes.status);
  
  const routeRes2 = await fetch('https://tunismapper.com/bus/772', { headers });
  console.log('Route page /bus/772 status:', routeRes2.status);
  
  // Try GraphQL
  const gqlRes = await fetch('https://tunismapper.com/graphql', { 
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: '{ __typename }' })
  });
  console.log('\nGraphQL status:', gqlRes.status);
  
  // Try GTFS-like endpoints
  const gtfsTests = [
    'https://tunismapper.com/gtfs/stops.txt',
    'https://tunismapper.com/gtfs/routes.txt', 
    'https://tunismapper.com/data/routes.json',
    'https://tunismapper.com/api/gtfs/772',
    'https://api.tunismapper.com/routes/772',
    'https://api.tunismapper.com/v1/routes/772',
  ];
  
  for (const url of gtfsTests) {
    const r = await fetch(url, { headers });
    console.log(`[${r.status}] ${url}`);
    if (r.status === 200) {
      const body = await r.text();
      console.log('  BODY:', body.substring(0, 200));
    }
  }
  
  // Look for API base in HTML
  const apiRefs = (html.match(/https?:\/\/[^"'\s,)>]+/g) || [])
    .filter(u => u.includes('api') || u.includes('data') || u.includes('transport'));
  console.log('\nAPI-like URLs in HTML:', [...new Set(apiRefs)].slice(0, 20));
}

main().catch(console.error);

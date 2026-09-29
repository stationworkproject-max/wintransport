/**
 * Find the tunismapper page that shows stops for a specific route/line
 * station_details.php shows lines PER stop. 
 * We need the reverse: stops per line.
 */
import fs from 'fs';

async function tryRoutePages(routeNum) {
  const headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' };
  
  const urls = [
    `https://tunismapper.com/ligne_details.php?id=772`,
    `https://tunismapper.com/route_details.php?id=772`,
    `https://tunismapper.com/line_details.php?id=772`,
    `https://tunismapper.com/horaires.php?route=772`,
    `https://tunismapper.com/horaires_ligne.php?id=772`,
    `https://tunismapper.com/timetable.php?route=772`,
    `https://tunismapper.com/itineraire.php?route=772`,
    `https://tunismapper.com/itineraire.php?id=772`,
    `https://tunismapper.com/?ligne=104`,
    `https://tunismapper.com/?line=104`,
    `https://tunismapper.com/bus-104`,
    `https://tunismapper.com/bus/104`,
    `https://tunismapper.com/lignes/104`,
    `https://tunismapper.com/backend/api/getLine.php?num=104`,
    `https://tunismapper.com/backend/api/getLine.php?name=104`,
    `https://tunismapper.com/backend/api/ligne.php?num=104`,
    `https://tunismapper.com/backend/api/horaires.php?ligne=104`,
    `https://tunismapper.com/backend/api/line_stops.php?line=104`,
    `https://tunismapper.com/backend/api/getRouteByName.php?name=104`,
  ];
  
  for (const url of urls) {
    try {
      const res = await fetch(url, { headers, signal: AbortSignal.timeout(8000) });
      console.log(`[${res.status}] ${url}`);
      if (res.status === 200) {
        const body = await res.text();
        console.log(`  → ${body.length} bytes, contains "104": ${body.includes('104')}, contains "7225": ${body.includes('7225')}`);
        if (body.includes('7225') || (body.includes('104') && body.length > 10000)) {
          console.log('  POTENTIALLY USEFUL! Saving...');
          fs.writeFileSync(`scripts/route_page_${url.split('/').pop().split('?')[0]}.html`, body);
        }
      }
    } catch (e) {
      console.log(`[ERR] ${url}: ${e.message.substring(0, 50)}`);
    }
    await new Promise(r => setTimeout(r, 200));
  }
}

await tryRoutePages('772').catch(console.error);

// Also parse station_details html to understand the line→stop mapping stored in it
const stationHtml = fs.readFileSync('scripts/station_7225.html', 'utf8');

// Find the routes listed for this station
const linesSection = stationHtml.match(/Lignes[^:]*:([\s\S]*?)(?:<\/|Horaires)/i);
console.log('\n\nLines for station 7225:', linesSection?.[0].substring(0, 200));

// Find stop list structure
const stopListMatch = stationHtml.match(/itinéraire[\s\S]{0,3000}/i);
if (stopListMatch) console.log('\nItinerary section:', stopListMatch[0].substring(0, 500));

// Look for embedded stop data
const embeddedStops = stationHtml.match(/stop_id.*?(?=\n)/g) || [];
console.log('\nEmbedded stop refs:', embeddedStops.slice(0, 5));

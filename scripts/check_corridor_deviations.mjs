import { STATIC_LINES } from '../src/data/staticTransit.js';

function getDist(lat1, lon1, lat2, lon2) {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

console.log('Checking all 190 bus lines for any stop with distance > 3km to its neighbors...');

const suspicious = [];

for (const line of STATIC_LINES) {
  if (line.type_id !== 'bus') continue;
  const stops = line.stops;
  if (!stops || stops.length < 2) continue;

  for (let i = 0; i < stops.length; i++) {
    const s = stops[i];
    const prev = i > 0 ? stops[i-1] : null;
    const next = i < stops.length - 1 ? stops[i+1] : null;

    const dPrev = prev ? getDist(prev.lat, prev.lon, s.lat, s.lon) : 0;
    const dNext = next ? getDist(s.lat, s.lon, next.lat, next.lon) : 0;

    // In an urban bus route, consecutive stops are usually 200m - 800m.
    // Any consecutive distance > 3.0km is suspicious in Greater Tunis.
    // If BOTH dPrev and dNext are > 2.5km, that's an isolated spike!
    if (prev && next && dPrev > 2.5 && dNext > 2.5) {
      suspicious.push({
        line: line.short_name,
        id: line.id,
        stopIndex: i + 1,
        stopName: s.name,
        lat: s.lat,
        lon: s.lon,
        dPrev: dPrev.toFixed(1) + 'km',
        dNext: dNext.toFixed(1) + 'km',
        prevName: prev.name,
        nextName: next.name
      });
    }
  }
}

console.log(`Found ${suspicious.length} suspicious spike stops:`);
suspicious.forEach(s => console.log(JSON.stringify(s)));

import fs from 'fs';
import { STATIC_LINES } from '../src/data/staticTransit.js';

function getDistance(p1, p2) {
  const R = 6371000;
  const dLat = (p2[0] - p1[0]) * Math.PI / 180;
  const dLon = (p2[1] - p1[1]) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(p1[0] * Math.PI / 180) * Math.cos(p2[0] * Math.PI / 180) *
            Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function decimate(points, minDistanceMeters = 20) {
  if (!points || points.length <= 2) return points;
  const result = [points[0]];
  let lastPt = points[0];
  for (let i = 1; i < points.length - 1; i++) {
    const pt = points[i];
    if (getDistance(lastPt, pt) >= minDistanceMeters) {
      result.push(pt);
      lastPt = pt;
    }
  }
  result.push(points[points.length - 1]);
  return result;
}

async function routeLine(stops) {
  const allPoints = [];
  const chunkSize = 25;
  for (let start = 0; start < stops.length - 1; start += chunkSize - 1) {
    const end = Math.min(start + chunkSize, stops.length);
    const chunkStops = stops.slice(start, end);
    const coordsStr = chunkStops.map(s => `${s.lon.toFixed(6)},${s.lat.toFixed(6)}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/driving/${coordsStr}?overview=full&geometries=geojson`;

    try {
      const res = await fetch(url, { headers: { 'User-Agent': 'WhereAmI-Transit/1.0' } });
      const data = await res.json();
      if (data.code === 'Ok' && data.routes && data.routes[0]) {
        const pts = data.routes[0].geometry.coordinates.map(c => [
          parseFloat(c[1].toFixed(5)),
          parseFloat(c[0].toFixed(5))
        ]);
        if (allPoints.length > 0 && pts.length > 0) {
          pts.shift();
        }
        allPoints.push(...pts);
      } else {
        chunkStops.forEach(s => allPoints.push([s.lat, s.lon]));
      }
    } catch (e) {
      chunkStops.forEach(s => allPoints.push([s.lat, s.lon]));
    }
    await new Promise(r => setTimeout(r, 80));
  }
  return decimate(allPoints, 20);
}

async function main() {
  console.log('=== STARTING NETWORK DATA CORRECTION ===');

  const affectedLineIds = new Set();

  // 1. Fix Bus 104 (bus_772): Move Gouvernorat Manouba from stop 7 to stop 22 in Manouba
  const b104 = STATIC_LINES.find(l => l.id === 'bus_772');
  if (b104) {
    const gouvIdx = b104.stops.findIndex(s => s.name.includes('Gouvernorat'));
    if (gouvIdx !== -1 && gouvIdx < 10) {
      const [gouvStop] = b104.stops.splice(gouvIdx, 1);
      const jazzarIdx = b104.stops.findIndex(s => s.name.includes('Jazzar'));
      if (jazzarIdx !== -1) {
        b104.stops.splice(jazzarIdx + 1, 0, gouvStop);
        console.log('✓ Fixed Bus 104: relocated Gouvernorat Manouba to Manouba city center');
        affectedLineIds.add('bus_772');
      }
    }
  }

  // 2. Network-wide outlier jump cleaner
  STATIC_LINES.forEach(line => {
    if (!line.stops || line.stops.length < 3) return;
    let changed = true;
    while (changed) {
      changed = false;
      for (let i = 1; i < line.stops.length - 1; i++) {
        const prev = [line.stops[i - 1].lat, line.stops[i - 1].lon];
        const curr = [line.stops[i].lat, line.stops[i].lon];
        const next = [line.stops[i + 1].lat, line.stops[i + 1].lon];

        const dPrev = getDistance(prev, curr);
        const dNext = getDistance(curr, next);
        const dDirect = getDistance(prev, next);

        if (dPrev > 2500 && dNext > 2500 && dDirect < 2000) {
          console.log(`✓ Removed outlier stop in ${line.id} (${line.short_name}): "${line.stops[i].name}" (Jump: ${(dPrev/1000).toFixed(1)} km)`);
          line.stops.splice(i, 1);
          affectedLineIds.add(line.id);
          changed = true;
          break;
        }
      }
    }
  });

  console.log(`Total affected lines needing shape re-routing: ${affectedLineIds.size}`);

  // 3. Re-save src/data/staticTransit.js with clean stop data
  const staticTransitContent = `// Static Transit Data for Tunisia (GTFS & Transtu official network)
export const TRANSIT_NETWORKS = [
  { id: 'all', name: 'Tous les réseaux', color: '#3b82f6' },
  { id: 'metro', name: 'Métro Léger', color: '#10b981' },
  { id: 'tgm', name: 'TGM', color: '#0ea5e9' },
  { id: 'rfr', name: 'RFR Rapide', color: '#8b5cf6' },
  { id: 'train', name: 'Train SNCFT', color: '#f59e0b' },
  { id: 'bus', name: 'Bus Transtu (190 Lignes)', color: '#ec4899' },
];

export const STATIC_LINES = ${JSON.stringify(STATIC_LINES, null, 2)};
`;
  fs.writeFileSync('src/data/staticTransit.js', staticTransitContent, 'utf8');
  console.log('Saved cleaned staticTransit.js successfully!');

  // 4. Re-route shapes for affected lines in src/data/transitShapes.json
  const shapes = JSON.parse(fs.readFileSync('src/data/transitShapes.json', 'utf8'));
  for (const lineId of affectedLineIds) {
    const line = STATIC_LINES.find(l => l.id === lineId);
    if (line && line.stops.length >= 2) {
      console.log(`Re-routing shape for ${line.id} (${line.short_name}: ${line.long_name})...`);
      const newShape = await routeLine(line.stops);
      shapes[lineId] = newShape;
      console.log(`-> Got ${newShape.length} points for ${line.short_name}!`);
    }
  }

  fs.writeFileSync('src/data/transitShapes.json', JSON.stringify(shapes));
  console.log('Updated transitShapes.json successfully!');
}

main();

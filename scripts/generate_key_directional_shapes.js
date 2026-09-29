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

function decimate(points, minDistanceMeters = 15) {
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

async function routeStops(stops) {
  const allPoints = [];
  const chunkSize = 15;
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
    await new Promise(r => setTimeout(r, 150));
  }
  return decimate(allPoints, 15);
}

async function main() {
  console.log('=== GENERATING DIRECTIONAL SHAPES FOR KEY BUS LINES ===');
  const targetLines = ['bus_772', 'bus_773', 'bus_707', 'bus_727', 'bus_736', 'bus_737', 'bus_746', 'bus_748', 'bus_760', 'bus_761', 'bus_856', 'bus_875'];
  const shapes = JSON.parse(fs.readFileSync('src/data/transitShapes.json', 'utf8'));

  for (const lineId of targetLines) {
    const line = STATIC_LINES.find(l => l.id === lineId);
    if (!line || !line.stops || line.stops.length < 2) continue;

    console.log(`Processing ${line.short_name} (${line.long_name}) [${line.stops.length} stops]...`);
    
    // Aller
    if (!shapes[`${lineId}_0`]) {
      const s0 = await routeStops(line.stops);
      shapes[`${lineId}_0`] = s0;
      shapes[lineId] = s0;
      console.log(`  -> Aller: ${s0.length} pts`);
    }

    // Retour
    if (!shapes[`${lineId}_1`]) {
      const s1 = await routeStops([...line.stops].reverse());
      shapes[`${lineId}_1`] = s1;
      console.log(`  -> Retour: ${s1.length} pts`);
    }
  }

  fs.writeFileSync('src/data/transitShapes.json', JSON.stringify(shapes));
  console.log('All targeted directional shapes successfully saved to transitShapes.json!');
}

main();

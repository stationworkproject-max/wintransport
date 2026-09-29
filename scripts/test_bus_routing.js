import fs from 'fs';
import { STATIC_LINES } from '../src/data/staticTransit.js';

// Distance between two points in meters
function getDistance(p1, p2) {
  const R = 6371000;
  const dLat = (p2[0] - p1[0]) * Math.PI / 180;
  const dLon = (p2[1] - p1[1]) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(p1[0] * Math.PI / 180) * Math.cos(p2[0] * Math.PI / 180) *
            Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// Decimate polyline: keep point if distance from last kept point > minDistanceMeters
function decimate(points, minDistanceMeters = 18) {
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

async function routeLine(line) {
  if (!line.stops || line.stops.length < 2) {
    return null;
  }

  const allPoints = [];
  const chunkSize = 25; // max stops per OSRM call
  
  for (let start = 0; start < line.stops.length - 1; start += chunkSize - 1) {
    const end = Math.min(start + chunkSize, line.stops.length);
    const chunkStops = line.stops.slice(start, end);
    const coordsStr = chunkStops.map(s => `${s.lon.toFixed(6)},${s.lat.toFixed(6)}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/driving/${coordsStr}?overview=full&geometries=geojson`;

    try {
      const res = await fetch(url, { headers: { 'User-Agent': 'WhereAmI-Transit-App/1.0' } });
      const data = await res.json();
      if (data.code === 'Ok' && data.routes && data.routes[0]) {
        // GeoJSON is [lon, lat], Leaflet is [lat, lon]
        const pts = data.routes[0].geometry.coordinates.map(c => [
          parseFloat(c[1].toFixed(5)),
          parseFloat(c[0].toFixed(5))
        ]);
        if (allPoints.length > 0 && pts.length > 0) {
          // Remove duplicate stitch point
          pts.shift();
        }
        allPoints.push(...pts);
      } else {
        console.warn(`[WARN] OSRM returned code ${data.code} for chunk of ${line.id}`);
        // Fallback to straight segments for this chunk
        chunkStops.forEach(s => allPoints.push([s.lat, s.lon]));
      }
    } catch (e) {
      console.warn(`[ERR] Fetch failed for ${line.id}: ${e.message}`);
      chunkStops.forEach(s => allPoints.push([s.lat, s.lon]));
    }

    // Small delay between requests to be polite
    await new Promise(r => setTimeout(r, 120));
  }

  return decimate(allPoints, 18);
}

async function runTest() {
  const buses = STATIC_LINES.filter(l => l.type_id === 'bus');
  console.log(`Testing first 5 buses...`);
  for (let i = 0; i < 5; i++) {
    const line = buses[i];
    console.log(`Processing ${line.id} (${line.short_name}: ${line.long_name}) with ${line.stops.length} stops...`);
    const shape = await routeLine(line);
    console.log(`-> Got ${shape ? shape.length : 0} road points!`);
  }
}

runTest();

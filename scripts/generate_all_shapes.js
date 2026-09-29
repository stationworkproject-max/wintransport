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

// Decimate polyline: keep point if distance from last kept point >= minDistanceMeters
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

async function routeBusLine(line) {
  if (!line.stops || line.stops.length < 2) {
    return { shape: null, status: 'missing_stops' };
  }

  const allPoints = [];
  const chunkSize = 25; // max stops per OSRM call
  let hasFailedChunk = false;

  for (let start = 0; start < line.stops.length - 1; start += chunkSize - 1) {
    const end = Math.min(start + chunkSize, line.stops.length);
    const chunkStops = line.stops.slice(start, end);
    const coordsStr = chunkStops.map(s => `${s.lon.toFixed(6)},${s.lat.toFixed(6)}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/driving/${coordsStr}?overview=full&geometries=geojson`;

    try {
      const res = await fetch(url, { headers: { 'User-Agent': 'WhereAmI-Transit-App/1.0' } });
      const data = await res.json();
      if (data.code === 'Ok' && data.routes && data.routes[0]) {
        // GeoJSON [lon, lat] -> Leaflet [lat, lon]
        const pts = data.routes[0].geometry.coordinates.map(c => [
          parseFloat(c[1].toFixed(5)),
          parseFloat(c[0].toFixed(5))
        ]);
        if (allPoints.length > 0 && pts.length > 0) {
          pts.shift(); // remove duplicate boundary vertex
        }
        allPoints.push(...pts);
      } else {
        hasFailedChunk = true;
        chunkStops.forEach(s => allPoints.push([s.lat, s.lon]));
      }
    } catch (e) {
      hasFailedChunk = true;
      chunkStops.forEach(s => allPoints.push([s.lat, s.lon]));
    }

    // Rate-limit safety: 80ms delay
    await new Promise(r => setTimeout(r, 80));
  }

  const finalPts = decimate(allPoints, 20);
  return {
    shape: finalPts,
    status: hasFailedChunk ? 'partial_fallback' : 'exact_road'
  };
}

async function fetchTunismapperTrain(routeId) {
  try {
    const url = `https://www.tunismapper.com/ligne_details.php?route_id=${routeId}`;
    const res = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
    const text = await res.text();
    const match = text.match(/var shapes\s*=\s*(\[[\s\S]*?\]);/);
    if (match) {
      const raw = JSON.parse(match[1]);
      if (raw && raw[0] && raw[0].length > 0) {
        const rawPts = raw[0].map(p => [parseFloat(p.shape_pt_lat), parseFloat(p.shape_pt_lon)]);
        // Decimate to ~25m
        return decimate(rawPts, 25);
      }
    }
  } catch (e) {
    console.error(`Tunismapper fetch error for route ${routeId}:`, e.message);
  }
  return null;
}

async function main() {
  console.log('=== STARTING TRANSIT SHAPE COMPILATION ===');
  
  // 1. Load existing rail shapes (Metros 1-6, TGM, RFR A/D/E)
  let existingShapes = {};
  if (fs.existsSync('src/data/transitShapes.json')) {
    existingShapes = JSON.parse(fs.readFileSync('src/data/transitShapes.json', 'utf8'));
  }

  const newShapes = { ...existingShapes };
  const report = {
    exact_rail: [],
    exact_bus: [],
    partial_bus: [],
    missing_trace: []
  };

  // Add existing rail lines to report
  ['metro_50', 'metro_51', 'metro_52', 'metro_53', 'metro_54', 'metro_55', 'metro_56', 'rfr_19', 'rfr_46', 'rfr_47'].forEach(id => {
    if (newShapes[id]) {
      const l = STATIC_LINES.find(line => line.id === id);
      report.exact_rail.push({
        id,
        name: l ? `${l.short_name} (${l.long_name})` : id,
        points: newShapes[id].length,
        source: 'OSM High-Definition Geometry'
      });
    }
  });

  // 2. Fetch SNCFT Train lines from Tunismapper
  const trains = STATIC_LINES.filter(l => l.type_id === 'train');
  console.log(`\nFetching ${trains.length} Train lines...`);
  
  for (const t of trains) {
    if (newShapes[t.id] && newShapes[t.id].length > 10) {
      console.log(`Train ${t.id} already has ${newShapes[t.id].length} points.`);
      report.exact_rail.push({
        id: t.id,
        name: `${t.short_name} (${t.long_name})`,
        points: newShapes[t.id].length,
        source: 'Tunismapper Railway Shape'
      });
      continue;
    }

    const pts = await fetchTunismapperTrain(t.route_id);
    if (pts && pts.length > 5) {
      newShapes[t.id] = pts;
      console.log(`[TRAIN OK] ${t.id} (${t.long_name}): ${pts.length} points`);
      report.exact_rail.push({
        id: t.id,
        name: `${t.short_name} (${t.long_name})`,
        points: pts.length,
        source: 'Tunismapper Railway Shape'
      });
    } else {
      console.log(`[TRAIN NO SHAPE] ${t.id} (${t.long_name})`);
      report.missing_trace.push({
        id: t.id,
        type: 'train',
        name: `${t.short_name} (${t.long_name})`,
        stopsCount: t.stops.length,
        reason: 'No rail geometry in Tunismapper database for route ' + t.route_id
      });
    }
    await new Promise(r => setTimeout(r, 100));
  }

  // 3. Process all 190 Bus lines via OSRM
  const buses = STATIC_LINES.filter(l => l.type_id === 'bus');
  console.log(`\nProcessing ${buses.length} Bus lines with OSRM road geometry...`);

  let busDone = 0;
  for (const b of buses) {
    busDone++;
    const res = await routeBusLine(b);
    if (res.shape && res.shape.length >= 2) {
      newShapes[b.id] = res.shape;
      if (res.status === 'exact_road') {
        report.exact_bus.push({
          id: b.id,
          short_name: b.short_name,
          long_name: b.long_name,
          stops: b.stops.length,
          points: res.shape.length
        });
      } else {
        report.partial_bus.push({
          id: b.id,
          short_name: b.short_name,
          long_name: b.long_name,
          stops: b.stops.length,
          points: res.shape.length
        });
      }
    } else {
      report.missing_trace.push({
        id: b.id,
        type: 'bus',
        name: `Bus ${b.short_name} (${b.long_name})`,
        stopsCount: b.stops ? b.stops.length : 0,
        reason: res.status === 'missing_stops' ? '0 stops defined in Transtu static GTFS' : 'OSM/OSRM routing failed'
      });
    }

    if (busDone % 10 === 0 || busDone === buses.length) {
      console.log(`Progress: ${busDone}/${buses.length} buses processed... (Current: ${b.short_name})`);
    }
  }

  // 4. Save results to src/data/transitShapes.json
  fs.writeFileSync('src/data/transitShapes.json', JSON.stringify(newShapes));
  console.log(`\n=== COMPILATION COMPLETE ===`);
  console.log(`Saved ${Object.keys(newShapes).length} total line shapes to src/data/transitShapes.json!`);

  // 5. Save report to scripts/transit_shapes_report.json
  fs.writeFileSync('scripts/transit_shapes_report.json', JSON.stringify(report, null, 2));
  console.log(`Saved detailed report to scripts/transit_shapes_report.json`);
}

main();

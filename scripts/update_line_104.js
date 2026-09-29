import fs from 'fs';
import { STATIC_LINES, TRANSIT_NETWORKS } from '../src/data/staticTransit.js';

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
      console.warn('OSRM error, falling back to straight segment:', e.message);
      chunkStops.forEach(s => allPoints.push([s.lat, s.lon]));
    }
    await new Promise(r => setTimeout(r, 200));
  }
  return decimate(allPoints, 15);
}

async function main() {
  console.log('=== UPDATING LINE 104 STOPS AND DIRECTIONAL SHAPES ===');

  const b104 = STATIC_LINES.find(l => l.id === 'bus_772');
  if (!b104) {
    console.error('Line bus_772 not found!');
    return;
  }

  // 1. Cleaned stops: Remove Bouchoucha/Errabta, add Boulevard 20 Mars & Bab Saadoun & 9 Avril
  const cleanedStops = [
    { id: 'st-7225', stop_id: 7225, name: 'Terminus Tunis Marine Bus', lat: 36.8003841, lon: 10.1903877, horaires_count: 26 },
    { id: 'st-7436', stop_id: 7436, name: 'Rue De La Turquie', lat: 36.7991033, lon: 10.1863693, horaires_count: 26 },
    { id: 'st-7363', stop_id: 7363, name: 'Moncef Bey', lat: 36.7929436, lon: 10.1856283, horaires_count: 26 },
    { id: 'st-7235', stop_id: 7235, name: 'Hopital Militaire', lat: 36.7856137, lon: 10.1799054, horaires_count: 26 },
    { id: 'st-7841', stop_id: 7841, name: 'Hopital Habib Thameur', lat: 36.784376, lon: 10.1758234, horaires_count: 26 },
    { id: 'st-7391', stop_id: 7391, name: 'Gorjani', lat: 36.7879938, lon: 10.1675136, horaires_count: 26 },
    { id: 'st-7392', stop_id: 7392, name: 'Arret Essayda', lat: 36.7852839, lon: 10.1711724, horaires_count: 26 },
    { id: 'st-7802', stop_id: 7802, name: 'Mosquée Al Hawa', lat: 36.7931059, lon: 10.1629207, horaires_count: 26 },
    // RFR Line D Deviation: Boulevard du 9 Avril -> Bab Saadoun -> Boulevard 20 Mars (Bardo)
    { id: 'st-dev-9avril', stop_id: 9901, name: 'Boulevard 9 Avril', lat: 36.8015, lon: 10.1650, horaires_count: 26 },
    { id: 'st-dev-babsaadoun', stop_id: 9902, name: 'Place Bab Saadoun', lat: 36.8105, lon: 10.1593, horaires_count: 26 },
    { id: 'st-dev-20mars', stop_id: 9903, name: 'Boulevard 20 Mars - Bardo', lat: 36.8095, lon: 10.1472, horaires_count: 26 },
    // Continuation through Bardo & Manouba
    { id: 'st-7182', stop_id: 7182, name: 'Cnam-Bardo', lat: 36.8068875, lon: 10.1383771, horaires_count: 26 },
    { id: 'st-7183', stop_id: 7183, name: 'Chebbi', lat: 36.8096013, lon: 10.1313362, horaires_count: 26 },
    { id: 'st-7184', stop_id: 7184, name: 'Saint Clement', lat: 36.8104848, lon: 10.126229, horaires_count: 26 },
    { id: 'st-7185', stop_id: 7185, name: 'Bortal', lat: 36.8120871, lon: 10.1174078, horaires_count: 26 },
    { id: 'st-7186', stop_id: 7186, name: 'Champ De Course Ksar Said', lat: 36.8130249, lon: 10.1133431, horaires_count: 26 },
    { id: 'st-7187', stop_id: 7187, name: 'Hopital Kassab', lat: 36.8155796, lon: 10.1003191, horaires_count: 26 },
    { id: 'st-7188', stop_id: 7188, name: 'Boudria', lat: 36.8161882, lon: 10.0961131, horaires_count: 26 },
    { id: 'st-7189', stop_id: 7189, name: 'Ibn Jazzar Mannouba', lat: 36.8128095, lon: 10.0892791, horaires_count: 26 },
    { id: 'st-7190', stop_id: 7190, name: 'Gouvernorat Manouba', lat: 36.8114227, lon: 10.0885442, horaires_count: 26 },
    { id: 'st-7191', stop_id: 7191, name: 'Dar Mocennine', lat: 36.8095931, lon: 10.0910119, horaires_count: 26 },
    { id: 'st-7192', stop_id: 7192, name: 'Hedi Chaker Mannouba', lat: 36.8079266, lon: 10.0893006, horaires_count: 26 },
    { id: 'st-7193', stop_id: 7193, name: 'Municipalite Mannouba', lat: 36.8068099, lon: 10.0870475, horaires_count: 26 },
    { id: 'st-7194', stop_id: 7194, name: 'Sidi Amor Mannouba', lat: 36.807287, lon: 10.0828732, horaires_count: 26 },
    { id: 'st-7195', stop_id: 7195, name: 'Palais El Warda', lat: 36.809297, lon: 10.0739254, horaires_count: 26 },
    { id: 'st-7196', stop_id: 7196, name: 'Faculte Des Lettres Mannouba', lat: 36.8110837, lon: 10.0659002, horaires_count: 26 },
    { id: 'st-7197', stop_id: 7197, name: 'Restaurant Universitaire Mannouba', lat: 36.813901, lon: 10.0604714, horaires_count: 26 },
    { id: 'st-7198', stop_id: 7198, name: 'Rabattement Khaireddine Mannouba', lat: 36.8156704, lon: 10.0564588, horaires_count: 26 }
  ];

  b104.stops = cleanedStops;
  console.log(`Updated Bus 104 with ${cleanedStops.length} stops (Bouchoucha bypassed via Bab Saadoun & Blvd 20 Mars)`);

  // Write updated staticTransit.js
  const staticTransitContent = `// Static Transit Data for Tunisia (GTFS & Transtu official network)
export const TRANSIT_NETWORKS = ${JSON.stringify(TRANSIT_NETWORKS, null, 2)};

export const STATIC_LINES = ${JSON.stringify(STATIC_LINES, null, 2)};
`;
  fs.writeFileSync('src/data/staticTransit.js', staticTransitContent, 'utf8');
  console.log('Saved src/data/staticTransit.js');

  // Route Direction 0 (Aller: Tunis Marine -> Khaireddine Mannouba)
  console.log('Routing Direction 0 (Aller: Tunis Marine -> Khaireddine)...');
  const shapeDir0 = await routeStops(cleanedStops);
  console.log(`-> Direction 0 generated ${shapeDir0.length} road curve points!`);

  // Route Direction 1 (Retour: Khaireddine Mannouba -> Tunis Marine)
  console.log('Routing Direction 1 (Retour: Khaireddine -> Tunis Marine)...');
  const returnStops = [...cleanedStops].reverse();
  const shapeDir1 = await routeStops(returnStops);
  console.log(`-> Direction 1 generated ${shapeDir1.length} road curve points!`);

  // Update transitShapes.json
  const shapes = JSON.parse(fs.readFileSync('src/data/transitShapes.json', 'utf8'));
  shapes['bus_772'] = shapeDir0;
  shapes['bus_772_0'] = shapeDir0;
  shapes['bus_772_1'] = shapeDir1;

  fs.writeFileSync('src/data/transitShapes.json', JSON.stringify(shapes));
  console.log('Updated src/data/transitShapes.json with bus_772, bus_772_0, and bus_772_1!');
}

main();

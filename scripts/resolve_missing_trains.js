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

// Slice polyline from closest point to pStart to closest point to pEnd
function slicePolyline(points, pStart, pEnd) {
  let closestStartIdx = 0;
  let minStartDist = Infinity;
  let closestEndIdx = points.length - 1;
  let minEndDist = Infinity;

  points.forEach((pt, idx) => {
    const dStart = getDistance(pt, pStart);
    if (dStart < minStartDist) {
      minStartDist = dStart;
      closestStartIdx = idx;
    }
    const dEnd = getDistance(pt, pEnd);
    if (dEnd < minEndDist) {
      minEndDist = dEnd;
      closestEndIdx = idx;
    }
  });

  if (closestStartIdx <= closestEndIdx) {
    return points.slice(closestStartIdx, closestEndIdx + 1);
  } else {
    return points.slice(closestEndIdx, closestStartIdx + 1).reverse();
  }
}

async function run() {
  const shapes = JSON.parse(fs.readFileSync('src/data/transitShapes.json', 'utf8'));

  // 1. train_18 (Tunis Ville - Sfax) from train_21 (Tunis Ville - Gabes)
  if (shapes['train_21']) {
    const tunisVille = [36.7947693, 10.1803806];
    const sfaxStation = [34.7402, 10.7601];
    shapes['train_18'] = slicePolyline(shapes['train_21'], tunisVille, sfaxStation);
    console.log(`Derived train_18 (Tunis - Sfax): ${shapes['train_18'].length} points`);
  }

  // 2. train_17 (Tunis Ville - Nabeul) from train_23 (Tunis - Sousse) + train_45 (Bir Bourekba - Nabeul)
  if (shapes['train_23'] && shapes['train_45']) {
    const tunisVille = [36.7947693, 10.1803806];
    const birBourekba = [36.4357, 10.5898];
    const tunisToBir = slicePolyline(shapes['train_23'], tunisVille, birBourekba);
    shapes['train_17'] = [...tunisToBir, ...shapes['train_45']];
    console.log(`Derived train_17 (Tunis - Nabeul): ${shapes['train_17'].length} points`);
  }

  // 3. train_36 (Sousse Bab Jdid - Moknine) from train_1 (Sousse - Mahdia)
  if (shapes['train_1']) {
    const sousseBabJdid = [35.823063, 10.6415928];
    const moknine = [35.6268, 10.9008];
    shapes['train_36'] = slicePolyline(shapes['train_1'], sousseBabJdid, moknine);
    console.log(`Derived train_36 (Sousse - Moknine): ${shapes['train_36'].length} points`);
  }

  // 4. train_38 (Sousse Bab Jdid - Sousse Sud) from train_1
  if (shapes['train_1']) {
    const sousseBabJdid = [35.823063, 10.6415928];
    const sousseSud = [35.800173, 10.649924];
    shapes['train_38'] = slicePolyline(shapes['train_1'], sousseBabJdid, sousseSud);
    console.log(`Derived train_38 (Sousse Bab Jdid - Sousse Sud): ${shapes['train_38'].length} points`);
  }

  // 5. train_41 (Monastir - Sousse Sud) from train_3 + train_1
  if (shapes['train_3'] && shapes['train_1']) {
    const monastir = [35.7725, 10.8262];
    const sousseSud = [35.800173, 10.649924];
    shapes['train_41'] = slicePolyline(shapes['train_3'], sousseSud, monastir);
    console.log(`Derived train_41 (Monastir - Sousse Sud): ${shapes['train_41'].length} points`);
  }

  // 6. bus_870 (Bus 44B Intilaka - Cité Monji Slim) via OSRM
  try {
    const url = 'https://router.project-osrm.org/route/v1/driving/10.1384,36.8322;10.0263224,36.9051251?overview=full&geometries=geojson';
    const res = await fetch(url, { headers: { 'User-Agent': 'WhereAmI-Transit/1.0' } });
    const data = await res.json();
    if (data.routes && data.routes[0]) {
      const raw = data.routes[0].geometry.coordinates.map(c => [
        parseFloat(c[1].toFixed(5)),
        parseFloat(c[0].toFixed(5))
      ]);
      // Decimate to ~20m
      const decimated = [raw[0]];
      let last = raw[0];
      for (let i = 1; i < raw.length - 1; i++) {
        if (getDistance(last, raw[i]) >= 20) {
          decimated.push(raw[i]);
          last = raw[i];
        }
      }
      decimated.push(raw[raw.length - 1]);
      shapes['bus_870'] = decimated;
      console.log(`Added bus_870 (44B Intilaka - Cité Monji Slim): ${decimated.length} points`);
    }
  } catch (e) {
    console.error('Error fetching 44B shape:', e.message);
  }

  fs.writeFileSync('src/data/transitShapes.json', JSON.stringify(shapes));
  console.log(`Updated transitShapes.json successfully! Total shapes now: ${Object.keys(shapes).length}`);
}

run();

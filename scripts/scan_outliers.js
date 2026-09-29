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

function scanOutliers() {
  console.log(`Scanning all ${STATIC_LINES.length} lines for zigzag outlier stops...`);
  const outliers = [];

  STATIC_LINES.forEach(line => {
    if (!line.stops || line.stops.length < 3) return;

    for (let i = 1; i < line.stops.length - 1; i++) {
      const prev = [line.stops[i - 1].lat, line.stops[i - 1].lon];
      const curr = [line.stops[i].lat, line.stops[i].lon];
      const next = [line.stops[i + 1].lat, line.stops[i + 1].lon];

      const dPrev = getDistance(prev, curr);
      const dNext = getDistance(curr, next);
      const dDirect = getDistance(prev, next);

      // If jump to current is > 2.5km AND jump back is > 2.5km, while prev and next are close (< 1.5km)
      if (dPrev > 2500 && dNext > 2500 && dDirect < 1500) {
        outliers.push({
          lineId: line.id,
          lineName: `${line.short_name} (${line.long_name})`,
          stopIndex: i + 1,
          stopName: line.stops[i].name,
          prevStop: line.stops[i - 1].name,
          nextStop: line.stops[i + 1].name,
          jumpDistKm: (dPrev / 1000).toFixed(1),
          directDistKm: (dDirect / 1000).toFixed(1)
        });
      }
    }
  });

  console.log(`Found ${outliers.length} outlier zigzag stops across all lines:`);
  outliers.forEach(o => {
    console.log(`\nLine: ${o.lineName} [${o.lineId}]`);
    console.log(` - Outlier Stop #${o.stopIndex}: "${o.stopName}"`);
    console.log(` - Squeezed between: "${o.prevStop}" and "${o.nextStop}"`);
    console.log(` - Jump distance: ${o.jumpDistKm} km (Direct distance between neighbours: ${o.directDistKm} km)`);
  });
}

scanOutliers();

import { STATIC_LINES } from '../src/data/staticTransit.js';

console.log('Total static lines:', STATIC_LINES.length);
const busLines = STATIC_LINES.filter(l => l.type_id === 'bus');
console.log('Total bus lines:', busLines.length);

function getDist(lat1, lon1, lat2, lon2) {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

let spikeCount = 0;
const spikeResults = [];

function checkSequence(stops, dirName, lineShort, lineId) {
  if (!stops || stops.length < 3) return;
  for (let i = 0; i < stops.length - 2; i++) {
    const d01 = getDist(stops[i].lat, stops[i].lon, stops[i+1].lat, stops[i+1].lon);
    const d12 = getDist(stops[i+1].lat, stops[i+1].lon, stops[i+2].lat, stops[i+2].lon);
    const d02 = getDist(stops[i].lat, stops[i].lon, stops[i+2].lat, stops[i+2].lon);
    
    // Outlier spike: stop i+1 jumps far away (> 2.5km) while direct i to i+2 is close (< 1.8km)
    if (d01 > 2.5 && d12 > 2.5 && d02 < 1.8) {
      spikeResults.push({
        line: lineShort,
        id: lineId,
        dir: dirName,
        idx: i + 1,
        stop: stops[i+1].name,
        prev: stops[i].name,
        next: stops[i+2].name,
        jump: d01.toFixed(1) + ' km'
      });
      spikeCount++;
    }
  }
}

for (const l of busLines) {
  checkSequence(l.stops, 'Aller', l.short_name, l.id);
  checkSequence(l.stops_retour, 'Retour', l.short_name, l.id);
}

console.log(`\n=== ANOMALY AUDIT RESULTS ===`);
console.log(`Outlier Spikes Detected across all Aller & Retour stops: ${spikeCount}`);
if (spikeCount > 0) {
  spikeResults.forEach(r => console.log('  ⚠️', JSON.stringify(r)));
} else {
  console.log('✅ ZERO outlier spikes found in any bus line (Aller or Retour)!');
}

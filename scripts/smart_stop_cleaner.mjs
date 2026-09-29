import fs from 'fs';
import { STATIC_LINES } from '../src/data/staticTransit.js';

function getDist(lat1, lon1, lat2, lon2) {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

/**
 * Cleans a bus line's stop sequence:
 * 1. Handles specific user requirement for Bus 104 (no Bouchoucha / Caserne Bouchoucha)
 * 2. Detects rogue coordinates (bad GPS entered in database, e.g. 40km away in wrong governorate)
 * 3. Detects misplaced / out-of-order stops and relocates them to the optimal position along the route
 * 4. Removes true outliers that do not belong to the route corridor
 */
export function cleanLineStops(lineId, shortName, initialStops) {
  let stops = [...initialStops];

  // Specific rule for Bus 104 from user:
  // "104 does not go through the line bouchoucha"
  if (lineId === 'bus_772' || shortName === '104') {
    stops = stops.filter(s => {
      const n = (s.name || '').toLowerCase();
      return !n.includes('bouchoucha') && !n.includes('khaznadar');
    });
  }

  if (stops.length < 3) return stops;

  let changed = true;
  let iterations = 0;

  while (changed && iterations < 8) {
    changed = false;
    iterations++;

    for (let i = 0; i < stops.length; i++) {
      const curr = stops[i];
      const prev = i > 0 ? stops[i - 1] : null;
      const next = i < stops.length - 1 ? stops[i + 1] : null;

      let isAnomaly = false;
      let reason = '';

      if (prev && next) {
        const dPrevCurr = getDist(prev.lat, prev.lon, curr.lat, curr.lon);
        const dCurrNext = getDist(curr.lat, curr.lon, next.lat, next.lon);
        const dPrevNext = getDist(prev.lat, prev.lon, next.lat, next.lon);

        // Spike: curr is far from both prev and next, but prev and next are reasonably close
        if (dPrevCurr > 2.0 && dCurrNext > 2.0 && dPrevNext < 3.0) {
          isAnomaly = true;
          reason = `Spike: prev->curr=${dPrevCurr.toFixed(1)}km, curr->next=${dCurrNext.toFixed(1)}km, direct=${dPrevNext.toFixed(1)}km`;
        }
        // Extreme jump: curr is > 10km away from both
        else if (dPrevCurr > 10.0 && dCurrNext > 10.0) {
          isAnomaly = true;
          reason = `Extreme jump: prev->curr=${dPrevCurr.toFixed(1)}km, curr->next=${dCurrNext.toFixed(1)}km`;
        }
      } else if (!prev && next) {
        // First stop is extremely far from second stop
        const dCurrNext = getDist(curr.lat, curr.lon, next.lat, next.lon);
        if (dCurrNext > 12.0) {
          isAnomaly = true;
          reason = `Start stop is ${dCurrNext.toFixed(1)}km from next stop`;
        }
      } else if (prev && !next) {
        // Last stop is extremely far from previous stop
        const dPrevCurr = getDist(prev.lat, prev.lon, curr.lat, curr.lon);
        if (dPrevCurr > 12.0) {
          isAnomaly = true;
          reason = `End stop is ${dPrevCurr.toFixed(1)}km from prev stop`;
        }
      }

      if (isAnomaly) {
        const remaining = stops.filter((_, idx) => idx !== i);

        // Try to find if curr belongs elsewhere in the line (detour < 1.0 km)
        let bestPos = -1;
        let bestDetour = Infinity;

        for (let j = 0; j < remaining.length - 1; j++) {
          const p1 = remaining[j];
          const p2 = remaining[j + 1];
          const direct = getDist(p1.lat, p1.lon, p2.lat, p2.lon);
          const via = getDist(p1.lat, p1.lon, curr.lat, curr.lon) + getDist(curr.lat, curr.lon, p2.lat, p2.lon);
          const detour = via - direct;

          if (detour < bestDetour && detour < 1.0) {
            bestDetour = detour;
            bestPos = j + 1;
          }
        }

        if (bestPos !== -1) {
          console.log(`[${shortName}] 🔄 Relocated "${curr.name}" from #${i+1} to #${bestPos+1} (${reason}, detour: ${bestDetour.toFixed(2)}km)`);
          remaining.splice(bestPos, 0, curr);
          stops = remaining;
          changed = true;
          break;
        } else {
          console.log(`[${shortName}] ❌ Removed corrupt stop "${curr.name}" (${reason})`);
          stops = remaining;
          changed = true;
          break;
        }
      }
    }
  }

  return stops;
}

// Test on all 190 lines
let totalFixed = 0;
const busLines = STATIC_LINES.filter(l => l.type_id === 'bus');

for (const line of busLines) {
  const cleaned = cleanLineStops(line.id, line.short_name, line.stops);
  if (cleaned.length !== line.stops.length || cleaned.some((s, idx) => s.id !== line.stops[idx]?.id)) {
    totalFixed++;
  }
}

console.log(`\n========================================`);
console.log(`Total bus lines cleaned: ${totalFixed} / ${busLines.length}`);
console.log(`========================================`);

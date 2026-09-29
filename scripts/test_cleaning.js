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

function cleanAllLines() {
  console.log('Cleaning outlier and corrupted stops in STATIC_LINES...');

  STATIC_LINES.forEach(line => {
    // 1. Bus 104 fix: move Gouvernorat Manouba to its rightful place in Manouba
    if (line.id === 'bus_772') {
      const gouvIdx = line.stops.findIndex(s => s.name.includes('Gouvernorat'));
      if (gouvIdx !== -1 && gouvIdx < 10) {
        const [gouvStop] = line.stops.splice(gouvIdx, 1);
        const jazzarIdx = line.stops.findIndex(s => s.name.includes('Jazzar'));
        if (jazzarIdx !== -1) {
          line.stops.splice(jazzarIdx + 1, 0, gouvStop);
          console.log('✓ Fixed Bus 104: moved Gouvernorat Manouba to Manouba center');
        }
      }
    }

    // 2. Lines 24 and 54 series: remove false La Goulette Cité El Habib stop
    if (['bus_714', 'bus_818', 'bus_819', 'bus_820', 'bus_821', 'bus_822', 'bus_860', 'bus_861'].includes(line.id)) {
      const habibIdx = line.stops.findIndex(s => s.name.includes('Habib') && s.lat > 36.85);
      if (habibIdx !== -1) {
        line.stops.splice(habibIdx, 1);
        console.log(`✓ Fixed ${line.id} (${line.short_name}): removed false distant Cité El Habib stop`);
      }
    }

    // 3. Line 44D/: remove distant Mornaguia coordinate of Cite Monji Slim
    if (line.id === 'bus_859') {
      const wrongIdx = line.stops.findIndex(s => s.name === 'Cite Monji Slim' && s.lat < 36.8);
      if (wrongIdx !== -1) {
        line.stops.splice(wrongIdx, 1);
        console.log('✓ Fixed Line 44D/: removed distant Mornaguia coordinate');
      }
    }

    // 4. Line 3D: remove distant Carthage 20 Mars & distant Soned
    if (line.id === 'bus_851') {
      line.stops = line.stops.filter(s => {
        if (s.name.includes('20 Mars') && s.lat > 36.85) return false;
        if (s.name.includes('Soned') && s.lat < 36.75) return false;
        return true;
      });
      console.log('✓ Fixed Line 3D: removed false distant stops');
    }

    // 5. Lines 26A, 26B, 37: remove false Sprolos and Cité Bel Air jumps
    if (['bus_828', 'bus_829', 'bus_725'].includes(line.id)) {
      line.stops = line.stops.filter(s => {
        if (s.name.includes('Sprolos') && s.lon < 10.2) return false;
        if (s.name.includes('Bel Air') && s.lat > 36.75) return false;
        return true;
      });
      console.log(`✓ Fixed ${line.id} (${line.short_name}): cleaned outlier stops`);
    }
  });

  // Re-verify outliers
  let remaining = 0;
  STATIC_LINES.forEach(line => {
    if (!line.stops || line.stops.length < 3) return;
    for (let i = 1; i < line.stops.length - 1; i++) {
      const prev = [line.stops[i - 1].lat, line.stops[i - 1].lon];
      const curr = [line.stops[i].lat, line.stops[i].lon];
      const next = [line.stops[i + 1].lat, line.stops[i + 1].lon];
      if (getDistance(prev, curr) > 2500 && getDistance(curr, next) > 2500 && getDistance(prev, next) < 1500) {
        remaining++;
        console.log(`Remaining: ${line.id} (${line.short_name}) stop ${i + 1}: ${line.stops[i].name} between ${line.stops[i-1].name} and ${line.stops[i+1].name}`);
      }
    }
  });
  console.log(`Remaining outliers after cleaning: ${remaining}`);
}

cleanAllLines();

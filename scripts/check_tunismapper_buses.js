import { STATIC_LINES } from '../src/data/staticTransit.js';

async function checkTunismapperBuses() {
  const buses = STATIC_LINES.filter(l => l.type_id === 'bus');
  console.log(`Checking 10 sample buses on Tunismapper...`);
  for (let i = 0; i < 10; i++) {
    const b = buses[i];
    try {
      const url = `https://www.tunismapper.com/ligne_details.php?route_id=${b.route_id}`;
      const res = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
      const text = await res.text();
      const match = text.match(/var shapes\s*=\s*(\[[\s\S]*?\]);/);
      if (match) {
        const raw = JSON.parse(match[1]);
        const count = (raw && raw[0]) ? raw[0].length : 0;
        console.log(`Bus ${b.id} (route ${b.route_id}, ${b.short_name}): ${count} points`);
      } else {
        console.log(`Bus ${b.id}: NO shapes var`);
      }
    } catch (e) {
      console.log(`Bus ${b.id} err: ${e.message}`);
    }
  }
}

checkTunismapperBuses();

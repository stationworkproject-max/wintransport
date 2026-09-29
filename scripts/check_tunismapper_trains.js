import { STATIC_LINES } from '../src/data/staticTransit.js';

async function checkTunismapperTrains() {
  const trains = STATIC_LINES.filter(l => l.type_id === 'train');
  console.log(`Checking ${trains.length} train lines on tunismapper...`);

  for (const t of trains) {
    try {
      const url = `https://www.tunismapper.com/ligne_details.php?route_id=${t.route_id}`;
      const res = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
      const text = await res.text();
      const match = text.match(/var shapes\s*=\s*(\[[\s\S]*?\]);/);
      if (match) {
        try {
          const raw = JSON.parse(match[1]);
          const count = (raw && raw[0]) ? raw[0].length : 0;
          console.log(`[FOUND] Train ${t.id} (route ${t.route_id}, ${t.long_name}): ${count} shape points!`);
        } catch (pe) {
          console.log(`[PARSE ERR] Train ${t.id} (route ${t.route_id})`);
        }
      } else {
        console.log(`[NO SHAPE] Train ${t.id} (route ${t.route_id}, ${t.long_name})`);
      }
    } catch (e) {
      console.log(`[ERR] Train ${t.id}: ${e.message}`);
    }
  }
}

checkTunismapperTrains();

import fs from 'fs';

async function checkHorairesDirs() {
  const res = await fetch('https://www.tunismapper.com/ligne_details.php?route_id=772', {
    headers: { 'User-Agent': 'Mozilla/5.0' }
  });
  const html = await res.text();
  const match = html.match(/var stops\s*=\s*(\[[\s\S]*?\]);/);
  if (match) {
    const stops = JSON.parse(match[1]);
    const dirs = new Set();
    const dirStops = {};

    stops.forEach((s, idx) => {
      const stopDirs = new Set();
      (s.horaires || []).forEach(h => {
        dirs.add(h.direction);
        stopDirs.add(h.direction);
        if (!dirStops[h.direction]) dirStops[h.direction] = [];
        if (!dirStops[h.direction].includes(s.name)) dirStops[h.direction].push(s.name);
      });
      console.log(`#${idx + 1} ${s.name} -> Dirs: [${[...stopDirs].join(', ')}]`);
    });

    console.log('\n--- ALL UNIQUE DIRECTIONS ---');
    console.log([...dirs]);

    for (const [d, stList] of Object.entries(dirStops)) {
      console.log(`\nDirection: "${d}" (${stList.length} stops)`);
      stList.forEach((st, i) => console.log(`  ${i+1}. ${st}`));
    }
  }
}

checkHorairesDirs();

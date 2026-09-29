import fs from 'fs';

const allLines = JSON.parse(fs.readFileSync('tunismapper_all_lines.json', 'utf-8'));
console.log(`Starting stops download for ${allLines.length} lines...`);

async function fetchStopsForLine(line) {
  const url = `https://www.tunismapper.com/ligne_details.php?route_id=${line.route_id}`;
  try {
    const res = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
    if (!res.ok) return null;
    const text = await res.text();
    const match = text.match(/var stops\s*=\s*(\[[\s\S]*?\]);/);
    if (match) {
      const stops = JSON.parse(match[1]);
      return stops.map((s, idx) => ({
        id: `st-${s.stop_id || idx}`,
        stop_id: s.stop_id,
        name: s.name,
        lat: parseFloat(s.lat),
        lon: parseFloat(s.lon),
        horaires_count: s.horaires ? s.horaires.length : 0
      }));
    }
  } catch (err) {
    console.error(`Error line ${line.route_id} (${line.short_name}):`, err.message);
  }
  return null;
}

async function main() {
  const concurrency = 8;
  const detailedLines = [];

  for (let i = 0; i < allLines.length; i += concurrency) {
    const slice = allLines.slice(i, i + concurrency);
    const results = await Promise.all(
      slice.map(async (line) => {
        const stops = await fetchStopsForLine(line);
        
        // Clean directions from long_name
        let directions = [];
        if (line.long_name.includes(' - ')) {
          directions = line.long_name.split(' - ').map(s => s.trim());
        } else if (line.long_name.includes('-')) {
          directions = line.long_name.split('-').map(s => s.trim());
        } else {
          directions = [line.long_name, 'Retour'];
        }

        const cleanColor = line.color.startsWith('#') ? line.color : `#${line.color}`;

        return {
          id: `${line.type}_${line.route_id}`,
          route_id: line.route_id,
          type_id: line.short_name === 'TGM' ? 'tgm' : line.type,
          short_name: line.short_name || 'Ligne',
          long_name: line.long_name,
          color: cleanColor,
          directions: directions.length >= 2 ? [directions[1], directions[0]] : directions,
          frequency_mins: line.type === 'metro' ? 8 : (line.type === 'rfr' ? 15 : 20),
          stops: stops || []
        };
      })
    );

    detailedLines.push(...results);
    const progress = Math.min(i + concurrency, allLines.length);
    console.log(`Progress: ${progress} / ${allLines.length} lines processed`);
    // Brief sleep to be polite
    await new Promise(r => setTimeout(r, 150));
  }

  const withStops = detailedLines.filter(l => l.stops && l.stops.length > 0).length;
  console.log(`Finished! Total lines: ${detailedLines.length}, lines with verified stops: ${withStops}`);

  fs.writeFileSync('tunismapper_full_database.json', JSON.stringify(detailedLines, null, 2), 'utf-8');
}

main();

import { createClient } from '@supabase/supabase-js';
import fs from 'fs';

const SUPABASE_URL = 'https://rqwpafatgsyncvretjym.supabase.co';
const SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJxd3BhZmF0Z3N5bmN2cmV0anltIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MzAxNzYzOSwiZXhwIjoyMDk4NTkzNjM5fQ.kEMKprtQMlf4BFWUU29v76PzalTSdrch3OElFg-JOWk';

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function seed() {
  console.log('Reading tunismapper_full_database.json...');
  const lines = JSON.parse(fs.readFileSync('tunismapper_full_database.json', 'utf-8'));
  console.log(`Loaded ${lines.length} lines.`);

  // 1. Prepare transit_lines
  const lineRecords = lines.map(l => ({
    id: `${l.type_id}_${l.route_id}`,
    type_id: l.type_id,
    short_name: l.short_name,
    long_name: l.long_name,
    color: l.color,
    text_color: '#FFFFFF',
    route_id: parseInt(l.route_id) || 0
  }));

  console.log(`Upserting ${lineRecords.length} lines in batches...`);
  for (let i = 0; i < lineRecords.length; i += 50) {
    const chunk = lineRecords.slice(i, i + 50);
    const { error: lErr } = await supabase.from('transit_lines').upsert(chunk);
    if (lErr) console.error(`Lines batch ${i} error:`, lErr.message);
    else console.log(`Lines batch ${i}-${i + chunk.length} upserted.`);
  }

  // 2. Prepare unique stations
  const routeTypeMap = { rfr: 0, metro: 1, tgm: 1, train: 2, bus: 3 };
  const stationsMap = new Map();
  for (const l of lines) {
    for (const s of l.stops) {
      if (s.stop_id && !stationsMap.has(s.stop_id)) {
        stationsMap.set(s.stop_id, {
          id: `st-${s.stop_id}`,
          stop_id: parseInt(s.stop_id),
          name: s.name,
          lat: parseFloat(s.lat),
          lon: parseFloat(s.lon),
          route_type: routeTypeMap[l.type_id] !== undefined ? routeTypeMap[l.type_id] : 3
        });
      }
    }
  }

  const stationRecords = Array.from(stationsMap.values());
  console.log(`Upserting ${stationRecords.length} unique stations in batches...`);
  for (let i = 0; i < stationRecords.length; i += 100) {
    const chunk = stationRecords.slice(i, i + 100);
    const { error: sErr } = await supabase.from('transit_stations').upsert(chunk);
    if (sErr) console.error(`Stations batch ${i} error:`, sErr.message);
    else console.log(`Stations batch ${i}-${i + chunk.length} upserted.`);
  }

  console.log('Seeding completed successfully!');
}

seed().catch(err => console.error('Fatal seed err:', err));

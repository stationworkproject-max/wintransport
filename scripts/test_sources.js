import fs from 'fs';
import { STATIC_LINES } from '../src/data/staticTransit.js';

async function checkOverpass() {
  const query = `[out:json][timeout:30];
relation["type"="route"]["route"="bus"](36.6,10.0,37.0,10.4);
out tags;`;
  try {
    const res = await fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'WhereAmI-Transit-App/1.0 (aymen@transport.tn)'
      },
      body: new URLSearchParams({ data: query }).toString()
    });
    const text = await res.text();
    try {
      const data = JSON.parse(text);
      console.log('Overpass bus relations found in Greater Tunis:', data.elements ? data.elements.length : 0);
      if (data.elements) {
        data.elements.slice(0, 30).forEach(e => {
          console.log(`- Ref: ${e.tags.ref || '?'}, Name: ${e.tags.name || ''}, Operator: ${e.tags.operator || ''}`);
        });
      }
    } catch (parseErr) {
      console.log('Overpass raw response error (first 300 chars):', text.substring(0, 300));
    }
  } catch (e) {
    console.log('Overpass error:', e.message);
  }
}

async function checkTrains() {
  console.log('Checking trains in STATIC_LINES...');
  const trains = STATIC_LINES.filter(l => l.type_id === 'train');
  console.log('Total train lines:', trains.length);
  trains.forEach(t => {
    console.log(`Train ${t.id} (${t.short_name}): ${t.long_name} - ${t.stops.length} stops`);
  });
}

async function main() {
  await checkOverpass();
  await checkTrains();
}

main();

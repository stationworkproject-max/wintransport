import fs from 'fs';

async function fetchAllBusRoutes() {
  console.log('Fetching all bus routes from Tunismapper API...');
  const allBuses = [];
  const limit = 20;
  let offset = 0;
  let total = 190;

  while (offset <= total) {
    const url = `https://www.tunismapper.com/backend/api/bus_routes.php?limit=${limit}&offset=${offset}`;
    try {
      const res = await fetch(url);
      const json = await res.json();
      if (json.success && json.data) {
        total = json.total || 190;
        allBuses.push(...json.data);
        console.log(`Offset ${offset}: got ${json.data.length} buses. Total so far: ${allBuses.length}/${total}`);
        if (json.data.length === 0) break;
      } else {
        break;
      }
    } catch (err) {
      console.error(`Error fetching offset ${offset}:`, err.message);
      break;
    }
    offset += limit;
  }

  console.log(`Completed fetching buses: ${allBuses.length} lines.`);
  fs.writeFileSync('tunismapper_buses.json', JSON.stringify(allBuses, null, 2), 'utf-8');
  return allBuses;
}

fetchAllBusRoutes();

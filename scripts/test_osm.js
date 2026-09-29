async function run() {
  const query = `[out:json][timeout:25];(relation["route"~"tram|light_rail|train"](36.7,10.0,36.9,10.4););out geom;`;
  const url = 'https://overpass-api.de/api/interpreter?data=' + encodeURIComponent(query);
  try {
    const res = await fetch(url, { headers: { 'User-Agent': 'WinTransportTN/1.0' } });
    const data = await res.json();
    console.log('OSM relations count:', data.elements ? data.elements.length : 0);
    if (data.elements) {
      data.elements.forEach(el => {
        const name = el.tags?.name || el.tags?.description || 'sans nom';
        const ref = el.tags?.ref || '';
        const geomMembers = el.members?.filter(m => m.geometry && m.geometry.length > 0) || [];
        console.log(`Relation ID: ${el.id} | Ref: "${ref}" | Name: "${name}" | Geom Ways: ${geomMembers.length}`);
      });
    }
  } catch (e) {
    console.error('Error fetching OSM:', e.message);
  }
}
run();

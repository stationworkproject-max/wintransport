const query = `[out:json][timeout:30];
relation["route"="bus"]["operator"~"TRANSTU|Transtu"](36.7,10.0,36.9,10.3);
out tags;`;

const url = 'https://overpass-api.de/api/interpreter?data=' + encodeURIComponent(query);
console.log('Querying Overpass for all TRANSTU bus relations in Tunis...');
try {
  const res = await fetch(url, { headers: { 'User-Agent': 'WinTransportTunisia/1.0' } });
  const data = await res.json();
  console.log('Total TRANSTU bus relations:', data.elements?.length);
  data.elements?.slice(0, 15).forEach(e => console.log(e.tags?.ref, e.tags?.name));
} catch (e) {
  console.log('Error:', e.message);
}

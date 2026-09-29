const query = `[out:json][timeout:30];
(
  relation["type"="route"]["route"="bus"]["ref"="3D"](36.7,10.0,36.9,10.3);
  relation["type"="route"]["route"="bus"]["ref"="3 D"](36.7,10.0,36.9,10.3);
  relation["type"="route"]["route"="bus"]["name"~"3D"](36.7,10.0,36.9,10.3);
);
out body;
>;
out skel qt;`;

const url = 'https://overpass-api.de/api/interpreter?data=' + encodeURIComponent(query);
console.log('Querying Overpass for Bus 3D in Greater Tunis...');
try {
  const res = await fetch(url, { headers: { 'User-Agent': 'WinTransportTunisia/1.0' } });
  const data = await res.json();
  console.log('Overpass elements:', data.elements?.length);
  const relations = data.elements.filter(e => e.type === 'relation');
  console.log('Relations:', relations.length);
  relations.forEach(r => {
    console.log('Relation ID:', r.id);
    console.log('Tags:', JSON.stringify(r.tags, null, 2));
    console.log('Members count:', r.members?.length);
    const stopMembers = r.members?.filter(m => m.role.includes('stop') || m.role.includes('platform'));
    console.log('Stop members count:', stopMembers?.length);
  });
} catch (e) {
  console.log('Error:', e.message);
}

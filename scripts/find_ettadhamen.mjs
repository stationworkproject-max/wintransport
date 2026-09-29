const q = encodeURIComponent('Lycée Abou El Kacem Chebbi');
const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${q}&format=json&bounded=1&viewbox=10.05,36.87,10.15,36.81`, { headers: { 'User-Agent': 'WinTransportApp/1.0' } });
const data = await res.json();
console.log('Results for Lycee Chebbi:', data.length);
data.forEach(d => console.log(d.display_name, d.lat, d.lon));

const q2 = encodeURIComponent('Avenue Abou El Kacem Chebbi, Ettadhamen');
const res2 = await fetch(`https://nominatim.openstreetmap.org/search?q=${q2}&format=json`, { headers: { 'User-Agent': 'WinTransportApp/1.0' } });
const data2 = await res2.json();
console.log('Results for Avenue Chebbi:', data2.length);
data2.forEach(d => console.log(d.display_name, d.lat, d.lon));

// Also search Ettadhamen schools / mosques
const q3 = encodeURIComponent('Ettadhamen');
const res3 = await fetch(`https://nominatim.openstreetmap.org/search?q=${q3}&format=json`, { headers: { 'User-Agent': 'WinTransportApp/1.0' } });
const data3 = await res3.json();
console.log('Ettadhamen center:', data3[0]?.lat, data3[0]?.lon);

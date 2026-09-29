import fs from 'fs';
import { STATIC_LINES } from '../src/data/staticTransit.js';
import { cleanLineStops } from './smart_stop_cleaner.mjs';

const line104 = STATIC_LINES.find(l => l.id === 'bus_772');
console.log('Original stops count:', line104.stops.length);
const cleaned104 = cleanLineStops(line104.id, line104.short_name, line104.stops);
console.log('Cleaned stops count:', cleaned104.length);
cleaned104.forEach((s, i) => console.log(`${i+1}. ${s.name} (${s.lat}, ${s.lon})`));

// Chunk for OSRM
function chunk(arr, size) {
  const chunks = [];
  for (let i = 0; i < arr.length; i += size - 1) {
    chunks.push(arr.slice(i, Math.min(i + size, arr.length)));
    if (i + size >= arr.length) break;
  }
  return chunks;
}

async function osrmRoute(stopSubset) {
  const coords = stopSubset.map(s => `${s.lon},${s.lat}`).join(';');
  const url = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`;
  const res = await fetch(url);
  const data = await res.json();
  if (!data.routes || !data.routes[0]) throw new Error('OSRM error');
  return {
    coords: data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon]),
    distance: data.routes[0].distance
  };
}

async function buildShape(stops) {
  const chunks = chunk(stops, 14);
  let fullShape = [];
  let totalDist = 0;
  for (let i = 0; i < chunks.length; i++) {
    const { coords, distance } = await osrmRoute(chunks[i]);
    totalDist += distance;
    if (i === 0) fullShape = fullShape.concat(coords);
    else fullShape = fullShape.concat(coords.slice(1));
    await new Promise(r => setTimeout(r, 200));
  }
  return { shape: fullShape, distanceKm: (totalDist / 1000).toFixed(2) };
}

const aller = await buildShape(cleaned104);
console.log(`\nAller shape: ${aller.shape.length} points, distance: ${aller.distanceKm} km`);

const retour = await buildShape([...cleaned104].reverse());
console.log(`Retour shape: ${retour.shape.length} points, distance: ${retour.distanceKm} km`);

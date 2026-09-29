import fs from 'fs';

const lines = JSON.parse(fs.readFileSync('tunismapper_full_database.json', 'utf-8'));

const content = `/**
 * Complete Tunisia Public Transit Directory (229 Lines, 1590 Stations - Tunismapper Grounded)
 */
export const TRANSIT_NETWORKS = [
  { id: 'all', name: 'Tous les réseaux', icon: 'Layers', color: '#0071e3' },
  { id: 'metro', name: 'Métro Léger', icon: 'Train', color: '#0071e3' },
  { id: 'tgm', name: 'TGM', icon: 'TramFront', color: '#0000FF' },
  { id: 'rfr', name: 'RFR Rapide', icon: 'TrainTrack', color: '#34C759' },
  { id: 'train', name: 'Train SNCFT', icon: 'TrainFront', color: '#FF9500' },
  { id: 'bus', name: 'Bus Transtu (190 Lignes)', icon: 'Bus', color: '#E30613' },
];

export const STATIC_LINES = ${JSON.stringify(lines, null, 2)};
`;

fs.writeFileSync('src/data/staticTransit.js', content, 'utf-8');
console.log('src/data/staticTransit.js updated with all 229 lines and stops!');

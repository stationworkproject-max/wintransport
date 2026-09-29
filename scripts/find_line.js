import fs from 'fs';
const content = fs.readFileSync('src/data/staticTransit.js', 'utf8');
const lines = content.split('\n');
lines.forEach((l, idx) => {
  if (l.includes('bus_870')) {
    console.log(`Line ${idx + 1}: ${l}`);
  }
});

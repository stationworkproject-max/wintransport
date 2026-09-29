import fs from 'fs';

async function checkDirections() {
  const res = await fetch('https://www.tunismapper.com/ligne_details.php?route_id=772', {
    headers: { 'User-Agent': 'Mozilla/5.0' }
  });
  const html = await res.text();
  
  // Search for currentDir
  const matchCurrentDir = html.match(/currentDir\s*=\s*([^;]+);/);
  console.log('currentDir definition:', matchCurrentDir ? matchCurrentDir[0] : 'not found');

  // Search for direction in HTML
  const dirOccurrences = [];
  const lines = html.split('\n');
  lines.forEach((l, idx) => {
    if (l.includes('currentDir') || l.includes('direction') || l.includes('dir=') || l.includes('dir_id')) {
      dirOccurrences.push(`L${idx+1}: ${l.trim()}`);
    }
  });

  console.log(`Found ${dirOccurrences.length} direction occurrences:`);
  dirOccurrences.slice(0, 30).forEach(o => console.log(' ', o));
}

checkDirections();

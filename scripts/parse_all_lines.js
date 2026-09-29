import fs from 'fs';

const html = fs.readFileSync('C:/Users/AymenFrd/.gemini/antigravity/brain/eb7101ed-5eba-4ef1-8359-81f3788f9662/.system_generated/steps/359/content.md', 'utf-8');

function extractLinesFromHtml(panelId, type) {
  const panelRegex = new RegExp(`<div class="tab-panel [^"]*" id="${panelId}"[\\s\\S]*?<\\/div>\\s*(?=<div class="tab-panel|$)`, 'i');
  const match = html.match(panelRegex);
  if (!match) {
    console.log(`Panel ${panelId} not found`);
    return [];
  }
  const panelHtml = match[0];
  const cardRegex = /<a href="ligne_details\.php\?route_id=([^"]+)"[\s\S]*?--card-color:\s*#([0-9a-fA-F]{3,6})[\s\S]*?<span class="line-badge"[^>]*>([^<]*)<\/span>[\s\S]*?<div class="route-name">([^<]+)<\/div>/gi;
  
  const lines = [];
  let m;
  while ((m = cardRegex.exec(panelHtml)) !== null) {
    lines.push({
      route_id: m[1],
      type: type,
      color: m[2],
      short_name: m[3].trim(),
      long_name: m[4].trim()
    });
  }
  return lines;
}

const rfrLines = extractLinesFromHtml('panel-0', 'rfr');
const metroLines = extractLinesFromHtml('panel-1', 'metro');
const trainLines = extractLinesFromHtml('panel-2', 'train');

console.log(`RFR: ${rfrLines.length}`);
console.log(`Metro: ${metroLines.length}`);
console.log(`Train: ${trainLines.length}`);

// Load buses
const buses = JSON.parse(fs.readFileSync('tunismapper_buses.json', 'utf-8')).map(b => ({
  route_id: b.route_id,
  type: 'bus',
  color: b.route_color ? `#${b.route_color}` : '#E30613',
  short_name: (b.route_short_name || 'Bus').trim(),
  long_name: (b.route_long_name || '').trim()
}));

console.log(`Bus: ${buses.length}`);

const allLines = [
  ...rfrLines,
  ...metroLines,
  ...trainLines,
  ...buses
];

console.log(`TOTAL ALL LINES: ${allLines.length}`);
fs.writeFileSync('tunismapper_all_lines.json', JSON.stringify(allLines, null, 2), 'utf-8');

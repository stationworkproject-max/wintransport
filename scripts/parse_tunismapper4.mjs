/**
 * Find route-stop relationship in tunismapper 
 * The page at ?route=772 should show different content
 * Let's look at what's different between the general page and route page
 */
import fs from 'fs';

const html = fs.readFileSync('scripts/tunismapper_route772.html', 'utf8');

// Find all script blocks and their sizes
const scriptBlocks = html.match(/<script[^>]*>([\s\S]*?)<\/script>/g) || [];
console.log('Script blocks:');
scriptBlocks.forEach((s, i) => {
  console.log(`  Block ${i}: ${s.length} chars`);
  // Show first 100 chars of each
  const inner = s.replace(/<script[^>]*>/, '').replace(/<\/script>/, '').trim();
  if (inner.length > 0) console.log('    ' + inner.substring(0, 100));
});

// Look for the horaires data - it had horaires_count in stops
const horairesMatch = html.match(/horaires_count["\s:]+\d+/g) || [];
console.log('\nhoraires_count references:', horairesMatch.slice(0, 5));

// Try fetching the horaires endpoint directly  
const stops_endpoint_clues = html.match(/\/horaires[^"'\s)>]*/g) || [];
const api_clues = html.match(/\/api[^"'\s)>]{0,50}/g) || [];
console.log('\nHoraires endpoints:', stops_endpoint_clues.slice(0, 5));
console.log('API endpoints:', [...new Set(api_clues)].slice(0, 10));

// Look for PHP form actions or AJAX targets
const formActions = html.match(/action="([^"]+)"/g) || [];
const ajaxTargets = html.match(/\$\.(?:get|post|ajax)\(\s*["']([^"']+)["']/g) || [];
console.log('\nForm actions:', formActions);
console.log('AJAX targets:', ajaxTargets);

// Check if there's a separate data file referenced
const dataFiles = html.match(/(?:src|href|url)\s*[=:]\s*["']([^"']+(?:json|csv|xml|txt|data)[^"']*)["']/gi) || [];
console.log('\nData files referenced:', dataFiles.slice(0, 10));

// Look for XMLHttpRequest
const xhrMatches = html.match(/XMLHttpRequest[\s\S]{0,200}/g) || [];
console.log('\nXHR usage:', xhrMatches.slice(0, 2));

// Check for route-specific stop table (HTML table)
const tableMatch = html.match(/<table[^>]*>[\s\S]*?7225[\s\S]*?<\/table>/);
if (tableMatch) console.log('\nTable with stop 7225:', tableMatch[0].substring(0, 300));

// Look for the route filter logic
const filterMatch = html.match(/filter[^(]*\([^)]*route[^)]*\)[\s\S]{0,200}/);
if (filterMatch) console.log('\nFilter logic:', filterMatch[0]);

/**
 * Extract the full big script and find route-stop mapping logic
 */
import fs from 'fs';

const html = fs.readFileSync('scripts/tunismapper_route772.html', 'utf8');
const scriptBlocks = html.match(/<script[^>]*>([\s\S]*?)<\/script>/g) || [];
const bigScript = scriptBlocks[11];

// Save just the big script block for inspection
fs.writeFileSync('scripts/tunismapper_bigscript.js', bigScript);
console.log(`Saved big script (${bigScript.length} chars)`);

// Find all PHP endpoints
const phpEndpoints = bigScript.match(/\/api\/[^'"`\s)>]+/g) || [];
console.log('\nPHP API endpoints:', [...new Set(phpEndpoints)]);

// Look for the route filtering mechanism
// Typically: stations.filter(s => s.route_id === selectedRoute) or similar
const filterMatches = bigScript.match(/\.filter\([^)]{0,200}\)/g) || [];
console.log('\nFilter expressions:', filterMatches.slice(0, 10));

// Find the route parameter usage
const paramMatches = bigScript.match(/(?:route|ligne|line)\s*[=:=]+\s*['"]\d+['"]/gi) || [];
console.log('\nRoute param usage:', paramMatches.slice(0, 10));

// Look for URL params
const urlParams = bigScript.match(/URLSearchParams[\s\S]{0,200}/g) || [];
const getParams = bigScript.match(/\.get\(['"][^'"]+['"]\)/g) || [];
console.log('\nURLSearchParams usage:', urlParams.slice(0, 3));
console.log('\nURL param .get():', getParams.slice(0, 10));

// Look specifically for the route=772 processing
const routeParam = bigScript.match(/['"]route['"][\s\S]{0,300}/);
if (routeParam) console.log('\nRoute param handling:', routeParam[0]);

// Find where horaires/schedule data is
const horairesSection = bigScript.match(/horaires[\s\S]{0,1000}/);
if (horairesSection) console.log('\nHoraires section:', horairesSection[0].substring(0, 300));

// What PHP endpoints does the page call
const fetchCalls = bigScript.match(/fetch\([^)]+\)/g) || [];
const xhrOpen = bigScript.match(/\.open\([^)]+\)/g) || [];
console.log('\nFetch calls:', fetchCalls.slice(0, 10));
console.log('\nXHR opens:', xhrOpen.slice(0, 10));

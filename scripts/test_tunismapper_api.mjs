/**
 * Test tunismapper.com API to find correct endpoint format
 */
import fs from 'fs';

const ROUTE_IDS_TO_TEST = ['772', '703', '723', '700'];

async function tryUrl(url) {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
    const text = await res.text();
    return { status: res.status, body: text.substring(0, 500) };
  } catch (e) {
    return { status: 'ERROR', body: e.message };
  }
}

async function main() {
  // Test various endpoint patterns
  const routeId = '772';
  const endpoints = [
    `https://tunismapper.com/api/route/${routeId}/stops`,
    `https://tunismapper.com/api/routes/${routeId}`,
    `https://tunismapper.com/api/v1/route/${routeId}/stops`,
    `https://tunismapper.com/api/lines/${routeId}/stops`,
    `https://tunismapper.com/api/ligne/${routeId}`,
    `https://tunismapper.com/api/line/${routeId}`,
    `https://tunismapper.com/en/line/${routeId}`,
    `https://tunismapper.com/en/bus/line/${routeId}`,
  ];
  
  console.log(`Testing API endpoints for route ${routeId}:`);
  for (const url of endpoints) {
    const result = await tryUrl(url);
    console.log(`\n[${result.status}] ${url}`);
    if (result.status === 200) {
      console.log('BODY:', result.body);
    }
  }
  
  // Also try to get the main page to see what APIs are called
  console.log('\n\nTesting main site:');
  const mainPage = await tryUrl('https://tunismapper.com');
  console.log('Main page status:', mainPage.status);
}

main().catch(console.error);

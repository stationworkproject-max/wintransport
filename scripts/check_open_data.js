import fs from 'fs';
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

async function check() {
  try {
    const res = await fetch('https://data.transport.tn/fr/dataset?q=transtu', {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    const html = await res.text();
    const links = [...html.matchAll(/href="([^"]+)"/g)].map(m => m[1]);
    const datasetLinks = [...new Set(links.filter(l => l.includes('/dataset/')))];
    console.log('Datasets found:', datasetLinks);
  } catch (e) {
    console.error(e);
  }
}
check();

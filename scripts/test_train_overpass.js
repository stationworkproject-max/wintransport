import fs from 'fs';

async function checkTrainOverpass() {
  const query = `[out:json][timeout:30];
relation["route"="train"](33.0,7.5,37.5,11.5);
out tags;`;
  try {
    const res = await fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'WhereAmI-Transit-App/1.0 (aymen@transport.tn)'
      },
      body: new URLSearchParams({ data: query }).toString()
    });
    const data = await res.json();
    console.log('Train relations found:', data.elements ? data.elements.length : 0);
    if (data.elements) {
      data.elements.forEach(e => {
        console.log(`- Rel ID: ${e.id}, Ref: ${e.tags.ref || '?'}, Name: ${e.tags.name || ''}, From: ${e.tags.from || ''} -> To: ${e.tags.to || ''}`);
      });
    }
  } catch (e) {
    console.log('Train Overpass err:', e.message);
  }
}

checkTrainOverpass();

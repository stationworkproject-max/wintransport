import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load train shapes and static lines
with open('src/data/transitShapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    st_text = f.read()

prefix = 'export const STATIC_LINES = '
idx = st_text.find(prefix)
lines = json.loads(st_text[idx + len(prefix):st_text.rfind(']') + 1])

rail_lines = [l for l in lines if l.get('type_id') in ['rfr', 'metro', 'tgm', 'train']]

routes_data = {}
for tl in rail_lines:
    lid = tl['id']
    pts = shapes.get(lid, [])
    # Convert pts from [lat, lon] to [lon, lat] for rail_map.html canvas
    lonlat_pts = [[round(p[1], 5), round(p[0], 5)] for p in pts]
    stops = [[s['name'], round(s['lon'], 5), round(s['lat'], 5)] for s in tl.get('stops', [])]
    routes_data[lid] = {
        'id': lid,
        'type': tl.get('type_id', 'train'),
        'name': f"[{tl.get('type_id', '').upper()}] {tl.get('short_name', '')} - {tl.get('long_name', '')}",
        'color': tl.get('color', '#00e5ff'),
        'stops': stops,
        'pts': lonlat_pts
    }

print(f"Prepared {len(routes_data)} total rail & metro routes for rail_map.html.")

# Read existing rail_map.html to extract DATA
with open('rail_map.html', 'r', encoding='utf-8') as f:
    html = f.read()

data_start = html.find('const DATA=')
data_end = html.find(';', data_start)
data_str = html[data_start:data_end + 1]

new_html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<title>Tunisia Rail Network & Lines Inspector</title>
<style>
html,body{{margin:0;height:100%;background:#0b0f14;overflow:hidden;touch-action:none;font-family:system-ui,-apple-system,sans-serif}}
canvas{{display:block;width:100%;height:100%}}
#topbar{{position:fixed;left:12px;top:12px;background:#151c24e6;backdrop-filter:blur(8px);color:#fff;padding:10px 14px;border-radius:10px;border:1px solid #2d3748;display:flex;align-items:center;gap:10px;box-shadow:0 4px 16px rgba(0,0,0,0.5);z-index:100}}
#topbar label{{font-size:12px;color:#94a3b8;font-weight:600}}
#trainSel{{background:#1e293b;color:#f8fafc;border:1px solid #475569;border-radius:6px;padding:6px 10px;font-size:13px;outline:none;cursor:pointer}}
#btn{{background:#334155;color:#fff;border:0;border-radius:6px;padding:6px 12px;font-size:12px;cursor:pointer;font-weight:600}}
#btn:hover{{background:#475569}}
#leg{{position:fixed;left:12px;bottom:12px;background:#151c24e6;backdrop-filter:blur(8px);color:#fff;padding:10px 14px;border-radius:10px;border:1px solid #2d3748;font-size:11px;line-height:1.7;box-shadow:0 4px 16px rgba(0,0,0,0.5);z-index:100}}
#leg .title{{font-weight:700;color:#94a3b8;margin-bottom:4px;text-transform:uppercase;font-size:10px;letter-spacing:0.5px}}
#leg label{{display:block;cursor:pointer}}
#leg i{{display:inline-block;width:16px;height:4px;margin-right:6px;vertical-align:middle;border-radius:2px}}
#routeInfo{{position:fixed;right:12px;top:12px;max-width:320px;background:#151c24e6;backdrop-filter:blur(8px);color:#fff;padding:12px 16px;border-radius:10px;border:1px solid #2d3748;font-size:12px;box-shadow:0 4px 16px rgba(0,0,0,0.5);display:none;z-index:100}}
#routeInfo h3{{margin:0 0 6px 0;font-size:14px;color:#38bdf8}}
#routeInfo .badge{{display:inline-block;background:#0369a1;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;margin-bottom:6px}}
#routeInfo .stops-list{{max-height:220px;overflow-y:auto;margin-top:6px;padding-left:16px;font-size:11px;line-height:1.6;color:#cbd5e1}}
</style></head><body>
<canvas id="c"></canvas>
<div id="topbar">
  <label for="trainSel">SELECT LINE:</label>
  <select id="trainSel">
    <option value="">-- View All Tracks (Overview) --</option>
  </select>
  <button id="btn">Reset View</button>
</div>
<div id="routeInfo">
  <span class="badge" id="rBadge"></span>
  <h3 id="rTitle"></h3>
  <div id="rDetails" style="color:#94a3b8;font-size:11px;"></div>
  <ol class="stops-list" id="rStops"></ol>
</div>
<div id="leg">
  <div class="title">Rail Network Tracks (rail.geojson)</div>
</div>
<script>
{data_str}
const TRAIN_ROUTES = {json.dumps(routes_data, separators=(',', ':'))};

const CATS=[
  ["Main line (SNCFT/RFR Heavy Rail)","#ffb020",2.2],
  ["Branch","#4dd0e1",1.6],
  ["Freight","#ef5350",1.6],
  ["Industrial","#b39ddb",1.2],
  ["Light rail (TRANSTU Métro & TGM)","#22c55e",2.0],
  ["Tram","#ec4899",1.6],
  ["Yard / siding / spur","#64748b",0.8]
];

const show=CATS.map(_=>true);
const leg=document.getElementById('leg');
CATS.forEach((c,i)=>{{
  const l=document.createElement('label');
  l.innerHTML='<input type="checkbox" checked> <i style="background:'+c[1]+'"></i>'+c[0];
  l.firstChild.onchange=e=>{{show[i]=e.target.checked;draw()}};
  leg.appendChild(l);
}});

// Populate Line selector grouped by category
const trainSel=document.getElementById('trainSel');
const rfrGroup=document.createElement('optgroup'); rfrGroup.label='--- RFR Lines ---';
const metroGroup=document.createElement('optgroup'); metroGroup.label='--- Métro Léger & TGM ---';
const sncftGroup=document.createElement('optgroup'); sncftGroup.label='--- SNCFT Trains ---';

Object.values(TRAIN_ROUTES).forEach(r=>{{
  const opt=document.createElement('option');
  opt.value=r.id;
  opt.textContent=r.name;
  if(r.type==='rfr') rfrGroup.appendChild(opt);
  else if(r.type==='metro'||r.type==='tgm') metroGroup.appendChild(opt);
  else sncftGroup.appendChild(opt);
}});
trainSel.appendChild(rfrGroup);
trainSel.appendChild(metroGroup);
trainSel.appendChild(sncftGroup);

const cv=document.getElementById('c'),ctx=cv.getContext('2d');
let W,H,dpr=devicePixelRatio||1;
let minX=1e9,maxX=-1e9,minY=1e9,maxY=-1e9;
DATA.forEach(([c,p])=>p.forEach(([x,y])=>{{minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y)}}));
const midLat=(minY+maxY)/2,kx=Math.cos(midLat*Math.PI/180);

// projected coords (equirectangular w/ cos correction), y up
const P=DATA.map(([c,p])=>[c,p.map(([x,y])=>[x*kx,-y])]);
const bx0=minX*kx,bx1=maxX*kx,by0=-maxY,by1=-minY;
let s=1,tx=0,ty=0;

// Projected train routes
const PROJ_ROUTES={{}};
for(const [id,r] of Object.entries(TRAIN_ROUTES)){{
  PROJ_ROUTES[id]={{
    ...r,
    projPts: r.pts.map(([x,y])=>[x*kx,-y]),
    projStops: r.stops.map(([name,x,y])=>[name,x*kx,-y])
  }};
}}

let activeRouteId=null;

function fit(bbox){{
  W=innerWidth;H=innerHeight;cv.width=W*dpr;cv.height=H*dpr;
  const b=bbox||[bx0,bx1,by0,by1];
  const bw=b[1]-b[0],bh=b[3]-b[2];
  s=Math.min(W/bw,H/bh)*0.85;
  tx=(W-bw*s)/2-b[0]*s;
  ty=(H-bh*s)/2-b[2]*s;
  draw();
}}

trainSel.onchange=e=>{{
  activeRouteId=e.target.value||null;
  const rInfo=document.getElementById('routeInfo');
  if(!activeRouteId){{
    rInfo.style.display='none';
    fit();
    return;
  }}
  const r=PROJ_ROUTES[activeRouteId];
  rInfo.style.display='block';
  document.getElementById('rBadge').textContent=r.id.toUpperCase();
  document.getElementById('rTitle').textContent=r.name;
  document.getElementById('rDetails').textContent=`${{r.stops.length}} stations • ${{r.pts.length}} route points`;
  const stList=document.getElementById('rStops');
  stList.innerHTML='';
  r.stops.forEach(([name],i)=>{{
    const li=document.createElement('li');
    li.textContent=`${{i+1}}. ${{name}}`;
    stList.appendChild(li);
  }});

  // Compute bbox for active route
  let rx0=1e9,rx1=-1e9,ry0=1e9,ry1=-1e9;
  r.projPts.forEach(([x,y])=>{{rx0=Math.min(rx0,x);rx1=Math.max(rx1,x);ry0=Math.min(ry0,y);ry1=Math.max(ry1,y)}});
  const padX=(rx1-rx0)*0.15||0.02,padY=(ry1-ry0)*0.15||0.02;
  fit([rx0-padX,rx1+padX,ry0-padY,ry1+padY]);
}};

function draw(){{
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.fillStyle='#0b0f14';
  ctx.fillRect(0,0,W,H);
  ctx.lineCap='round';ctx.lineJoin='round';

  // Draw background rail network from rail.geojson
  const order=[6,3,2,1,5,4,0];
  for(const k of order){{
    if(!show[k])continue;
    ctx.strokeStyle=CATS[k][1];
    ctx.lineWidth=Math.max(CATS[k][2],CATS[k][2]*Math.min(3,Math.sqrt(s/fit.s0)));
    ctx.beginPath();
    for(const [c,p] of P){{
      if(c!==k)continue;
      for(let i=0;i<p.length;i++){{
        const x=p[i][0]*s+tx,y=p[i][1]*s+ty;
        i?ctx.lineTo(x,y):ctx.moveTo(x,y);
      }}
    }}
    ctx.stroke();
  }}

  // Draw active selected transit line on top
  if(activeRouteId && PROJ_ROUTES[activeRouteId]){{
    const r=PROJ_ROUTES[activeRouteId];
    const pts=r.projPts;
    
    // Glowing casing
    ctx.strokeStyle='rgba(255,255,255,0.75)';
    ctx.lineWidth=8;
    ctx.beginPath();
    for(let i=0;i<pts.length;i++){{
      const x=pts[i][0]*s+tx,y=pts[i][1]*s+ty;
      i?ctx.lineTo(x,y):ctx.moveTo(x,y);
    }}
    ctx.stroke();

    // Vibrant main route line
    ctx.strokeStyle=r.color||'#00e5ff';
    ctx.lineWidth=4.8;
    ctx.beginPath();
    for(let i=0;i<pts.length;i++){{
      const x=pts[i][0]*s+tx,y=pts[i][1]*s+ty;
      i?ctx.lineTo(x,y):ctx.moveTo(x,y);
    }}
    ctx.stroke();

    // Draw Stations
    r.projStops.forEach(([name,sx,sy],idx)=>{{
      const x=sx*s+tx,y=sy*s+ty;
      const isTerminus = idx===0 || idx===r.projStops.length-1;

      // Outer ring
      ctx.fillStyle='#ffffff';
      ctx.beginPath();
      ctx.arc(x,y,isTerminus?7:5,0,Math.PI*2);
      ctx.fill();

      // Inner dot
      ctx.fillStyle=isTerminus?'#ef4444':(r.color||'#00e5ff');
      ctx.beginPath();
      ctx.arc(x,y,isTerminus?4.5:3,0,Math.PI*2);
      ctx.fill();

      // Station label
      if(s>120000||r.projStops.length<=15){{
        ctx.font='bold 11px system-ui,sans-serif';
        ctx.fillStyle='#0f172a';
        ctx.fillText(`${{idx+1}}. ${{name}}`,x+9,y+4);
        ctx.fillStyle='#ffffff';
        ctx.fillText(`${{idx+1}}. ${{name}}`,x+8,y+3);
      }}
    }});
  }}
}}

// gestures
let pts=new Map(),last=null;
cv.addEventListener('pointerdown',e=>{{cv.setPointerCapture(e.pointerId);pts.set(e.pointerId,[e.clientX,e.clientY]);last=null}});
cv.addEventListener('pointerup',e=>{{pts.delete(e.pointerId);last=null}});
cv.addEventListener('pointercancel',e=>{{pts.delete(e.pointerId);last=null}});
cv.addEventListener('pointermove',e=>{{
  if(!pts.has(e.pointerId))return;
  const old=[...pts.values()];pts.set(e.pointerId,[e.clientX,e.clientY]);const cur=[...pts.values()];
  if(cur.length===1){{tx+=cur[0][0]-old[0][0];ty+=cur[0][1]-old[0][1];draw()}}
  else if(cur.length>=2){{
    const d0=Math.hypot(old[0][0]-old[1][0],old[0][1]-old[1][1]),d1=Math.hypot(cur[0][0]-cur[1][0],cur[0][1]-cur[1][1]);
    const cx=(cur[0][0]+cur[1][0])/2,cy=(cur[0][1]+cur[1][1])/2,ocx=(old[0][0]+old[1][0])/2,ocy=(old[0][1]+old[1][1])/2;
    if(d0>0){{const f=d1/d0;tx=cx-(ocx-tx)*f;ty=cy-(ocy-ty)*f;s*=f}}draw()
  }}
}});
cv.addEventListener('wheel',e=>{{e.preventDefault();const f=e.deltaY<0?1.2:1/1.2;tx=e.clientX-(e.clientX-tx)*f;ty=e.clientY-(e.clientY-ty)*f;s*=f;draw()}},{{passive:false}});
document.getElementById('btn').onclick=()=>{{trainSel.value='';activeRouteId=null;document.getElementById('routeInfo').style.display='none';fit()}};
addEventListener('resize',()=>fit());
fit();fit.s0=s;draw();
</script></body></html>'''

with open('rail_map.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("rail_map.html updated successfully with all 39 lines categorized!")

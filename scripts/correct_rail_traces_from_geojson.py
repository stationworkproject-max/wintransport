import argparse, heapq, json, math
from collections import defaultdict
from pathlib import Path

def hav(a,b,c,d):
    r=6371000.0
    p1,p2=math.radians(a),math.radians(c)
    dp,dl=math.radians(c-a),math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.atan2(math.sqrt(x),math.sqrt(1-x))

def add(adj,u,v):
    if u==v:return
    w=hav(u[0],u[1],v[0],v[1]); adj[u].append((v,w)); adj[v].append((u,w))

def load_lines(p):
    t=Path(p).read_text(encoding='utf-8'); k='export const STATIC_LINES = '
    i=t.find(k)
    if i<0: raise RuntimeError('STATIC_LINES not found')
    s=t[i+len(k):].strip(); s=s[:-1].strip() if s.endswith(';') else s
    return json.loads(s)

def rail_graph(path):
    d=json.loads(Path(path).read_text(encoding='utf-8')); adj=defaultdict(list); eps=[]
    for f in d.get('features',[]):
        g=(f or {}).get('geometry') or {}; t=g.get('type'); c=g.get('coordinates') or []
        ls=[c] if t=='LineString' else (c if t=='MultiLineString' else [])
        for l in ls:
            if len(l)<2: continue
            pts=[(round(float(p[1]),7),round(float(p[0]),7)) for p in l]
            eps += [pts[0],pts[-1]]
            for i in range(len(pts)-1): add(adj,pts[i],pts[i+1])
    gs=0.005; grid=defaultdict(list)
    for n in adj: grid[(int(n[0]/gs),int(n[1]/gs))].append(n)
    for e in eps:
        gx,gy=int(e[0]/gs),int(e[1]/gs)
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for o in grid.get((gx+dx,gy+dy),[]):
                    if e!=o and hav(e[0],e[1],o[0],o[1])<=35.0: add(adj,e,o)
    return adj

def mkgrid(nodes,gs=0.01):
    g=defaultdict(list)
    for n in nodes: g[(int(n[0]/gs),int(n[1]/gs))].append(n)
    return g

def nearest(lat,lon,nodes,grid,gs=0.01):
    gx,gy=int(lat/gs),int(lon/gs); best=None; bd=10**18
    for r in (1,2,3,4):
        ok=False
        for dx in range(-r,r+1):
            for dy in range(-r,r+1):
                for n in grid.get((gx+dx,gy+dy),[]):
                    d=hav(lat,lon,n[0],n[1])
                    if d<bd: bd,best=d,n; ok=True
        if ok and bd<=10000: return best,bd
    for n in nodes:
        d=hav(lat,lon,n[0],n[1])
        if d<bd: bd,best=d,n
    return best,bd

def astar(adj,s,t,cache):
    if s==t: return [s]
    if (s,t) in cache: return cache[(s,t)]
    if (t,s) in cache: return list(reversed(cache[(t,s)]))
    q=[(0.0,0.0,s)]; prev={}; g={s:0.0}; seen=set()
    while q:
        _,cd,u=heapq.heappop(q)
        if u in seen: continue
        if u==t:
            p=[u]
            while u in prev: u=prev[u]; p.append(u)
            p=list(reversed(p)); cache[(s,t)]=p; return p
        seen.add(u)
        for v,w in adj.get(u,[]):
            if v in seen: continue
            nd=cd+w
            if nd<g.get(v,1e30):
                g[v]=nd; prev[v]=u
                heapq.heappush(q,(nd+hav(v[0],v[1],t[0],t[1]),nd,v))
    cache[(s,t)]=None; return None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--geojson',required=True)
    ap.add_argument('--project-root',default=str(Path(__file__).resolve().parents[1])); a=ap.parse_args()
    pr=Path(a.project_root); st=pr/'src'/'data'/'staticTransit.js'; shp=pr/'src'/'data'/'transitShapes.json'
    bkp=pr/'src'/'data'/'transitShapes.rail-backup.json'
    lines=load_lines(st)
    ts=json.loads(shp.read_text(encoding='utf-8'))
    bkp.write_text(json.dumps(ts,ensure_ascii=False),encoding='utf-8')
    adj=rail_graph(a.geojson); nodes=list(adj.keys()); grid=mkgrid(nodes); cache={}
    rails=[l for l in lines if l.get('type_id') in {'metro','tgm','rfr','train'}]
    ok=[]; fail=[]
    for l in rails:
        lid=l['id']; stops=l.get('stops') or []
        if len(stops)<2: fail.append((lid,'few-stops')); continue
        ns=[]; bad=None
        for s in stops:
            n,d=nearest(s['lat'],s['lon'],nodes,grid)
            if not n or d>5000: bad=f"{s.get('name','?')}:{d:.1f}m"; break
            ns.append(n)
        if bad: fail.append((lid,'far-stop:'+bad)); continue
        track=[]; bad=None
        for i in range(len(ns)-1):
            p=astar(adj,ns[i],ns[i+1],cache)
            if not p: bad=f'leg-{i}'; break
            pts=[[round(x[0],6),round(x[1],6)] for x in p]
            track.extend(pts if not track else pts[1:])
        if bad or len(track)<2: fail.append((lid,bad or 'empty')); continue
        rev=list(reversed(track))
        ts[lid]=track; ts[f'{lid}_0']=track; ts[f'{lid}_1']=rev; ts[f'{lid}_aller']=track; ts[f'{lid}_retour']=rev
        ok.append((lid,len(track)))
    shp.write_text(json.dumps(ts,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Rail graph nodes: {len(nodes)}')
    print(f'Rail lines targeted: {len(rails)}')
    print(f'Updated: {len(ok)} | Failed: {len(fail)}')
    for lid,n in ok: print(f'  OK   {lid:12s} {n:6d} pts')
    for lid,r in fail: print(f'  FAIL {lid:12s} {r}')

if __name__=='__main__':
    main()
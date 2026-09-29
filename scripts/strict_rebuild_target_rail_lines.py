import argparse
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

TARGET_LINES = ['metro_50', 'metro_55', 'rfr_46', 'rfr_47']


def haversine(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def add_edge(adj, u, v):
    if u == v:
        return
    d = haversine(u[0], u[1], v[0], v[1])
    adj[u].append((v, d))
    adj[v].append((u, d))


def build_graph(geojson_path):
    data = json.loads(Path(geojson_path).read_text(encoding='utf-8'))
    adj = defaultdict(list)
    endpoints = []

    for feat in data.get('features', []):
        geom = (feat or {}).get('geometry') or {}
        typ = geom.get('type')
        coords = geom.get('coordinates') or []

        lines = [coords] if typ == 'LineString' else (coords if typ == 'MultiLineString' else [])
        for line in lines:
            if len(line) < 2:
                continue
            pts = [(round(float(p[1]), 7), round(float(p[0]), 7)) for p in line]
            endpoints.append(pts[0])
            endpoints.append(pts[-1])
            for i in range(len(pts) - 1):
                add_edge(adj, pts[i], pts[i + 1])

    # Bridge tiny gaps only (segmentation artifacts)
    gs = 0.005
    grid = defaultdict(list)
    for n in adj.keys():
        grid[(int(n[0] / gs), int(n[1] / gs))].append(n)

    for ep in endpoints:
        gx, gy = int(ep[0] / gs), int(ep[1] / gs)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for other in grid.get((gx + dx, gy + dy), []):
                    if ep == other:
                        continue
                    d = haversine(ep[0], ep[1], other[0], other[1])
                    if 0 < d <= 25.0:
                        add_edge(adj, ep, other)

    return adj


def build_grid(nodes, cell_size=0.0025):
    g = defaultdict(list)
    for n in nodes:
        g[(int(n[0] / cell_size), int(n[1] / cell_size))].append(n)
    return g


def nearest_node(lat, lon, nodes, grid, cell_size=0.0025):
    gx, gy = int(lat / cell_size), int(lon / cell_size)
    best = None
    best_d = float('inf')

    for r in (1, 2, 3, 4, 5, 6):
        found = False
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for n in grid.get((gx + dx, gy + dy), []):
                    d = haversine(lat, lon, n[0], n[1])
                    if d < best_d:
                        best = n
                        best_d = d
                        found = True
        if found:
            return best, best_d

    for n in nodes:
        d = haversine(lat, lon, n[0], n[1])
        if d < best_d:
            best = n
            best_d = d
    return best, best_d


def shortest_path(adj, start, goal, cache):
    key = (start, goal)
    rkey = (goal, start)
    if key in cache:
        return cache[key]
    if rkey in cache:
        p, c = cache[rkey]
        return list(reversed(p)), c

    if start == goal:
        cache[key] = ([start], 0.0)
        return [start], 0.0

    pq = [(0.0, 0.0, start)]
    prev = {}
    gscore = {start: 0.0}
    visited = set()

    while pq:
        _, cost, u = heapq.heappop(pq)
        if u in visited:
            continue
        if u == goal:
            path = [u]
            cur = u
            while cur in prev:
                cur = prev[cur]
                path.append(cur)
            path.reverse()
            cache[key] = (path, cost)
            return path, cost

        visited.add(u)

        for v, w in adj.get(u, []):
            if v in visited:
                continue
            nd = cost + w
            if nd < gscore.get(v, float('inf')):
                gscore[v] = nd
                prev[v] = u
                h = haversine(v[0], v[1], goal[0], goal[1])
                heapq.heappush(pq, (nd + h, nd, v))

    cache[key] = (None, float('inf'))
    return None, float('inf')


def dedupe_nodes(nodes):
    out = []
    last = None
    for n in nodes:
        if n != last:
            out.append(n)
            last = n
    return out


def max_segment_m(shape):
    if not shape or len(shape) < 2:
        return 0.0
    m = 0.0
    for i in range(len(shape) - 1):
        a = shape[i]
        b = shape[i + 1]
        d = haversine(a[0], a[1], b[0], b[1])
        if d > m:
            m = d
    return m


def rebuild_line_from_guide(guide_shape, nodes, grid, adj, route_cache):
    if not guide_shape or len(guide_shape) < 2:
        return None, 'missing-guide'

    snapped = []
    for p in guide_shape:
        lat, lon = float(p[0]), float(p[1])
        n, d = nearest_node(lat, lon, nodes, grid)
        if n is None or d > 120.0:
            # strict: if guide point is too far from rails, reject to avoid fake jumps
            return None, f'guide-point-too-far:{d:.1f}m'
        snapped.append(n)

    snapped = dedupe_nodes(snapped)
    if len(snapped) < 2:
        return None, 'too-few-snapped-nodes'

    track_nodes = []
    for i in range(len(snapped) - 1):
        leg, _ = shortest_path(adj, snapped[i], snapped[i + 1], route_cache)
        if not leg:
            return None, f'unroutable-leg-{i}'
        if not track_nodes:
            track_nodes.extend(leg)
        else:
            track_nodes.extend(leg[1:])

    track = [[round(n[0], 6), round(n[1], 6)] for n in dedupe_nodes(track_nodes)]
    if len(track) < 2:
        return None, 'empty-track'

    return track, None


def main():
    parser = argparse.ArgumentParser(description='Strict, no-jump rebuild for key rail lines')
    parser.add_argument('--geojson', required=True)
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()

    root = Path(args.project_root)
    shapes_path = root / 'src' / 'data' / 'transitShapes.json'
    backup_path = root / 'src' / 'data' / 'transitShapes.rail-backup.json'

    shapes = json.loads(shapes_path.read_text(encoding='utf-8'))
    guide_shapes = json.loads(backup_path.read_text(encoding='utf-8')) if backup_path.exists() else dict(shapes)

    adj = build_graph(args.geojson)
    nodes = list(adj.keys())
    grid = build_grid(nodes)
    route_cache = {}

    ok = []
    fail = []

    for lid in TARGET_LINES:
        guide = guide_shapes.get(f'{lid}_0') or guide_shapes.get(lid)
        if not isinstance(guide, list) or len(guide) < 2:
            fail.append((lid, 'no-guide-shape'))
            continue

        rebuilt, err = rebuild_line_from_guide(guide, nodes, grid, adj, route_cache)
        if err:
            fail.append((lid, err))
            continue

        rev = list(reversed(rebuilt))
        shapes[lid] = rebuilt
        shapes[f'{lid}_0'] = rebuilt
        shapes[f'{lid}_1'] = rev
        shapes[f'{lid}_aller'] = rebuilt
        shapes[f'{lid}_retour'] = rev
        ok.append((lid, len(rebuilt), round(max_segment_m(rebuilt), 1)))

    shapes_path.write_text(json.dumps(shapes, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    print(f'Graph nodes: {len(nodes)}')
    print(f'Updated: {len(ok)} | Failed: {len(fail)}')
    for lid, pts, max_seg in ok:
        print(f'  OK   {lid:10s} {pts:5d} pts  maxSeg={max_seg:6.1f}m')
    for lid, reason in fail:
        print(f'  FAIL {lid:10s} {reason}')


if __name__ == '__main__':
    main()
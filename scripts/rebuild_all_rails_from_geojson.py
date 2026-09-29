import argparse
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

RAIL_TYPES = {'metro', 'tgm', 'rfr', 'train'}


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


def parse_static_lines(path):
    text = Path(path).read_text(encoding='utf-8')
    prefix = 'export const STATIC_LINES = '
    idx = text.find(prefix)
    if idx < 0:
        raise RuntimeError('STATIC_LINES not found in staticTransit.js')
    raw = text[idx + len(prefix):].strip()
    if raw.endswith(';'):
        raw = raw[:-1].strip()
    return json.loads(raw)


def build_rail_graph(geojson_path):
    data = json.loads(Path(geojson_path).read_text(encoding='utf-8'))
    adj = defaultdict(list)
    endpoints = []

    for feat in data.get('features', []):
        geom = (feat or {}).get('geometry') or {}
        gtype = geom.get('type')
        coords = geom.get('coordinates') or []

        lines = [coords] if gtype == 'LineString' else (coords if gtype == 'MultiLineString' else [])
        for line in lines:
            if len(line) < 2:
                continue
            pts = [(round(float(p[1]), 7), round(float(p[0]), 7)) for p in line]
            endpoints.append(pts[0])
            endpoints.append(pts[-1])
            for i in range(len(pts) - 1):
                add_edge(adj, pts[i], pts[i + 1])

    # Bridge tiny gaps only (OSM splitting artifacts)
    cell = 0.005
    grid = defaultdict(list)
    for n in adj.keys():
        grid[(int(n[0] / cell), int(n[1] / cell))].append(n)

    for ep in endpoints:
        gx, gy = int(ep[0] / cell), int(ep[1] / cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for other in grid.get((gx + dx, gy + dy), []):
                    if ep == other:
                        continue
                    d = haversine(ep[0], ep[1], other[0], other[1])
                    if 0 < d <= 25.0:
                        add_edge(adj, ep, other)

    return adj


def build_grid(nodes, cell=0.0025):
    g = defaultdict(list)
    for n in nodes:
        g[(int(n[0] / cell), int(n[1] / cell))].append(n)
    return g


def nearest_node(lat, lon, nodes, grid, cell=0.0025):
    gx, gy = int(lat / cell), int(lon / cell)
    best, best_d = None, float('inf')

    for radius in (1, 2, 3, 4, 5, 6):
        found = False
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for n in grid.get((gx + dx, gy + dy), []):
                    d = haversine(lat, lon, n[0], n[1])
                    if d < best_d:
                        best, best_d = n, d
                        found = True
        if found:
            return best, best_d

    for n in nodes:
        d = haversine(lat, lon, n[0], n[1])
        if d < best_d:
            best, best_d = n, d
    return best, best_d


def shortest_path(adj, start, goal, cache):
    key = (start, goal)
    rkey = (goal, start)
    if key in cache:
        return cache[key]
    if rkey in cache:
        p, cost = cache[rkey]
        return list(reversed(p)), cost

    if start == goal:
        cache[key] = ([start], 0.0)
        return [start], 0.0

    pq = [(0.0, 0.0, start)]
    prev = {}
    g = {start: 0.0}
    seen = set()

    while pq:
        _, cur_cost, u = heapq.heappop(pq)
        if u in seen:
            continue
        if u == goal:
            path = [u]
            cur = u
            while cur in prev:
                cur = prev[cur]
                path.append(cur)
            path.reverse()
            cache[key] = (path, cur_cost)
            return path, cur_cost

        seen.add(u)
        for v, w in adj.get(u, []):
            if v in seen:
                continue
            nd = cur_cost + w
            if nd < g.get(v, float('inf')):
                g[v] = nd
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


def max_seg_m(shape):
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


def build_anchor_points(guide_shape):
    if not guide_shape:
        return []
    n = len(guide_shape)
    if n <= 1200:
        step = 1
    elif n <= 3000:
        step = 2
    else:
        step = 3

    anchors = [guide_shape[0]]
    for i in range(step, n - 1, step):
        anchors.append(guide_shape[i])
    anchors.append(guide_shape[-1])
    return anchors


def rebuild_line(guide_shape, adj, neighbor_sets, nodes, grid, cache):
    anchors = build_anchor_points(guide_shape)
    if len(anchors) < 2:
        return None, 'not-enough-anchors'

    snapped = []
    far_points = 0
    for p in anchors:
        lat, lon = float(p[0]), float(p[1])
        n, d = nearest_node(lat, lon, nodes, grid)
        if n is None:
            return None, 'no-nearest-node'
        if d > 180.0:
            far_points += 1
        snapped.append(n)

    if far_points > max(3, len(anchors) // 20):
        return None, f'too-many-far-anchors:{far_points}'

    snapped = dedupe_nodes(snapped)
    if len(snapped) < 2:
        return None, 'snapped-collapsed'

    route_nodes = [snapped[0]]
    for i in range(1, len(snapped)):
        u = route_nodes[-1]
        v = snapped[i]
        if v == u:
            continue

        if v in neighbor_sets.get(u, set()):
            route_nodes.append(v)
            continue

        leg, _ = shortest_path(adj, u, v, cache)
        if not leg:
            return None, f'unroutable-leg-{i-1}'

        route_nodes.extend(leg[1:])

    route_nodes = dedupe_nodes(route_nodes)
    shape = [[round(n[0], 6), round(n[1], 6)] for n in route_nodes]
    if len(shape) < 2:
        return None, 'empty-shape'

    return shape, None


def main():
    parser = argparse.ArgumentParser(description='Rebuild all rail lines from provided rail geojson (strict)')
    parser.add_argument('--geojson', required=True)
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()

    root = Path(args.project_root)
    static_path = root / 'src' / 'data' / 'staticTransit.js'
    shapes_path = root / 'src' / 'data' / 'transitShapes.json'
    backup_path = root / 'src' / 'data' / 'transitShapes.rail-backup.json'

    lines = parse_static_lines(static_path)
    shapes = json.loads(shapes_path.read_text(encoding='utf-8'))
    guide_shapes = json.loads(backup_path.read_text(encoding='utf-8')) if backup_path.exists() else dict(shapes)

    adj = build_rail_graph(args.geojson)
    nodes = list(adj.keys())
    grid = build_grid(nodes)

    neighbor_sets = {u: {v for v, _ in adj[u]} for u in adj.keys()}
    cache = {}

    rail_lines = [line for line in lines if line.get('type_id') in RAIL_TYPES]
    ok = []
    fail = []

    for line in rail_lines:
        lid = line['id']
        guide = guide_shapes.get(f'{lid}_0') or guide_shapes.get(lid) or shapes.get(lid)
        if not isinstance(guide, list) or len(guide) < 2:
            fail.append((lid, 'missing-guide-shape'))
            continue

        rebuilt, err = rebuild_line(guide, adj, neighbor_sets, nodes, grid, cache)
        if err:
            fail.append((lid, err))
            continue

        rev = list(reversed(rebuilt))
        shapes[lid] = rebuilt
        shapes[f'{lid}_0'] = rebuilt
        shapes[f'{lid}_1'] = rev
        shapes[f'{lid}_aller'] = rebuilt
        shapes[f'{lid}_retour'] = rev
        ok.append((lid, len(rebuilt), round(max_seg_m(rebuilt), 1)))

    shapes_path.write_text(json.dumps(shapes, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    print(f'Graph nodes: {len(nodes)}')
    print(f'Rail lines targeted: {len(rail_lines)}')
    print(f'Updated: {len(ok)} | Failed: {len(fail)}')
    for lid, pts, max_seg in ok:
        print(f'  OK   {lid:12s} {pts:5d} pts  maxSeg={max_seg:6.1f}m')
    for lid, reason in fail:
        print(f'  FAIL {lid:12s} {reason}')


if __name__ == '__main__':
    main()
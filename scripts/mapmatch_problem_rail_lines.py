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

    for feat in data.get('features', []):
        geom = (feat or {}).get('geometry') or {}
        gtype = geom.get('type')
        coords = geom.get('coordinates') or []

        lines = [coords] if gtype == 'LineString' else (coords if gtype == 'MultiLineString' else [])
        for line in lines:
            if len(line) < 2:
                continue
            pts = [(round(float(p[1]), 7), round(float(p[0]), 7)) for p in line]
            for i in range(len(pts) - 1):
                add_edge(adj, pts[i], pts[i + 1])

    return adj


def build_grid(nodes, cell_size=0.005):
    grid = defaultdict(list)
    for n in nodes:
        grid[(int(n[0] / cell_size), int(n[1] / cell_size))].append(n)
    return grid


def nearest_node(lat, lon, nodes, grid, cell_size=0.005):
    gx, gy = int(lat / cell_size), int(lon / cell_size)
    best = None
    best_d = float('inf')

    for radius in (1, 2, 3, 4, 5):
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


def astar(adj, start, goal, cache):
    key = (start, goal)
    rev = (goal, start)
    if key in cache:
        return cache[key]
    if rev in cache:
        path, cost = cache[rev]
        return list(reversed(path)), cost

    if start == goal:
        cache[key] = ([start], 0.0)
        return [start], 0.0

    pq = [(0.0, 0.0, start)]
    prev = {}
    gscore = {start: 0.0}
    visited = set()

    while pq:
        _, cur_g, u = heapq.heappop(pq)
        if u in visited:
            continue
        if u == goal:
            path = [u]
            cur = u
            while cur in prev:
                cur = prev[cur]
                path.append(cur)
            path.reverse()
            cache[key] = (path, cur_g)
            return path, cur_g

        visited.add(u)
        for v, w in adj.get(u, []):
            if v in visited:
                continue
            ng = cur_g + w
            if ng < gscore.get(v, float('inf')):
                gscore[v] = ng
                prev[v] = u
                h = haversine(v[0], v[1], goal[0], goal[1])
                heapq.heappush(pq, (ng + h, ng, v))

    cache[key] = (None, float('inf'))
    return None, float('inf')


def polyline_length_km(shape):
    if not shape or len(shape) < 2:
        return 0.0
    total = 0.0
    for i in range(len(shape) - 1):
        a = shape[i]
        b = shape[i + 1]
        total += haversine(a[0], a[1], b[0], b[1])
    return total / 1000.0


def downsample_anchors(points, max_anchors=260):
    if len(points) <= 2:
        return points
    step = max(1, len(points) // max_anchors)
    anchors = [points[0]]
    for i in range(step, len(points) - 1, step):
        anchors.append(points[i])
    anchors.append(points[-1])

    dedup = []
    last = None
    for p in anchors:
        key = (round(float(p[0]), 6), round(float(p[1]), 6))
        if key != last:
            dedup.append([float(p[0]), float(p[1])])
            last = key
    return dedup


def mapmatch_line(guide_shape, nodes, grid, adj, route_cache):
    if not guide_shape or len(guide_shape) < 2:
        return None, 'no-guide-shape'

    anchors = downsample_anchors(guide_shape)
    snapped = []
    for p in anchors:
        n, d = nearest_node(float(p[0]), float(p[1]), nodes, grid)
        if n is None or d > 400:
            return None, f'anchor-too-far:{d:.1f}m'
        if not snapped or snapped[-1] != n:
            snapped.append(n)

    if len(snapped) < 2:
        return None, 'too-few-snapped-anchors'

    track = []
    for i in range(len(snapped) - 1):
        leg, _ = astar(adj, snapped[i], snapped[i + 1], route_cache)
        if not leg:
            return None, f'unroutable-leg-{i}'
        pts = [[round(x[0], 6), round(x[1], 6)] for x in leg]
        if not track:
            track.extend(pts)
        else:
            track.extend(pts[1:])

    if len(track) < 2:
        return None, 'empty-track'

    return track, None


def main():
    parser = argparse.ArgumentParser(description='Map-match selected rail lines to rail geojson')
    parser.add_argument('--geojson', required=True)
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()

    root = Path(args.project_root)
    shapes_path = root / 'src' / 'data' / 'transitShapes.json'
    backup_path = root / 'src' / 'data' / 'transitShapes.rail-backup.json'

    shapes = json.loads(shapes_path.read_text(encoding='utf-8'))
    guide = json.loads(backup_path.read_text(encoding='utf-8')) if backup_path.exists() else dict(shapes)

    adj = build_graph(args.geojson)
    nodes = list(adj.keys())
    grid = build_grid(nodes)
    route_cache = {}

    ok = []
    fail = []

    for lid in TARGET_LINES:
        source = guide.get(f'{lid}_0') or guide.get(lid) or shapes.get(lid)
        shape, err = mapmatch_line(source, nodes, grid, adj, route_cache)
        if err:
            fail.append((lid, err))
            continue

        rev = list(reversed(shape))
        shapes[lid] = shape
        shapes[f'{lid}_0'] = shape
        shapes[f'{lid}_1'] = rev
        shapes[f'{lid}_aller'] = shape
        shapes[f'{lid}_retour'] = rev
        ok.append((lid, len(shape), polyline_length_km(shape)))

    shapes_path.write_text(json.dumps(shapes, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    print(f'Graph nodes: {len(nodes)}')
    print(f'Updated: {len(ok)} | Failed: {len(fail)}')
    for lid, pts, km in ok:
        print(f'  OK   {lid:10s} {pts:5d} pts  {km:6.2f} km')
    for lid, reason in fail:
        print(f'  FAIL {lid:10s} {reason}')


if __name__ == '__main__':
    main()
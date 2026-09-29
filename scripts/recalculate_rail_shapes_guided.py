import argparse
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path


def haversine(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
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


def load_static_lines(path):
    text = Path(path).read_text(encoding='utf-8')
    prefix = 'export const STATIC_LINES = '
    idx = text.find(prefix)
    if idx < 0:
        raise RuntimeError('STATIC_LINES not found')
    raw = text[idx + len(prefix):].strip()
    if raw.endswith(';'):
        raw = raw[:-1].strip()
    return json.loads(raw)


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

    # bridge tiny segmentation gaps around endpoints
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
                    if 0 < d <= 35.0:
                        add_edge(adj, ep, other)

    return adj


def build_node_grid(nodes, cell_size=0.01):
    grid = defaultdict(list)
    for n in nodes:
        grid[(int(n[0] / cell_size), int(n[1] / cell_size))].append(n)
    return grid


def nearest_node(lat, lon, nodes, grid, cell_size=0.01):
    gx, gy = int(lat / cell_size), int(lon / cell_size)
    best, best_d = None, float('inf')

    for r in (1, 2, 3, 4):
        found = False
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for n in grid.get((gx + dx, gy + dy), []):
                    d = haversine(lat, lon, n[0], n[1])
                    if d < best_d:
                        best, best_d = n, d
                        found = True
        if found and best_d <= 2000:
            return best, best_d

    for n in nodes:
        d = haversine(lat, lon, n[0], n[1])
        if d < best_d:
            best, best_d = n, d
    return best, best_d


def build_guide_grid(guide_latlngs, cell_size=0.01):
    if not guide_latlngs:
        return None
    grid = defaultdict(list)
    for lat, lon in guide_latlngs:
        grid[(int(lat / cell_size), int(lon / cell_size))].append((float(lat), float(lon)))
    return grid


def nearest_guide_distance(lat, lon, guide_grid, cell_size=0.01):
    if guide_grid is None:
        return 0.0
    gx, gy = int(lat / cell_size), int(lon / cell_size)
    best_d = float('inf')

    for r in (1, 2, 3, 4, 5):
        found = False
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for p in guide_grid.get((gx + dx, gy + dy), []):
                    d = haversine(lat, lon, p[0], p[1])
                    if d < best_d:
                        best_d = d
                        found = True
        if found:
            return best_d

    # no nearby guide points -> heavy penalty zone
    return 500.0


def guided_astar(adj, start, goal, guide_grid, path_cache, guide_cache, penalty_factor=2.8):
    cache_key = (start, goal, id(guide_grid))
    if cache_key in path_cache:
        return path_cache[cache_key]

    if start == goal:
        path_cache[cache_key] = ([start], 0.0)
        return [start], 0.0

    pq = [(0.0, 0.0, start)]
    prev = {}
    gscore = {start: 0.0}
    visited = set()

    while pq:
        _, cost_so_far, u = heapq.heappop(pq)
        if u in visited:
            continue
        if u == goal:
            path = [u]
            cur = u
            while cur in prev:
                cur = prev[cur]
                path.append(cur)
            path.reverse()
            path_cache[cache_key] = (path, cost_so_far)
            return path, cost_so_far

        visited.add(u)

        for v, edge_len in adj.get(u, []):
            if v in visited:
                continue

            mid = ((u[0] + v[0]) / 2.0, (u[1] + v[1]) / 2.0)
            mid_key = (round(mid[0], 6), round(mid[1], 6), id(guide_grid))
            if mid_key in guide_cache:
                guide_d = guide_cache[mid_key]
            else:
                guide_d = nearest_guide_distance(mid[0], mid[1], guide_grid)
                guide_cache[mid_key] = guide_d

            # cap penalty influence to avoid blocking genuine junction transitions
            penalty = min(220.0, guide_d) * penalty_factor
            step = edge_len + penalty

            new_cost = cost_so_far + step
            if new_cost < gscore.get(v, float('inf')):
                gscore[v] = new_cost
                prev[v] = u
                # straight-line heuristic remains admissible lower bound (penalties are >=0)
                h = haversine(v[0], v[1], goal[0], goal[1])
                heapq.heappush(pq, (new_cost + h, new_cost, v))

    path_cache[cache_key] = (None, float('inf'))
    return None, float('inf')


def main():
    parser = argparse.ArgumentParser(description='Recalculate rail lines with line-guided routing from rail geojson')
    parser.add_argument('--geojson', required=True)
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()

    root = Path(args.project_root)
    static_path = root / 'src' / 'data' / 'staticTransit.js'
    shapes_path = root / 'src' / 'data' / 'transitShapes.json'
    backup_path = root / 'src' / 'data' / 'transitShapes.rail-backup.json'

    lines = load_static_lines(static_path)
    current_shapes = json.loads(shapes_path.read_text(encoding='utf-8'))
    guide_shapes = json.loads(backup_path.read_text(encoding='utf-8')) if backup_path.exists() else current_shapes

    adj = build_graph(args.geojson)
    nodes = list(adj.keys())
    node_grid = build_node_grid(nodes)

    rail_types = {'metro', 'tgm', 'rfr', 'train'}
    rail_lines = [line for line in lines if line.get('type_id') in rail_types]

    path_cache = {}
    guide_cache = {}
    ok, fail = [], []

    for line in rail_lines:
        lid = line['id']
        stops = line.get('stops') or []
        if len(stops) < 2:
            fail.append((lid, 'few-stops'))
            continue

        guide = guide_shapes.get(f'{lid}_0') or guide_shapes.get(lid) or current_shapes.get(lid)
        guide_grid = build_guide_grid(guide if isinstance(guide, list) else None)

        snapped = []
        bad = None
        for s in stops:
            n, d = nearest_node(float(s['lat']), float(s['lon']), nodes, node_grid)
            if n is None or d > 5000:
                bad = f"stop-too-far:{s.get('name','?')}:{d:.1f}m"
                break
            snapped.append(n)

        if bad:
            fail.append((lid, bad))
            continue

        track = []
        for i in range(len(snapped) - 1):
            leg, _ = guided_astar(adj, snapped[i], snapped[i + 1], guide_grid, path_cache, guide_cache)
            if not leg:
                bad = f'unroutable-leg-{i}'
                break
            pts = [[round(p[0], 6), round(p[1], 6)] for p in leg]
            if not track:
                track.extend(pts)
            else:
                track.extend(pts[1:])

        if bad or len(track) < 2:
            fail.append((lid, bad or 'empty-shape'))
            continue

        rev = list(reversed(track))
        current_shapes[lid] = track
        current_shapes[f'{lid}_0'] = track
        current_shapes[f'{lid}_1'] = rev
        current_shapes[f'{lid}_aller'] = track
        current_shapes[f'{lid}_retour'] = rev
        ok.append((lid, len(track)))

    shapes_path.write_text(json.dumps(current_shapes, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    print(f'Rail graph nodes: {len(nodes)}')
    print(f'Rail lines targeted: {len(rail_lines)}')
    print(f'Updated: {len(ok)} | Failed: {len(fail)}')
    for lid, count in ok:
        print(f'  OK   {lid:12s} {count:6d} pts')
    for lid, reason in fail:
        print(f'  FAIL {lid:12s} {reason}')


if __name__ == '__main__':
    main()
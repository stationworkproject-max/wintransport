import json
import math
import heapq
import os
import urllib.request

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def calc_bearing(p1, p2):
    lat1, lon1, lat2, lon2 = map(math.radians, [p1[0], p1[1], p2[0], p2[1]])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return round((math.degrees(math.atan2(x, y)) + 360) % 360)

# Rail Graph Singleton
RAIL_GRAPH = None

def init_rail_graph(geojson_path):
    global RAIL_GRAPH
    if RAIL_GRAPH is not None:
        return RAIL_GRAPH
    if not os.path.exists(geojson_path):
        return None
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            rw = json.load(f)
        adj = {}
        endpoints = []
        for feat in rw.get('features', []):
            geom = feat.get('geometry')
            if not geom: continue
            coords = geom.get('coordinates', [])
            t = geom.get('type')
            coords_list = [coords] if t == 'LineString' else coords if t == 'MultiLineString' else []
            for line in coords_list:
                pts = [(round(p[1], 6), round(p[0], 6)) for p in line]
                if len(pts) < 2: continue
                endpoints.append(pts[0])
                endpoints.append(pts[-1])
                for i in range(len(pts) - 1):
                    u, v = pts[i], pts[i+1]
                    d = haversine(u[0], u[1], v[0], v[1])
                    if u not in adj: adj[u] = []
                    if v not in adj: adj[v] = []
                    adj[u].append((v, d))
                    adj[v].append((u, d))

        # Spatial grid for fast nearest-node lookup and endpoint bridging
        grid_size = 0.005
        grid = {}
        for node in adj.keys():
            cell = (int(node[0] / grid_size), int(node[1] / grid_size))
            if cell not in grid: grid[cell] = []
            grid[cell].append(node)

        # Bridge rail gaps up to 45m
        for ep in endpoints:
            gx, gy = int(ep[0] / grid_size), int(ep[1] / grid_size)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for other in grid.get((gx + dx, gy + dy), []):
                        if ep != other:
                            d = haversine(ep[0], ep[1], other[0], other[1])
                            if 0 < d <= 45.0:
                                adj[ep].append((other, d))
                                adj[other].append((ep, d))

        RAIL_GRAPH = {'adj': adj, 'grid': grid, 'grid_size': grid_size}
        print(f"[Studio Rail] Initialized rail graph with {len(adj)} nodes")
        return RAIL_GRAPH
    except Exception as e:
        print(f"[Studio Rail] Failed to load rail graph: {e}")
        return None

def route_rail_leg(p1, p2, graph):
    if not graph:
        return [p1, p2]
    adj = graph['adj']
    grid = graph['grid']
    gs = graph['grid_size']

    def find_nearest(lat, lon):
        gx, gy = int(lat / gs), int(lon / gs)
        best, best_d = None, float('inf')
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for node in grid.get((gx + dx, gy + dy), []):
                    d = haversine(lat, lon, node[0], node[1])
                    if d < best_d:
                        best_d, best = d, node
        return best, best_d

    n1, d1 = find_nearest(p1[0], p1[1])
    n2, d2 = find_nearest(p2[0], p2[1])
    if not n1 or not n2 or d1 > 800 or d2 > 800:
        return [p1, p2]
    if n1 == n2:
        return [[n1[0], n1[1]]]

    pq = [(0.0, n1)]
    dist = {n1: 0.0}
    prev = {}
    while pq:
        d, u = heapq.heappop(pq)
        if u == n2:
            break
        if d > dist.get(u, float('inf')):
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, float('inf')):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))

    if n2 not in dist:
        return [p1, p2]

    path = []
    curr = n2
    while curr:
        path.append([curr[0], curr[1]])
        curr = prev.get(curr)
    path.reverse()
    return path

def route_road_leg(p1, p2, prefer_transit=False):
    # Calculate bearing from p1 to p2 to snap to the correct directional carriageway
    b = calc_bearing(p1, p2)
    direct_dist = haversine(p1[0], p1[1], p2[0], p2[1])

    def query_osrm(url):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'WinTransportStudio/2.0'})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('code') == 'Ok' and data.get('routes'):
                    r = data['routes'][0]
                    pts = [[round(c[1], 6), round(c[0], 6)] for c in r['geometry']['coordinates']]
                    return pts, r['distance']
        except Exception:
            pass
        return None, 0

    # 1. Primary: OSRM driving with strict bearing & continue_straight to forbid U-turns and wrong carriageways
    url_driving = (
        f"https://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}"
        f"?overview=full&geometries=geojson&continue_straight=true&bearings={b},50;{b},50"
    )
    pts, dist = query_osrm(url_driving)

    # 2. Check if the driving route took a detour or loop ("went to the hip and turned around")
    # A detour is detected if distance > 1.7x direct distance and difference > 200m
    detour_detected = False
    if pts and dist > 0:
        ratio = dist / max(direct_dist, 30)
        detour_m = dist - direct_dist
        if (ratio > 1.7 and detour_m > 200) or ratio > 2.5:
            detour_detected = True

    # 3. If detour detected or prefer_transit, query transit-friendly OpenStreetMap routed-bike profile
    # which allows bus corridors, pedestrian malls (Habib Bourguiba, Passage, Barcelone) and contraflow lanes
    if detour_detected or prefer_transit or not pts:
        url_transit = (
            f"https://routing.openstreetmap.de/routed-bike/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}"
            f"?overview=full&geometries=geojson"
        )
        pts_t, dist_t = query_osrm(url_transit)
        if pts_t and dist_t > 0:
            if not pts or dist_t < dist:
                pts = pts_t
                dist = dist_t

    # 4. If still no valid route or massive detour, fallback to direct points
    if not pts:
        pts = [p1, p2]

    return pts

def remove_hairpin_loops(pts, max_loop_dist=35, min_waste=120):
    """
    Detects and eliminates unwanted loops, roundabouts, or hairpin U-turns
    where the route leaves an avenue, loops around, and returns to virtually the same spot.
    """
    if len(pts) < 6:
        return pts
    result = list(pts)
    changed = True
    iterations = 0
    while changed and iterations < 6:
        changed = False
        iterations += 1
        n = len(result)
        for i in range(n - 4):
            for j in range(i + 4, min(n, i + 40)):
                d_between = haversine(result[i][0], result[i][1], result[j][0], result[j][1])
                if d_between < max_loop_dist:
                    loop_len = sum(haversine(result[k][0], result[k][1], result[k+1][0], result[k+1][1]) for k in range(i, j))
                    if loop_len > min_waste:
                        # Found a wasteful loop / hairpin: cut it out cleanly
                        result = result[:i+1] + result[j:]
                        changed = True
                        break
            if changed:
                break
    return result

def smart_route_full(points, mode='auto', network_type=None, rail_geojson_path='rail.geojson', remove_loops=True):
    if len(points) < 2:
        return points

    # Determine mode: rail vs road
    is_rail = False
    if mode == 'rail':
        is_rail = True
    elif mode in ['road', 'transit']:
        is_rail = False
    else: # auto
        if network_type in ['metro', 'tgm', 'rfr', 'train']:
            is_rail = True
        else:
            is_rail = False

    graph = None
    if is_rail:
        graph = init_rail_graph(rail_geojson_path)

    full_coords = []
    prefer_transit = (mode == 'transit')

    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        
        # Check if points are identical or virtually zero distance
        if haversine(p1[0], p1[1], p2[0], p2[1]) < 4:
            continue

        if is_rail and graph:
            leg_pts = route_rail_leg(p1, p2, graph)
        else:
            leg_pts = route_road_leg(p1, p2, prefer_transit=prefer_transit)

        if not full_coords:
            full_coords.extend(leg_pts)
        else:
            full_coords.extend(leg_pts[1:])

    # Clean redundant consecutive points
    cleaned = []
    for p in full_coords:
        if not cleaned or (cleaned[-1][0] != p[0] or cleaned[-1][1] != p[1]):
            cleaned.append(p)

    if remove_loops and not is_rail:
        cleaned = remove_hairpin_loops(cleaned)

    return cleaned if len(cleaned) >= 2 else points


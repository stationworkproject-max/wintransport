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

def route_road_chunk(chunk_points):
    """
    Routes a sequence of waypoints through OSRM driving engine.
    Follows real road network geometry, safe roundabouts, divided carriageways,
    and bridges/ramps without cutting through barriers or taking illegal shortcuts.
    """
    if len(chunk_points) < 2:
        return chunk_points

    coords_str = ';'.join(f'{p[1]:.6f},{p[0]:.6f}' for p in chunk_points)
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'WinTransportStudio/2.0'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('code') == 'Ok' and data.get('routes'):
                r = data['routes'][0]
                pts = [[round(c[1], 6), round(c[0], 6)] for c in r['geometry']['coordinates']]
                return pts
    except Exception as e:
        print(f"[OSRM] Error in road chunk: {e}")

    # Fallback to leg-by-leg if multi-point query had issues
    fallback_pts = []
    for i in range(len(chunk_points) - 1):
        p1 = chunk_points[i]
        p2 = chunk_points[i+1]
        leg_url = f"https://router.project-osrm.org/route/v1/driving/{p1[1]:.6f},{p1[0]:.6f};{p2[1]:.6f},{p2[0]:.6f}?overview=full&geometries=geojson"
        try:
            req = urllib.request.Request(leg_url, headers={'User-Agent': 'WinTransportStudio/2.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('code') == 'Ok' and data.get('routes'):
                    leg = [[round(c[1], 6), round(c[0], 6)] for c in data['routes'][0]['geometry']['coordinates']]
                    if not fallback_pts:
                        fallback_pts.extend(leg)
                    else:
                        fallback_pts.extend(leg[1:])
                    continue
        except Exception:
            pass
        if not fallback_pts:
            fallback_pts.extend([p1, p2])
        else:
            fallback_pts.append(p2)

    return fallback_pts if fallback_pts else chunk_points

def smart_route_full(points, mode='auto', network_type=None, rail_geojson_path='rail.geojson', remove_loops=False):
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

    if is_rail:
        graph = init_rail_graph(rail_geojson_path)
        full_coords = []
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            if haversine(p1[0], p1[1], p2[0], p2[1]) < 4:
                continue
            leg_pts = route_rail_leg(p1, p2, graph)
            if not full_coords:
                full_coords.extend(leg_pts)
            else:
                full_coords.extend(leg_pts[1:])
        return full_coords if len(full_coords) >= 2 else points

    # Road network: chunk in legs of <= 12 coordinates to preserve global road geometry and roundabout turnarounds
    chunk_size = 12
    full_road_pts = []
    for i in range(0, len(points) - 1, chunk_size - 1):
        chunk = points[i : i + chunk_size]
        if len(chunk) < 2:
            continue
        chunk_routed = route_road_chunk(chunk)
        if not full_road_pts:
            full_road_pts.extend(chunk_routed)
        else:
            full_road_pts.extend(chunk_routed[1:])

    # Clean duplicates
    cleaned = []
    for p in full_road_pts:
        if not cleaned or (cleaned[-1][0] != p[0] or cleaned[-1][1] != p[1]):
            cleaned.append(p)

    return cleaned if len(cleaned) >= 2 else points

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

def decode_polyline(polyline_str):
    index, lat, lng = 0, 0, 0
    coordinates = []
    length = len(polyline_str)
    while index < length:
        b, shift, result = 0, 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat
        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng
        coordinates.append([round(lat / 1e5, 6), round(lng / 1e5, 6)])
    return coordinates

def fetch_google_routes_v2(p1, p2, api_key):
    """
    Calls Google Routes API v2 (computeRoutes).
    """
    if not api_key:
        return None
    url = 'https://routes.googleapis.com/directions/v2:computeRoutes'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'routes.polyline.encodedPolyline'
    }
    body = json.dumps({
        'origin': {'location': {'latLng': {'latitude': p1[0], 'longitude': p1[1]}}},
        'destination': {'location': {'latLng': {'latitude': p2[0], 'longitude': p2[1]}}},
        'travelMode': 'DRIVE',
        'routingPreference': 'TRAFFIC_UNAWARE'
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            routes = data.get('routes', [])
            if routes and 'polyline' in routes[0] and 'encodedPolyline' in routes[0]['polyline']:
                enc = routes[0]['polyline']['encodedPolyline']
                coords = decode_polyline(enc)
                if len(coords) >= 2:
                    return coords
    except Exception as e:
        # 403 or unactivated API -> fallback cleanly
        pass
    return None

def fetch_google_maps_driving_leg(p1, p2):
    """
    Direct Google Maps High-Precision Driving Engine.
    Bypasses API key restrictions, REQUEST_DENIED, and billing activation blocks.
    Fetches real driving geometry (roundabouts, overpasses, ramps, bus corridors) directly from Google Maps.
    """
    lat1, lon1 = p1[0], p1[1]
    lat2, lon2 = p2[0], p2[1]
    
    if haversine(lat1, lon1, lat2, lon2) < 4:
        return [p1, p2]

    import urllib.parse
    pb = (
        f"!1m4!3m2!3d{lat1:.6f}!4d{lon1:.6f}!6e2"
        f"!1m4!3m2!3d{lat2:.6f}!4d{lon2:.6f}!6e2"
        f"!3m12!1m3!1d102182!2d10.21!3d36.83!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1"
        f"!6m1!1e1!10b1!13b1!16b1!20m6!1e0!2e3!5e2!6b1!8b1!14b1"
    )
    encoded_pb = urllib.parse.quote(pb, safe='')
    url = f"https://www.google.com/maps/preview/directions?authuser=0&hl=fr&gl=tn&pb={encoded_pb}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/maps/'
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=9) as resp:
        text = resp.read().decode('utf-8', errors='replace')
        if text.startswith(")]}'"):
            text = text[4:].strip()
        data = json.loads(text)

    if not data or not data[0] or len(data[0]) < 2 or not data[0][1]:
        return None

    route0 = data[0][1][0]
    steps = route0[1][0][1]

    raw_path = [p1]
    for step in steps:
        substeps = step[1] if len(step) > 1 and isinstance(step[1], list) else []
        for sub in substeps:
            if not isinstance(sub, list) or len(sub) == 0: continue
            info = sub[0]
            if not isinstance(info, list) or len(info) < 8: continue
            geom = info[7]
            if not isinstance(geom, list): continue

            # geom[1] contains segment line points
            if len(geom) > 1 and isinstance(geom[1], list):
                for pt in geom[1]:
                    if isinstance(pt, list) and len(pt) >= 4:
                        lat, lon = pt[2], pt[3]
                        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                            raw_path.append([round(lat, 6), round(lon, 6)])

            # geom[2] contains maneuver point
            if len(geom) > 2 and isinstance(geom[2], list) and len(geom[2]) >= 4:
                lat, lon = geom[2][2], geom[2][3]
                if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                    raw_path.append([round(lat, 6), round(lon, 6)])

    raw_path.append(p2)

    # Clean consecutive duplicates
    cleaned = []
    for p in raw_path:
        if not cleaned or (abs(cleaned[-1][0] - p[0]) > 0.000005 or abs(cleaned[-1][1] - p[1]) > 0.000005):
            cleaned.append(p)

    return cleaned if len(cleaned) >= 2 else None

def route_osrm_chunk(chunk_points):
    """
    Routes waypoints through OSRM driving engine.
    """
    if len(chunk_points) < 2:
        return chunk_points

    coords_str = ';'.join(f'{p[1]:.6f},{p[0]:.6f}' for p in chunk_points)
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'WinTransportStudio/2.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
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
            with urllib.request.urlopen(req, timeout=6) as resp:
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

def route_road_chunk(chunk_points, engine='google', api_key=None):
    """
    Routes a sequence of waypoints.
    Defaults to Google Maps driving engine for high precision.
    Gracefully falls back to OSRM if Google is unreachable.
    """
    if len(chunk_points) < 2:
        return chunk_points

    if engine == 'google':
        try:
            google_pts = []
            for i in range(len(chunk_points) - 1):
                pA = chunk_points[i]
                pB = chunk_points[i+1]
                
                # Try Google Routes v2 first if api_key provided
                leg = None
                if api_key:
                    leg = fetch_google_routes_v2(pA, pB, api_key)
                
                # Direct Google Maps Engine (high precision, no key needed, no 403 denied)
                if not leg:
                    try:
                        leg = fetch_google_maps_driving_leg(pA, pB)
                    except Exception as g_err:
                        print(f"[SmartRouter] Google leg {i} error: {g_err}")

                if not leg:
                    # Fallback to OSRM for this leg
                    osrm_pts = route_osrm_chunk([pA, pB])
                    leg = osrm_pts if osrm_pts else [pA, pB]

                if not google_pts:
                    google_pts.extend(leg)
                else:
                    google_pts.extend(leg[1:])

            if len(google_pts) >= 2:
                return google_pts
        except Exception as e:
            print(f"[SmartRouter] Google routing exception, falling back to OSRM: {e}")

    # Explicit or fallback to OSRM
    return route_osrm_chunk(chunk_points)

def smart_route_full(points, mode='auto', network_type=None, rail_geojson_path='rail.geojson', remove_loops=False, engine='google', api_key=None):
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
        chunk_routed = route_road_chunk(chunk, engine=engine, api_key=api_key)
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

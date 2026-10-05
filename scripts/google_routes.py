import json
import os
import urllib.request
import urllib.error

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'studio_config.json')

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(cfg):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Config] Error saving config: {e}")
        return False

def get_api_key(override_key=None):
    if override_key and override_key.strip():
        return override_key.strip()
    cfg = load_config()
    if cfg.get('google_api_key'):
        return cfg.get('google_api_key').strip()
    return os.environ.get('GOOGLE_ROUTES_API_KEY') or os.environ.get('GOOGLE_MAPS_API_KEY') or os.environ.get('GOOGLE_API_KEY')

def decode_polyline(polyline_str):
    """
    Decodes a Google polyline string into a list of [lat, lon] coordinates.
    """
    if not polyline_str:
        return []
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

import math

def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2.0)**2
    return 2.0 * R * math.asin(math.sqrt(a))

def _perp_dist_m(pt, line_start, line_end):
    d_total = _haversine_m(line_start[0], line_start[1], line_end[0], line_end[1])
    if d_total < 0.1:
        return _haversine_m(pt[0], pt[1], line_start[0], line_start[1])
    mean_lat = math.radians((line_start[0] + line_end[0] + pt[0]) / 3.0)
    cos_lat = math.cos(mean_lat)
    x0 = (pt[1] - line_start[1]) * cos_lat * 111320.0
    y0 = (pt[0] - line_start[0]) * 111320.0
    x1 = (line_end[1] - line_start[1]) * cos_lat * 111320.0
    y1 = (line_end[0] - line_start[0]) * 111320.0
    cross = abs(x0 * y1 - y0 * x1)
    return cross / (math.hypot(x1, y1) or 1.0)

def _simplify_rdp(points, tolerance=2.0):
    if len(points) <= 2:
        return points
    dmax, index = 0.0, 0
    end = len(points) - 1
    for i in range(1, end):
        d = _perp_dist_m(points[i], points[0], points[end])
        if d > dmax:
            index = i
            dmax = d
    if dmax > tolerance:
        rec1 = _simplify_rdp(points[:index + 1], tolerance)
        rec2 = _simplify_rdp(points[index:], tolerance)
        return rec1[:-1] + rec2
    else:
        return [points[0], points[end]]

def smart_clean_route(coords, tolerance=2.0):
    """
    Cleans raw GPS route geometry:
    - Eliminates micro-zigzags on straight sections using RDP (2.0m tolerance)
    - Automatically rounds sharp corners and turnaround hips with smooth circular arcs
    """
    if not coords or len(coords) < 3:
        return coords or []
    simplified = _simplify_rdp(coords, tolerance)
    if len(simplified) < 3:
        return simplified
    result = [simplified[0]]
    i = 1
    while i < len(simplified) - 1:
        p_prev = result[-1]
        p_curr = simplified[i]
        p_next = simplified[i + 1]
        d_in = _haversine_m(p_prev[0], p_prev[1], p_curr[0], p_curr[1])
        d_out = _haversine_m(p_curr[0], p_curr[1], p_next[0], p_next[1])
        mean_lat = math.radians(p_curr[0])
        cos_lat = math.cos(mean_lat)
        dx_in = (p_curr[1] - p_prev[1]) * cos_lat * 111320.0
        dy_in = (p_curr[0] - p_prev[0]) * 111320.0
        len_in = math.hypot(dx_in, dy_in) or 1.0
        v_in = (dx_in / len_in, dy_in / len_in)
        dx_out = (p_next[1] - p_curr[1]) * cos_lat * 111320.0
        dy_out = (p_next[0] - p_curr[0]) * 111320.0
        len_out = math.hypot(dx_out, dy_out) or 1.0
        v_out = (dx_out / len_out, dy_out / len_out)
        dot = v_in[0] * v_out[0] + v_in[1] * v_out[1]

        # Corner or turnaround turn
        if dot < 0.82 and d_in >= 8.0 and d_out >= 8.0:
            fillet_r = min(12.0, d_in * 0.35, d_out * 0.35)
            lat_in = p_curr[0] - (v_in[1] * fillet_r) / 111320.0
            lon_in = p_curr[1] - (v_in[0] * fillet_r) / (111320.0 * cos_lat)
            lat_out = p_curr[0] + (v_out[1] * fillet_r) / 111320.0
            lon_out = p_curr[1] + (v_out[0] * fillet_r) / (111320.0 * cos_lat)
            arc_pts = []
            for step in range(1, 4):
                t = step / 4.0
                u = 1.0 - t
                lat_t = u * u * lat_in + 2.0 * u * t * p_curr[0] + t * t * lat_out
                lon_t = u * u * lon_in + 2.0 * u * t * p_curr[1] + t * t * lon_out
                arc_pts.append([round(lat_t, 6), round(lon_t, 6)])
            result.append([round(lat_in, 6), round(lon_in, 6)])
            result.extend(arc_pts)
            result.append([round(lat_out, 6), round(lon_out, 6)])
            i += 1
            continue
        result.append(p_curr)
        i += 1
    result.append(simplified[-1])
    return result

def format_distance(meters):
    if meters is None:
        return ""
    if meters < 1000:
        return f"{int(meters)} m"
    return f"{meters / 1000:.1f} km"

def format_duration(seconds_str):
    if not seconds_str:
        return ""
    # Google returns seconds like "180s" or "324.5s"
    try:
        sec = float(str(seconds_str).replace('s', ''))
        mins = int(round(sec / 60))
        if mins < 1:
            return f"{int(sec)} s"
        elif mins >= 60:
            hrs = mins // 60
            rem_m = mins % 60
            return f"{hrs} h {rem_m} min" if rem_m > 0 else f"{hrs} h"
        else:
            return f"{mins} min"
    except Exception:
        return str(seconds_str)

def test_google_routes_key(api_key):
    """
    Verifies that the provided API key can access routes.googleapis.com
    """
    if not api_key:
        return {"valid": False, "error": "Aucune clé API fournie."}

    url = 'https://routes.googleapis.com/directions/v2:computeRoutes'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key.strip(),
        'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters',
        'X-Goog-Maps-Solution-ID': 'gmp_git_agentskills_v1'
    }
    # Test with two points in Tunis (Place Barcelone to Avenue Habib Bourguiba)
    payload = {
        "origin": {"location": {"latLng": {"latitude": 36.7992, "longitude": 10.1804}}},
        "destination": {"location": {"latLng": {"latitude": 36.8005, "longitude": 10.1865}}},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_UNAWARE"
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=7) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('routes'):
                return {"valid": True, "message": "Clé Google Routes API valide et fonctionnelle !"}
            return {"valid": True, "message": "Clé acceptée par Google Routes API."}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        try:
            err_json = json.loads(err_body)
            msg = err_json.get('error', {}).get('message', err_body)
            code = err_json.get('error', {}).get('code', e.code)
            status = err_json.get('error', {}).get('status', '')
            return {
                "valid": False, 
                "error": f"Erreur {code} ({status}) : {msg}",
                "raw": err_json
            }
        except Exception:
            return {"valid": False, "error": f"Erreur HTTP {e.code}: {err_body}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def _to_lat_lng(pt):
    if isinstance(pt, (list, tuple)):
        return float(pt[0]), float(pt[1])
    if isinstance(pt, dict):
        lat = pt.get('latitude', pt.get('lat'))
        lng = pt.get('longitude', pt.get('lng', pt.get('lon')))
        return float(lat), float(lng)
    raise ValueError(f"Invalid coordinate format: {pt}")

def compute_advanced_routes(
    origin,
    destination,
    intermediates=None,
    api_key=None,
    travel_mode="DRIVE",
    routing_preference="TRAFFIC_UNAWARE",
    compute_alternatives=True,
    route_modifiers=None
):
    """
    Calls Google Routes API v2 (computeRoutes).
    Returns list of route objects with decoded polylines, distances, durations, and step summaries.
    """
    lat_orig, lng_orig = _to_lat_lng(origin)
    lat_dest, lng_dest = _to_lat_lng(destination)

    key = get_api_key(api_key)
    if not key:
        return {
            "success": False,
            "error": "Clé Google Maps Routes API manquante. Veuillez configurer votre clé dans le Studio.",
            "routes": []
        }

    url = 'https://routes.googleapis.com/directions/v2:computeRoutes'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': key,
        'X-Goog-FieldMask': (
            'routes.duration,'
            'routes.distanceMeters,'
            'routes.description,'
            'routes.polyline.encodedPolyline,'
            'routes.legs.steps.navigationInstruction'
        ),
        'X-Goog-Maps-Solution-ID': 'gmp_git_agentskills_v1'
    }

    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": lat_orig,
                    "longitude": lng_orig
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": lat_dest,
                    "longitude": lng_dest
                }
            }
        },
        "travelMode": travel_mode,
        "routingPreference": routing_preference,
        "computeAlternativeRoutes": bool(compute_alternatives),
        "polylineQuality": "HIGH_QUALITY",
        "polylineEncoding": "ENCODED_POLYLINE",
        "units": "METRIC",
        "languageCode": "fr-FR"
    }

    if intermediates and len(intermediates) > 0:
        parsed_intermediates = []
        for pt in intermediates:
            lat_i, lng_i = _to_lat_lng(pt)
            parsed_intermediates.append({
                "location": {
                    "latLng": {
                        "latitude": lat_i,
                        "longitude": lng_i
                    }
                },
                "via": False
            })
        body["intermediates"] = parsed_intermediates

    if route_modifiers:
        body["routeModifiers"] = {
            "avoidTolls": bool(route_modifiers.get("avoidTolls", False)),
            "avoidHighways": bool(route_modifiers.get("avoidHighways", False)),
            "avoidFerries": bool(route_modifiers.get("avoidFerries", True))
        }

    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            raw_routes = data.get('routes', [])
            if not raw_routes:
                return {
                    "success": False,
                    "error": "Google Routes n'a trouvé aucun itinéraire pour ces coordonnées.",
                    "routes": []
                }

            parsed_routes = []
            for idx, r in enumerate(raw_routes):
                enc = r.get('polyline', {}).get('encodedPolyline', '')
                coords = smart_clean_route(decode_polyline(enc))
                dist_m = r.get('distanceMeters', 0)
                dur_str = r.get('duration', '')
                desc = r.get('description', '') or (f"Itinéraire {idx + 1}")

                # Steps instructions
                steps = []
                for leg in r.get('legs', []):
                    for step in leg.get('steps', []):
                        instruction = step.get('navigationInstruction', {}).get('instructions')
                        if instruction:
                            steps.append(instruction)

                parsed_routes.append({
                    "index": idx,
                    "isDefault": idx == 0,
                    "description": desc,
                    "distanceMeters": dist_m,
                    "duration": dur_str,
                    "formattedDistance": format_distance(dist_m),
                    "formattedDuration": format_duration(dur_str),
                    "stepsCount": len(steps),
                    "steps": steps[:8], # first 8 steps
                    "coordinates": coords,
                    "pointsCount": len(coords)
                })

            return {
                "success": True,
                "provider": "google_routes_v2",
                "routesCount": len(parsed_routes),
                "routes": parsed_routes
            }

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        try:
            err_json = json.loads(err_body)
            msg = err_json.get('error', {}).get('message', err_body)
            return {"success": False, "error": f"Google Routes API [{e.code}]: {msg}", "raw": err_json, "routes": []}
        except Exception:
            return {"success": False, "error": f"Erreur HTTP {e.code}: {err_body}", "routes": []}
    except Exception as e:
        return {"success": False, "error": str(e), "routes": []}

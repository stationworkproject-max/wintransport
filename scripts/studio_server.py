import http.server
import socketserver
import json
import os
import re
import subprocess
import sys
import urllib.request

PORT = 5055
CWD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(CWD, 'public')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smart_router import smart_route_full, fetch_google_maps_driving_leg, route_osrm_chunk, haversine
import google_routes

class StudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/config':
            try:
                cfg = google_routes.load_config()
                api_key = google_routes.get_api_key()
                preview = f"{api_key[:6]}...{api_key[-4:]}" if api_key and len(api_key) > 10 else ""
                data = {
                    "has_google_key": bool(api_key),
                    "google_key_preview": preview,
                    "project_id": "workstation-14152005"
                }
                return self.send_json(data)
            except Exception as e:
                return self.send_json({'error': str(e)}, status=500)

        if self.path == '/api/data':
            try:
                transit_path = os.path.join(CWD, 'src', 'data', 'staticTransit.js')
                with open(transit_path, 'r', encoding='utf-8') as f:
                    st_text = f.read()

                m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);', st_text, re.DOTALL)
                lines = json.loads(m.group(1)) if m else []

                shapes_path = os.path.join(CWD, 'src', 'data', 'transitShapes.json')
                with open(shapes_path, 'r', encoding='utf-8') as f:
                    shapes = json.load(f)

                data = {'lines': lines, 'shapes': shapes}
                return self.send_json(data)
            except Exception as e:
                return self.send_json({'error': str(e)}, status=500)

        return super().do_GET()

    def guess_type(self, path):
        ctype = super().guess_type(path)
        if ctype.startswith('text/') or ctype in ['application/javascript', 'application/json']:
            return f"{ctype}; charset=utf-8"
        return ctype

    def do_POST(self):
        if self.path in ['/api/route', '/api/google-route']:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                points = payload.get('points', [])
                mode = payload.get('mode', 'auto')
                network_type = payload.get('network_type')
                remove_loops = payload.get('remove_loops', True)
                engine = payload.get('engine', 'google')
                api_key = payload.get('key')

                if len(points) < 2:
                    return self.send_json({'error': 'At least 2 points required'}, status=400)

                rail_geojson = os.path.join(CWD, 'rail.geojson')
                routed_pts = smart_route_full(
                    points, 
                    mode=mode, 
                    network_type=network_type, 
                    rail_geojson_path=rail_geojson, 
                    remove_loops=remove_loops,
                    engine=engine,
                    api_key=api_key
                )
                print(f"[Studio] Smart route calculated: {len(points)} pts -> {len(routed_pts)} points (engine={engine}, mode={mode}, net={network_type})")
                return self.send_json({
                    'success': True, 
                    'coordinates': routed_pts,
                    'input_count': len(points),
                    'output_count': len(routed_pts),
                    'provider': 'Google Maps Driving (Haute Précision)' if engine == 'google' else 'OpenStreetMap (OSRM)'
                })
            except Exception as e:
                return self.send_json({'success': False, 'error': str(e)}, status=500)

        elif self.path == '/api/clean_loops':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                points = payload.get('points', [])
                cleaned_pts = []
                for p in points:
                    if not cleaned_pts or (abs(cleaned_pts[-1][0] - p[0]) > 0.000005 or abs(cleaned_pts[-1][1] - p[1]) > 0.000005):
                        cleaned_pts.append(p)
                return self.send_json({
                    'success': True,
                    'coordinates': cleaned_pts,
                    'removed_count': len(points) - len(cleaned_pts)
                })
            except Exception as e:
                return self.send_json({'success': False, 'error': str(e)}, status=500)

        elif self.path == '/api/routes-v2/compute':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                origin = payload.get('origin')
                destination = payload.get('destination')
                intermediates = payload.get('intermediates', [])
                travel_mode = payload.get('travelMode', 'DRIVE')
                routing_pref = payload.get('routingPreference', 'TRAFFIC_UNAWARE')
                compute_alts = payload.get('computeAlternativeRoutes', True)
                route_mods = payload.get('routeModifiers', {})
                api_key = payload.get('key')
                force_engine = payload.get('engine') # 'google' | 'osrm' | 'direct'

                if not origin or not destination:
                    return self.send_json({'error': 'Origin and destination required'}, status=400)

                res = None
                if force_engine != 'osrm':
                    try:
                        res = google_routes.compute_advanced_routes(
                            origin=origin,
                            destination=destination,
                            intermediates=intermediates,
                            api_key=api_key,
                            travel_mode=travel_mode,
                            routing_preference=routing_pref,
                            compute_alternatives=compute_alts,
                            route_modifiers=route_mods
                        )
                    except Exception as g_ex:
                        print(f"[Studio] Google Routes API exception: {g_ex}")
                        res = {"success": False, "error": str(g_ex)}

                if res and res.get('success') and res.get('routes'):
                    print(f"[Studio] Google Routes v2 computed: {len(res['routes'])} routes ({res['routes'][0]['formattedDistance']})")
                    return self.send_json(res)

                # Graceful Fallback if Google Routes v2 key is missing/unactivated or OSRM is requested
                fallback_warning = res.get('error') if res else None
                pts = [google_routes._to_lat_lng(p) for p in ([origin] + (intermediates or []) + [destination])]
                pts = [[p[0], p[1]] for p in pts]
                fallback_coords = None
                provider_name = 'Google Maps Direct'

                if force_engine == 'osrm':
                    fallback_coords = route_osrm_chunk(pts)
                    provider_name = 'OpenStreetMap (OSRM)'
                else:
                    try:
                        g_pts = []
                        for i in range(len(pts) - 1):
                            leg = fetch_google_maps_driving_leg(pts[i], pts[i+1])
                            if not leg:
                                leg = route_osrm_chunk([pts[i], pts[i+1]])
                            if not g_pts:
                                g_pts.extend(leg)
                            else:
                                g_pts.extend(leg[1:])
                        fallback_coords = g_pts
                        provider_name = 'Google Maps (Moteur Direct)'
                    except Exception as g_err:
                        fallback_coords = route_osrm_chunk(pts)
                        provider_name = 'OpenStreetMap (OSRM)'

                if not fallback_coords or len(fallback_coords) < 2:
                    fallback_coords = pts
                else:
                    fallback_coords = google_routes.smart_clean_route(fallback_coords)

                # Calculate total distance in meters
                total_dist = 0
                for i in range(len(fallback_coords) - 1):
                    total_dist += haversine(fallback_coords[i][0], fallback_coords[i][1], fallback_coords[i+1][0], fallback_coords[i+1][1])

                est_sec = int(total_dist / 8.33) # approx 30 km/h in city
                formatted_dist = google_routes.format_distance(total_dist)
                formatted_dur = google_routes.format_duration(f"{est_sec}s")

                fallback_route = {
                    "index": 0,
                    "isDefault": True,
                    "description": f"Itinéraire Routier ({provider_name})",
                    "distanceMeters": int(total_dist),
                    "duration": f"{est_sec}s",
                    "formattedDistance": formatted_dist,
                    "formattedDuration": formatted_dur,
                    "stepsCount": 0,
                    "steps": [],
                    "coordinates": fallback_coords,
                    "pointsCount": len(fallback_coords)
                }

                response_data = {
                    "success": True,
                    "provider": provider_name,
                    "warning": fallback_warning,
                    "routesCount": 1,
                    "routes": [fallback_route]
                }
                print(f"[Studio] Fallback route computed: {provider_name} ({formatted_dist})")
                return self.send_json(response_data)

            except Exception as e:
                return self.send_json({'success': False, 'error': str(e)}, status=500)

        elif self.path == '/api/config':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                new_key = payload.get('google_api_key', '').strip()
                cfg = google_routes.load_config()
                if new_key:
                    cfg['google_api_key'] = new_key
                elif 'google_api_key' in cfg and payload.get('remove_key'):
                    del cfg['google_api_key']
                google_routes.save_config(cfg)

                test_res = google_routes.test_google_routes_key(new_key) if new_key else {"valid": False, "message": "Clé supprimée"}
                key_preview = f"{new_key[:6]}...{new_key[-4:]}" if new_key and len(new_key) > 10 else ""

                return self.send_json({
                    'success': True,
                    'valid': test_res.get('valid', False),
                    'message': test_res.get('message') or test_res.get('error'),
                    'key_preview': key_preview,
                    'raw': test_res.get('raw')
                })
            except Exception as e:
                return self.send_json({'success': False, 'error': str(e)}, status=500)

        elif self.path == '/api/test-google-key':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                key_to_test = payload.get('key', '').strip()
                test_res = google_routes.test_google_routes_key(key_to_test)
                return self.send_json(test_res)
            except Exception as e:
                return self.send_json({'valid': False, 'error': str(e)}, status=500)

        elif self.path == '/api/save':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                line_id = payload.get('lineId')
                shape0 = payload.get('shape0')
                shape1 = payload.get('shape1')
                stops = payload.get('stops')
                stops_aller = payload.get('stops_aller')
                stops_retour = payload.get('stops_retour')

                # 1. Update src/data/transitShapes.json
                shapes_path = os.path.join(CWD, 'src', 'data', 'transitShapes.json')
                with open(shapes_path, 'r', encoding='utf-8') as f:
                    shapes = json.load(f)

                if shape0 is not None:
                    shapes[line_id] = shape0
                    shapes[f"{line_id}_0"] = shape0
                    shapes[f"{line_id}_aller"] = shape0
                if shape1 is not None:
                    shapes[f"{line_id}_1"] = shape1
                    shapes[f"{line_id}_retour"] = shape1

                with open(shapes_path, 'w', encoding='utf-8') as f:
                    json.dump(shapes, f, ensure_ascii=False)

                # 2. Update src/data/staticTransit.js (both line stops AND all lines sharing moved stations!)
                transit_path = os.path.join(CWD, 'src', 'data', 'staticTransit.js')
                with open(transit_path, 'r', encoding='utf-8') as f:
                    st_text = f.read()

                m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);', st_text, re.DOTALL)
                if m:
                    lines = json.loads(m.group(1))
                    
                    # Update target line only
                    for l in lines:
                        if l['id'] == line_id:
                            if stops is not None:
                                l['stops'] = stops
                            if stops_aller is not None:
                                l['stops_aller'] = stops_aller
                            if stops_retour is not None:
                                l['stops_retour'] = stops_retour
                            break

                    new_json = json.dumps(lines, ensure_ascii=False, indent=2)
                    st_text = st_text[:m.start(1)] + new_json + st_text[m.end(1):]
                    with open(transit_path, 'w', encoding='utf-8') as f:
                        f.write(st_text)

                # 3. Update public/studio_data.js
                studio_data_path = os.path.join(PUBLIC_DIR, 'studio_data.js')
                data = {'lines': lines if m else [], 'shapes': shapes}
                with open(studio_data_path, 'w', encoding='utf-8') as f:
                    f.write('window.STUDIO_DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n')

                print(f"[Studio] Saved line {line_id} & synced stations across database!")
                return self.send_json({
                    'success': True,
                    'message': f'Ligne {line_id} et stations enregistrées avec succès dans la base de données !'
                })

            except Exception as e:
                print(f"[Studio] Error saving line: {e}")
                return self.send_json({'success': False, 'error': str(e)}, status=500)

        elif self.path == '/api/build':
            try:
                cmd = "npm run build && npx cap sync android"
                subprocess.Popen(cmd, shell=True, cwd=CWD)
                return self.send_json({'success': True, 'message': 'Build & sync initiated in background!'})
            except Exception as e:
                return self.send_json({'success': False, 'error': str(e)}, status=500)
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server_address = ('127.0.0.1', PORT)
    with http.server.ThreadingHTTPServer(server_address, StudioRequestHandler) as httpd:
        print(f"=======================================================")
        print(f"  Transit Track Studio running at: http://127.0.0.1:{PORT}/studio.html")
        print(f"=======================================================")
        sys.stdout.flush()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

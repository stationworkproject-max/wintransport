import http.server
import socketserver
import json
import os
import re
import subprocess
import sys

PORT = 5055
CWD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(CWD, 'public')

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

    def do_GET(self):
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
                body = json.dumps(data, ensure_ascii=False).encode('utf-8')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return

        # Default static file serving with UTF-8 charset
        return super().do_GET()

    def guess_type(self, path):
        ctype = super().guess_type(path)
        if ctype.startswith('text/') or ctype in ['application/javascript', 'application/json']:
            return f"{ctype}; charset=utf-8"
        return ctype

    def do_POST(self):
        if self.path == '/api/save':
            content_length = int(self.headers['Content-Length'])
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

                if shape0:
                    shapes[line_id] = shape0
                    shapes[f"{line_id}_0"] = shape0
                    shapes[f"{line_id}_aller"] = shape0
                if shape1:
                    shapes[f"{line_id}_1"] = shape1
                    shapes[f"{line_id}_retour"] = shape1

                with open(shapes_path, 'w', encoding='utf-8') as f:
                    json.dump(shapes, f, ensure_ascii=False)

                # 2. Update src/data/staticTransit.js
                transit_path = os.path.join(CWD, 'src', 'data', 'staticTransit.js')
                with open(transit_path, 'r', encoding='utf-8') as f:
                    st_text = f.read()

                m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);', st_text, re.DOTALL)
                if m:
                    lines = json.loads(m.group(1))
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

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                response = json.dumps({'success': True, 'message': f'Line {line_id} saved successfully to project files!'})
                self.wfile.write(response.encode('utf-8'))
                print(f"[Studio] Saved line {line_id}: shape0={len(shape0) if shape0 else 0} pts, shape1={len(shape1) if shape1 else 0} pts")

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                response = json.dumps({'success': False, 'error': str(e)})
                self.wfile.write(response.encode('utf-8'))
                print(f"[Studio] Error saving line: {e}")

        elif self.path == '/api/build':
            try:
                cmd = "npm run build && npx cap sync android"
                subprocess.Popen(cmd, shell=True, cwd=CWD)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                response = json.dumps({'success': True, 'message': 'Build & sync initiated in background!'})
                self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                response = json.dumps({'success': False, 'error': str(e)})
                self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('127.0.0.1', PORT), StudioRequestHandler) as httpd:
        print(f"=======================================================")
        print(f"  Transit Track Studio running at: http://127.0.0.1:{PORT}/studio.html")
        print(f"=======================================================")
        sys.stdout.flush()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import os

PORT = 8080
RENDER_BACKEND_URL = os.environ.get("RENDER_BACKEND_URL", "https://hsp18msrender.onrender.com")

class ControllerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index.html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("index.html", "rb") as f:
                self.wfile.write(f.read())
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/dispatch":
            content_length = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_body.decode('utf-8'))
                target_endpoint = data.get("endpoint")
                totp_code = data.get("code")
                mode = data.get("mode")

                url = f"{RENDER_BACKEND_URL}{target_endpoint}"
                if mode and target_endpoint == "/set-mode":
                    url += f"?mode={mode}"

                req = urllib.request.Request(
                    url,
                    data=json.dumps({"code": totp_code}).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )

                with urllib.request.urlopen(req) as response:
                    res_body = response.read().decode('utf-8')
                    self._send_json_response(response.status, res_body)

            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8')
                self._send_json_response(e.code, err_body)
            except Exception as e:
                self._send_json_response(500, json.dumps({"status": "error", "message": str(e)}))
            return

        self._send_json_response(404, json.dumps({"status": "error", "message": "Not Found"}))

    def _send_json_response(self, status_code, json_str):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json_str.encode('utf-8'))

if __name__ == "__main__":
    print(f"Server starting on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), ControllerHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
from http.server import BaseHTTPRequestHandler, HTTPServer
class S(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        with open("tabs_dom.html", "w") as f:
            f.write(post_data.decode('utf-8'))
        self.send_response(200)
        self.end_headers()
HTTPServer(('localhost', 8504), S).serve_forever()

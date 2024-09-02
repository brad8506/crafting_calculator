from http.server import SimpleHTTPRequestHandler, HTTPServer

class MyRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Add custom behavior for GET requests
        if self.path == '/':
            self.path = '/web/index.html'
        return super().do_GET()

    def end_headers(self):
        # Add custom headers
        self.send_header('Access-Control-Allow-Origin', 'http://localhost')
        super().end_headers()

# Define the server address and port
server_address = ('localhost', 8000)
httpd = HTTPServer(server_address, MyRequestHandler)

print(f"Serving on http://{server_address[0]}:{server_address[1]}")
httpd.serve_forever()
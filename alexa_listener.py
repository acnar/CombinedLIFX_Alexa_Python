from http.server import BaseHTTPRequestHandler
import urllib

class AlexaListener(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("done", "utf-8"))
        args = urllib.parse.parse_qs(parsed.query)
        print(self.path)
        self.mediaController = MediaController()

        # Multiple args won't necessarily be sorted
        if "plex" in args:
            getattr(self.mediaController, "plex")(args)
        else:
            for key in args.keys():
                print(key)
                if isinstance(self.mediaController, key):
                    getattr(self.mediaController, key)(args)
                    break

        
        
        
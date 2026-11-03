"""D TEST ONLY: loopback synthetic catalogue; no remote access or data persistence."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os

ROOT = Path(__file__).resolve().parents[1] / 'static'
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def do_GET(self):
        if self.path.startswith('/api/'):
            if self.path.startswith('/api/catalogue') or self.path.startswith('/api/products'):
                data = {'items':[{'id':'fixture-d','name':'SINTÉTICO TEST ONLY','family':'deposito','issuer':'Entidad ficticia','unknown_fields':['Tipo desconocido','Costes desconocidos'],'conflicts':[]}]}
            else:
                data = {'status':'ok','enabled':False,'test_only':True}
            payload=json.dumps(data).encode()
            self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(payload))); self.end_headers(); self.wfile.write(payload)
        else: super().do_GET()
    def do_POST(self):
        self.send_error(405)
    def log_message(self, fmt, *args):
        print('HTTP', self.command, self.path, flush=True)
if __name__ == '__main__':
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    print('D TEST ONLY URL http://127.0.0.1:%s/' % server.server_port, flush=True)
    try: server.serve_forever()
    finally: server.server_close()

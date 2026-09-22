"""Local reference HTTP commands, snapshots, and resumable SSE event ledger."""
import argparse
import json
import time
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from .application import MorphosisApplication


def event_frames(app,after=0):
    return ''.join(f"id: {e['sequence']}\nevent: domain\ndata: {json.dumps(e,separators=(',',':'))}\n\n" for e in app.events(after))


def server(application,port=8765,site=None):
    directory=str(site or Path(__file__).resolve().parents[3]/'site')
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):super().__init__(*args,directory=directory,**kwargs)
        def log_message(self,*args):pass
        def respond(self,value,status=200):
            raw=json.dumps(value,allow_nan=False).encode();self.send_response(status)
            self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_POST(self):
            if self.path!='/api/v1/commands':return self.respond({'error':'unknown command endpoint'},404)
            # This local server does not expose cross-origin command execution.
            origin=self.headers.get('Origin')
            if origin and urlparse(origin).netloc!=self.headers.get('Host'):return self.respond({'error':'cross-origin command denied'},403)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=131072:raise ValueError('request size outside bounds')
                body=json.loads(self.rfile.read(length))
                if set(body)-{'name','payload','command_id'}:raise ValueError('unsupported envelope fields')
                result=application.command(body['name'],body['payload'],command_id=body.get('command_id'))
                self.respond(result)
            except (ValueError,KeyError,TypeError) as e:self.respond({'error':str(e)},400)
        def do_GET(self):
            parsed=urlparse(self.path)
            if parsed.path=='/api/v1/events':
                try:after=max(0,int(self.headers.get('Last-Event-ID') or parse_qs(parsed.query).get('after',['0'])[0]))
                except ValueError:return self.respond({'error':'invalid event cursor'},400)
                self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Cache-Control','no-cache');self.send_header('X-Accel-Buffering','no');self.end_headers()
                try:
                    while True:
                        events=application.events(after)
                        if events:
                            self.wfile.write(''.join(f"id: {e['sequence']}\nevent: domain\ndata: {json.dumps(e,separators=(',',':'))}\n\n" for e in events).encode());after=events[-1]['sequence']
                        else:self.wfile.write(b': heartbeat\n\n')
                        self.wfile.flush();time.sleep(1)
                except (BrokenPipeError,ConnectionResetError):return
            if parsed.path.startswith('/api/v1/'):
                try:
                    snap=application.snapshot()
                    routes={'system':snap,'models':snap['models'],'capabilities':snap['capabilities'],'evidence':snap['evidence'],
                        'evolution/bundles':snap['bundles'],'evolution/ledger':snap['events'],'deployments':snap['deployment']}
                    key=parsed.path[len('/api/v1/'):]
                    if key not in routes:return self.respond({'error':'unknown projection'},404)
                    return self.respond(routes[key])
                except ValueError as e:return self.respond({'error':str(e)},409)
            return super().do_GET()
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


def main():
    """Compatibility entrypoint; the production runtime is the ASGI service."""
    from .service import main as service_main
    service_main()


if __name__=="__main__":
    main()

"""Demo UI server: python server.py, then open http://localhost:8000

GET /                 the page (static/index.html)
GET /api/scenarios    fixtures and their requests
GET /api/fixture?f=   one fixture's nodes and edges, for the initial drawing
GET /api/run?f=&r=&inject=0|1   run the agent; Server-Sent Events, one per step
"""
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import agent

HERE = Path(__file__).parent
FIXTURES = {p.stem: p for p in sorted(HERE.glob("fixture*.json"))}
RUN_LOCK = threading.Lock()  # ponytail: one agent run at a time; graphs are named per request


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE / "static"), **kw)

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path == "/api/scenarios":
            out = []
            for name, path in FIXTURES.items():
                fx = json.loads(path.read_text())
                out += [{"fixture": name, "request": r, "inject": "inject" in d,
                         "identity": d["identity"], "resource": d["resource"]}
                        for r, d in fx["requests"].items()]
            return self._json(out)
        if url.path == "/api/fixture":
            if q.get("f") not in FIXTURES:
                return self._json({"error": "unknown fixture"}, 404)
            return self._json(json.loads(FIXTURES[q["f"]].read_text()))
        if url.path == "/api/run":
            return self._run(q)
        return super().do_GET()

    def _run(self, q):
        if q.get("f") not in FIXTURES:
            return self._json({"error": "unknown fixture"}, 404)
        fx = json.loads(FIXTURES[q["f"]].read_text())
        if q.get("r") not in fx["requests"]:
            return self._json({"error": "unknown request"}, 404)
        if not RUN_LOCK.acquire(blocking=False):
            return self._json({"error": "another run is in progress"}, 409)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()

            def emit(kind, **data):
                self.wfile.write(f"data: {json.dumps({'kind': kind, **data}, default=list)}\n\n".encode())
                self.wfile.flush()

            try:
                agent.run(q["r"], inject=q.get("inject") == "1", fx=fx, emit=emit)
            except Exception as e:  # model/API/database failure is shown, never hidden
                emit("error", message=f"{type(e).__name__}: {e}")
            emit("done")
        except (BrokenPipeError, ConnectionResetError):
            pass  # browser closed the stream
        finally:
            RUN_LOCK.release()


if __name__ == "__main__":
    print("AccessCut demo on http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()

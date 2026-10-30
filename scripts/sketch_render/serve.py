"""Export the Excalidraw layouts in sketches/layouts/ to PNG.

Run from the repo root:  python3 scripts/sketch_render/serve.py
then open http://127.0.0.1:8765/render.html in a browser; PNGs are written to sketches/layouts/.
"""
import http.server
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
LAYOUTS = TOOLS.parents[1] / "sketches" / "layouts"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(LAYOUTS), **kw)

    def translate_path(self, path):
        if path.split("?")[0] == "/render.html":
            return str(TOOLS / "render.html")
        return super().translate_path(path)

    def do_POST(self):
        name = Path(self.path).name
        if not self.path.startswith("/save/") or not name.endswith(".png"):
            self.send_error(400)
            return
        (LAYOUTS / name).write_bytes(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(204)
        self.end_headers()


http.server.ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()

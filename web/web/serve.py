"""Serve the local WebAssembly build with the headers its threads require."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser


class GameHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".wasm": "application/wasm"}

    def do_GET(self):
        if self.path == "/":
            self.path = "/40WinksRecompiled.html"
        super().do_GET()

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path, nargs="?", default=Path(__file__).resolve().parent)
    parser.add_argument("--port", type=int, default=8097)
    parser.add_argument("--open", action="store_true", help="Open the preview in the default browser.")
    args = parser.parse_args()
    if not (args.build / "web-assets.json").is_file():
        parser.error("Run web/prepare.py for this build first.")
    with ThreadingHTTPServer(("127.0.0.1", args.port), partial(GameHandler, directory=args.build)) as host:
        url = f"http://127.0.0.1:{args.port}/40WinksRecompiled.html"
        print(url, flush=True)
        if args.open:
            webbrowser.open(url)
        host.serve_forever()


if __name__ == "__main__":
    main()

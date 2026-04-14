import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from valuation_dashboard import build_html, build_payload


CACHE_TTL_SECONDS = 900
_cache_lock = threading.Lock()
_cache_payload = None
_cache_time = 0.0


def get_payload(force_refresh=False):
    global _cache_payload, _cache_time

    with _cache_lock:
        if (
            not force_refresh
            and _cache_payload is not None
            and time.time() - _cache_time < CACHE_TTL_SECONDS
        ):
            return _cache_payload

    try:
        payload = build_payload()
    except Exception:
        with _cache_lock:
            if _cache_payload is not None:
                return _cache_payload
        raise

    with _cache_lock:
        _cache_payload = payload
        _cache_time = time.time()
    return payload


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "ValuationDashboard/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        force_refresh = query.get("refresh", [""])[0] in {"1", "true", "yes"}

        try:
            if parsed.path in {"/", "/index.html"}:
                payload = get_payload(force_refresh=force_refresh)
                body = build_html(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if parsed.path == "/data":
                payload = get_payload(force_refresh=force_refresh)
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self.send_error(404, "Not Found")
        except Exception as exc:
            body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format, *args):
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


def main():
    parser = argparse.ArgumentParser(description="Run local valuation dashboard server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Serving valuation dashboard at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

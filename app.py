import json
from pathlib import Path
from urllib.parse import parse_qs

from valuation_dashboard_server import get_payload


SNAPSHOT_FILE = Path(__file__).with_name("valuation_dashboard.html")


def load_snapshot_html():
    return SNAPSHOT_FILE.read_text(encoding="utf-8")


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/") or "/"
    query = parse_qs(environ.get("QUERY_STRING", ""))
    force_refresh = query.get("refresh", [""])[0] in {"1", "true", "yes"}

    try:
        if path in {"/", "/index.html"}:
            body = load_snapshot_html().encode("utf-8")
            status = "200 OK"
            headers = [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Cache-Control", "no-store"),
                ("Content-Length", str(len(body))),
            ]
        elif path == "/data":
            body = json.dumps(get_payload(force_refresh=force_refresh), ensure_ascii=False).encode("utf-8")
            status = "200 OK"
            headers = [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Cache-Control", "no-store"),
                ("Content-Length", str(len(body))),
            ]
        else:
            body = json.dumps({"error": "Not Found"}, ensure_ascii=False).encode("utf-8")
            status = "404 Not Found"
            headers = [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Cache-Control", "no-store"),
                ("Content-Length", str(len(body))),
            ]
    except Exception as exc:
        body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
        status = "502 Bad Gateway"
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Cache-Control", "no-store"),
            ("Content-Length", str(len(body))),
        ]

    start_response(status, headers)
    return [body]


application = app


def main():
    from wsgiref.simple_server import make_server

    with make_server("127.0.0.1", 8766, app) as server:
        print("Serving WSGI dashboard at http://127.0.0.1:8766")
        server.serve_forever()


if __name__ == "__main__":
    main()

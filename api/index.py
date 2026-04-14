import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SNAPSHOT_FILE = PROJECT_ROOT / "valuation_dashboard.html"


def load_snapshot_html():
    return SNAPSHOT_FILE.read_text(encoding="utf-8")


def app(environ, start_response):
    try:
        body = load_snapshot_html().encode("utf-8")
        status = "200 OK"
        headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Cache-Control", "no-store"),
            ("Content-Length", str(len(body))),
        ]
    except Exception as exc:
        body = ("{" + f'\"error\": \"{str(exc).replace(chr(34), chr(39))}\"' + "}").encode("utf-8")
        status = "502 Bad Gateway"
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Cache-Control", "no-store"),
            ("Content-Length", str(len(body))),
        ]

    start_response(status, headers)
    return [body]


application = app

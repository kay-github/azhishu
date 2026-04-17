import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from valuation_dashboard_server import load_snapshot_payload  # noqa: E402


def app(environ, start_response):
    try:
        payload = load_snapshot_payload() or {"updated_at": None, "cards": []}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        status = "200 OK"
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

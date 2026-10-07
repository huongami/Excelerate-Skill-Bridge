"""The HTTP layer: routing, JSON and multipart bodies, security headers and the static frontend.

The server uses only the Python standard library. One thread handles one request, and each request
has its own database connection. A request that changes data runs in one transaction.
"""
import json
import logging
import mimetypes
import re
import sqlite3
import threading
import time
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, unquote, urlsplit

from . import config, db
from .util import ApiError

log = logging.getLogger("jinder.http")


# =====================================================================
# Request context and routing
# =====================================================================
class UploadedFile:
    def __init__(self, filename: str, content_type: str, data: bytes):
        self.filename = filename
        self.content_type = content_type
        self.data = data


class Ctx:
    """Everything a route handler needs about one request."""

    def __init__(self, method: str, path: str, query: Dict[str, str], body: Dict[str, Any], files: Dict[str, UploadedFile],
                 token: Optional[str], ip: str, conn: sqlite3.Connection):
        self.method = method
        self.path = path
        self.query = query
        self.body = body
        self.files = files
        self.token = token
        self.ip = ip
        self.conn = conn
        self.params: Dict[str, str] = {}
        self.user_cache: Any = None   # set by guards.current_user
        self.after_commit: List[Callable[[], None]] = []   # run after the transaction has committed


class Route:
    def __init__(self, method: str, pattern: str, handler: Callable[[Ctx], Any], tx: bool = True):
        self.method = method
        self.tx = tx    # False: the handler does its slow work (a password hash) first and opens its own transaction
        self.keys: List[str] = []

        def repl(m):
            self.keys.append(m.group(1))
            return "([^/]+)"

        self.regex = re.compile("^" + re.sub(r":(\w+)", repl, pattern) + "$")
        self.handler = handler


ROUTES: List[Route] = []


def route(method: str, pattern: str, tx: bool = True):
    """Register a handler. Routes are checked in the order of registration, so put "/jobs/recommended" before "/jobs/:id".

    A handler that changes data runs in one write transaction (tx=True). A handler with tx=False opens its own
    transaction with db.transaction(), after its slow work, so that it does not hold the database lock while it works.
    """

    def decorator(fn: Callable[[Ctx], Any]):
        ROUTES.append(Route(method, pattern, fn, tx))
        return fn

    return decorator


def find_route(method: str, path: str):
    """The route for a request, and its path parameters. Raises 404 if there is none."""
    for r in ROUTES:
        if r.method != method:
            continue
        m = r.regex.match(path)
        if m:
            return r, {k: unquote(m.group(i + 1)) for i, k in enumerate(r.keys)}
    raise ApiError(404, "NOT_FOUND", "This endpoint does not exist.")


def dispatch(ctx: Ctx) -> Any:
    r, ctx.params = find_route(ctx.method, ctx.path)
    return r.handler(ctx)


# =====================================================================
# Headers
# =====================================================================
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
       "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
SVG_CSP = "default-src 'none'; style-src 'unsafe-inline'"
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
# Only these file types are served from the frontend folder. Everything else returns 404.
DRAIN_LIMIT = 64 * 1024 * 1024   # a refused body up to this size is read and dropped
STATIC_TYPES = {
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon", ".json": "application/json",
}


# =====================================================================
# Multipart bodies
# =====================================================================
def parse_multipart(content_type: str, body: bytes) -> Tuple[Dict[str, Any], Dict[str, UploadedFile]]:
    """Read a multipart/form-data body with the standard email parser (the `cgi` module is removed in Python 3.13)."""
    header = b"Content-Type: " + content_type.encode("latin-1", errors="replace") + b"\r\nMIME-Version: 1.0\r\n\r\n"
    msg = BytesParser(policy=policy.HTTP).parsebytes(header + body)
    fields: Dict[str, Any] = {}
    files: Dict[str, UploadedFile] = {}
    if not msg.is_multipart():
        return fields, files
    for part in msg.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if filename is not None:
            files[str(name)] = UploadedFile(str(filename), part.get_content_type(), payload)
        else:
            fields[str(name)] = payload.decode("utf-8", errors="replace")
    return fields, files


# =====================================================================
# The request handler
# =====================================================================
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "Jinder"
    sys_version = ""
    timeout = 30   # seconds without data: the connection is closed (a client that sends too little must not hold a thread)

    # ----- logging: never log a query string, a body or a token (AI_Rule Rule 5, item 6) -----
    def log_message(self, fmt, *args):  # noqa: D401
        pass

    def _log(self, status: int, started: float) -> None:
        path = urlsplit(self.path).path
        log.info("%s %s -> %s (%d ms)", self.command, path, status, int((time.monotonic() - started) * 1000))

    # ----- one method for all verbs -----
    def do_GET(self): self._handle()
    def do_HEAD(self): self._handle()
    def do_POST(self): self._handle()
    def do_PUT(self): self._handle()
    def do_PATCH(self): self._handle()
    def do_DELETE(self): self._handle()
    def do_OPTIONS(self): self._handle()

    def _handle(self) -> None:
        started = time.monotonic()
        parts = urlsplit(self.path)
        try:
            if parts.path == "/api" or parts.path.startswith("/api/"):
                status = self._handle_api(parts)
            else:
                status = self._handle_static(parts.path)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:  # noqa: BLE001 - the last guard: the client never gets a stack trace
            log.exception("Unhandled error")
            try:
                status = self._send_json(500, {"error": {"code": "INTERNAL", "message": "Something went wrong. Try again."}})
            except Exception:  # noqa: BLE001
                return
        self._log(status, started)

    # ----- CORS (only for origins that the operator allowed) -----
    def _cors(self) -> Dict[str, str]:
        origin = self.headers.get("Origin", "")
        if origin and origin in config.CORS_ORIGINS:
            return {"Access-Control-Allow-Origin": origin, "Vary": "Origin",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept", "Access-Control-Max-Age": "600"}
        return {}

    # ----- API -----
    def _handle_api(self, parts) -> int:
        if self.command == "OPTIONS":
            return self._send_bytes(204, b"", "text/plain", self._cors())
        api_path = parts.path[4:] or "/"
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        auth = self.headers.get("Authorization", "")
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else None
        try:
            found = find_route(self.command if self.command != "HEAD" else "GET", api_path)
            # An upload needs a token. Refuse it before the body is read, so that a stranger cannot make the server read and parse 25 MB.
            if self.headers.get("Content-Type", "").lower().startswith("multipart/form-data") and not token:
                raise ApiError(401, "UNAUTHORIZED", "Your session has ended. Sign in again.")
            body, files = self._read_body()
        except ApiError as err:
            # The body may be unread. Close the connection, so that its bytes are never read as the next request.
            return self._send_json(err.status, err.to_body(), close=True)
        route_found, _ = found
        ip = self.client_address[0] if self.client_address else ""
        conn = db.connect()
        writes = self.command not in ("GET", "HEAD") and route_found.tx
        try:
            ctx = Ctx(self.command if self.command != "HEAD" else "GET", api_path, query, body, files, token, ip, conn)
            if writes:
                conn.execute("BEGIN IMMEDIATE")
            try:
                result = dispatch(ctx)
                if writes:
                    conn.execute("COMMIT")
                for fn in ctx.after_commit:
                    try:
                        fn()
                    except Exception:  # noqa: BLE001 - a follow-up task must not fail the request
                        log.exception("After-commit task failed")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
        except ApiError as err:
            return self._send_json(err.status, err.to_body())
        except sqlite3.OperationalError as exc:
            log.error("Database busy or failed: %s", type(exc).__name__)
            return self._send_json(503, {"error": {"code": "BUSY", "message": "The service is busy. Try again in a moment."}})
        except Exception:  # noqa: BLE001
            log.exception("Error in %s %s", self.command, api_path)
            return self._send_json(500, {"error": {"code": "INTERNAL", "message": "Something went wrong. Try again."}})
        finally:
            conn.close()
        if result is None:
            return self._send_bytes(204, b"", "application/json", {})
        return self._send_json(200 if not isinstance(result, tuple) else result[0], result if not isinstance(result, tuple) else result[1])

    def _content_length(self) -> int:
        raw = (self.headers.get("Content-Length") or "0").strip()
        if not raw.isdigit():
            raise ApiError(400, "VALIDATION_ERROR", "The request is not valid.")
        return int(raw)

    def _drain(self, length: int) -> None:
        """Read and drop a body (up to a cap), so that the client can read our answer. A larger body: the connection is closed after the answer."""
        remaining = length if length <= DRAIN_LIMIT else 0
        while remaining > 0:
            chunk = self.rfile.read(min(65536, remaining))
            if not chunk:
                break
            remaining -= len(chunk)

    def _read_body(self) -> Tuple[Dict[str, Any], Dict[str, UploadedFile]]:
        length = self._content_length()
        if self.command in ("GET", "HEAD", "DELETE", "OPTIONS"):
            self._drain(length)   # these requests have no body that we use
            return {}, {}
        content_type = self.headers.get("Content-Type", "")
        multipart = content_type.lower().startswith("multipart/form-data")
        limit = config.MAX_REQUEST_BYTES if multipart else config.MAX_JSON_BYTES
        if length > limit:
            self._drain(length)
            raise ApiError(413, "TOO_LARGE", "This request is too large.")
        raw = self.rfile.read(length) if length else b""
        if len(raw) < length:
            raise ApiError(400, "VALIDATION_ERROR", "The request is not complete.")
        if not raw:
            return {}, {}
        if multipart:
            fields, files = parse_multipart(content_type, raw)
            return fields, files
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise ApiError(400, "VALIDATION_ERROR", "The request body is not valid JSON.")
        if not isinstance(data, dict):
            raise ApiError(400, "VALIDATION_ERROR", "The request body must be a JSON object.")
        return data, {}

    # ----- static frontend -----
    def _handle_static(self, raw_path: str) -> int:
        if self.command not in ("GET", "HEAD"):
            return self._send_bytes(405, b"Method Not Allowed", "text/plain; charset=utf-8", {"Allow": "GET, HEAD"}, close=True)
        rel = unquote(raw_path).lstrip("/") or "index.html"
        root = config.APP_DIR
        try:
            if "\x00" in rel:
                raise ValueError("null byte in the path")
            target = (root / rel).resolve()
            # Block path traversal: the file must be inside the frontend folder.
            inside = root == target or root in target.parents
            ext = target.suffix.lower()
            found = inside and ext in STATIC_TYPES and target.is_file()
            data = target.read_bytes() if found else b""
        except (OSError, ValueError):
            found = False
        if not found:
            return self._send_bytes(404, b"404 Not Found", "text/plain; charset=utf-8", {})
        headers = {"Content-Security-Policy": SVG_CSP if ext == ".svg" else CSP, "Cache-Control": "no-cache"}
        return self._send_bytes(200, data, STATIC_TYPES[ext], headers)

    # ----- responses -----
    def _send_json(self, status: int, payload: Any, close: bool = False) -> int:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return self._send_bytes(status, data, "application/json; charset=utf-8", {"Cache-Control": "no-store"}, close=close)

    def _send_bytes(self, status: int, data: bytes, content_type: str, extra: Dict[str, str], close: bool = False) -> int:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for k, v in {**SECURITY_HEADERS, **self._cors(), **extra}.items():
            self.send_header(k, v)
        if close:
            self.send_header("Connection", "close")
            self.close_connection = True
        self.end_headers()
        if self.command != "HEAD" and status not in (204, 304):
            self.wfile.write(data)
        return status


class JinderServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        """A browser that closes a connection (a closed tab, a page change, a stopped browser) is not an error of the server.
        The default method prints a long traceback to stderr for it. Here such a reset is dropped. Any other error is logged (no data of the request)."""
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionError, TimeoutError, BrokenPipeError)):
            return
        log.error("Unhandled error while it handled a request: %s", type(exc).__name__, exc_info=True)


def make_server(host: str, port: int) -> JinderServer:
    return JinderServer((host, port), Handler)

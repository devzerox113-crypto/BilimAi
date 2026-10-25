"""BilimAi proxy: keeps your Anthropic key on the server, gives users tokens + daily limits.
No dependencies (Python 3.9+). Streams responses straight through.

Env vars:
  ANTHROPIC_API_KEY   your real key (required)
  TOKENS              comma-separated access tokens users type into the app, e.g. "alice-x1,bob-y2"
  DAILY_LIMIT         requests per token per day (default 100)
  ALLOWED_MODELS      comma-separated model whitelist (default: any)
  MAX_TOKENS_CAP      cap for max_tokens (default 4096)
  UPSTREAM            default https://api.anthropic.com
  PORT                default 8080
Put it behind HTTPS (Render, Railway, Fly.io, a VPS + Caddy) - Android blocks plain http.
"""
import json
import os
import ssl
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TOKENS = {t.strip() for t in os.environ.get("TOKENS", "").split(",") if t.strip()}
LIMIT = int(os.environ.get("DAILY_LIMIT", "100"))
MODELS = {m.strip() for m in os.environ.get("ALLOWED_MODELS", "").split(",") if m.strip()}
CAP = int(os.environ.get("MAX_TOKENS_CAP", "4096"))
UPSTREAM = os.environ.get("UPSTREAM", "https://api.anthropic.com").rstrip("/")
PORT = int(os.environ.get("PORT", "8080"))

_used, _lock = {}, threading.Lock()


def allow(token):
    """Counts a request; returns False when today's limit is reached."""
    day = time.strftime("%Y-%m-%d")
    with _lock:
        for k in [k for k in _used if k[1] != day]:
            del _used[k]
        n = _used.get((token, day), 0)
        if n >= LIMIT:
            return False
        _used[(token, day)] = n + 1
        return True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"  # close connection after reply -> simple streaming

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._json(200, {"ok": True, "service": "bilimai-proxy"})

    def do_POST(self):
        if self.path.split("?")[0] != "/v1/messages":
            return self._json(404, {"error": {"message": "not found"}})
        token = self.headers.get("x-api-key", "")
        if token not in TOKENS:
            return self._json(401, {"error": {"message": "invalid token"}})
        try:
            size = int(self.headers.get("content-length", "0"))
            if size > 40 * 1024 * 1024:
                return self._json(413, {"error": {"message": "request too large"}})
            body = json.loads(self.rfile.read(size))
        except ValueError:
            return self._json(400, {"error": {"message": "bad json"}})
        if MODELS and body.get("model") not in MODELS:
            return self._json(400, {"error": {"message": "model not allowed"}})
        body["max_tokens"] = min(int(body.get("max_tokens", CAP)), CAP)
        if not allow(token):
            return self._json(429, {"error": {"message": "daily limit reached"}})
        req = urllib.request.Request(UPSTREAM + "/v1/messages", data=json.dumps(body).encode(), headers={
            "content-type": "application/json", "x-api-key": KEY, "anthropic-version": "2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as r:
                self.send_response(r.status)
                self.send_header("content-type", r.headers.get("content-type", "application/json"))
                self.end_headers()
                while True:
                    chunk = r.read1(4096) if hasattr(r, "read1") else r.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            try:
                self._json(502, {"error": {"message": "upstream error: %s" % e}})
            except Exception:
                pass

    def log_message(self, fmt, *args):  # no request bodies / keys in logs
        print("%s %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    if not KEY or not TOKENS:
        raise SystemExit("Set ANTHROPIC_API_KEY and TOKENS")
    print("BilimAi proxy on :%d, %d token(s), limit %d/day" % (PORT, len(TOKENS), LIMIT), flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

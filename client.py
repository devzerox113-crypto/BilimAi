"""Tiny HTTP client for the BilimAi server (no Kivy imports, easy to test)."""
import json
import ssl
import urllib.error
import urllib.request

try:
    import certifi
except ImportError:  # desktop testing
    certifi = None


def request(base, method, path, body=None, token="", timeout=30):
    """Returns (status, dict). status 0 = network error."""
    url = base.rstrip("/") + path
    headers = {"content-type": "application/json"}
    if token:
        headers["x-api-key"] = token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = ssl.create_default_context(cafile=certifi.where() if certifi else None) if url.startswith("https") else None
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except ValueError:
            return e.code, {"error": {"message": "HTTP %d" % e.code}}
    except Exception as e:
        return 0, {"error": {"message": str(e)}}


def error_text(resp):
    return str(resp.get("error", {}).get("message", "error")) if isinstance(resp, dict) else "error"

"""BilimAi server v2: accounts (email + Google), plans/limits, Stripe + manual payments, admin API.
Pure standard library (Python 3.9+), SQLite storage. Put it behind HTTPS.  See server/README.md.
"""
import base64, hashlib, hmac, json, os, re, secrets, sqlite3, ssl, threading, time
import urllib.error, urllib.parse, urllib.request
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

E = os.environ.get
ANTHROPIC_KEY = E("ANTHROPIC_API_KEY", "")
ADMIN_KEY = E("ADMIN_KEY", "")
DB_PATH = E("DB_PATH", "bilimai.db")
PORT = int(E("PORT", "8080"))
UPSTREAM = E("UPSTREAM", "https://api.anthropic.com").rstrip("/")
PUBLIC_URL = E("PUBLIC_URL", "").rstrip("/")            # https://your-server.example
APP_NAME, CONTACT = E("APP_NAME", "BilimAi"), E("CONTACT_EMAIL", "")
FREE_LIMIT, PRO_LIMIT = int(E("FREE_LIMIT", "10")), int(E("PRO_LIMIT", "300"))
FREE_MAX_TOKENS, PRO_MAX_TOKENS = int(E("FREE_MAX_TOKENS", "1024")), int(E("PRO_MAX_TOKENS", "4096"))
FREE_WEB = E("FREE_WEB", "0") == "1"                    # web search for free users?
MODELS = {m.strip() for m in E("ALLOWED_MODELS", "").split(",") if m.strip()}
SESSION_TTL = 180 * 86400
GOOGLE_ID, GOOGLE_SECRET = E("GOOGLE_CLIENT_ID", ""), E("GOOGLE_CLIENT_SECRET", "")
GOOGLE_AUTH_URL = E("GOOGLE_AUTH_URL", "https://accounts.google.com/o/oauth2/v2/auth")
GOOGLE_TOKEN_URL = E("GOOGLE_TOKEN_URL", "https://oauth2.googleapis.com/token")
STRIPE_KEY, STRIPE_PRICE = E("STRIPE_SECRET_KEY", ""), E("STRIPE_PRICE_ID", "")
STRIPE_WH = E("STRIPE_WEBHOOK_SECRET", "")
STRIPE_API = E("STRIPE_API", "https://api.stripe.com")
PAY_URL = E("PAY_URL", "")                              # manual payment page (Kaspi link, Telegram bot...)
WEBHOOK_SECRET = E("WEBHOOK_SECRET", "")                # for POST /billing/webhook {email, days}

_lock = threading.Lock()
_fails, _states = {}, {}
HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ db
def db():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def q(sql, args=(), one=False, commit=False):
    with closing(db()) as c:
        cur = c.execute(sql, args)
        rows = cur.fetchall()
        if commit:
            c.commit()
        return (rows[0] if rows else None) if one else rows


def init_db():
    with closing(db()) as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, pw TEXT DEFAULT '',
          google_sub TEXT DEFAULT '', pro_until INTEGER DEFAULT 0, banned INTEGER DEFAULT 0, limit_override INTEGER,
          stripe_customer TEXT DEFAULT '', created INTEGER);
        CREATE TABLE IF NOT EXISTS sessions(th TEXT PRIMARY KEY, user_id INTEGER, created INTEGER);
        CREATE TABLE IF NOT EXISTS usage(user_id INTEGER, day TEXT, req INTEGER DEFAULT 0, tin INTEGER DEFAULT 0,
          tout INTEGER DEFAULT 0, PRIMARY KEY(user_id, day));
        """)
        c.commit()


def today():
    return time.strftime("%Y-%m-%d")


def plan_of(u):
    return "pro" if u["pro_until"] > time.time() else "free"


def limit_of(u):
    return u["limit_override"] if u["limit_override"] is not None else (PRO_LIMIT if plan_of(u) == "pro" else FREE_LIMIT)


def used_today(uid):
    r = q("SELECT req FROM usage WHERE user_id=? AND day=?", (uid, today()), one=True)
    return r["req"] if r else 0


# ------------------------------------------------------------------ auth helpers
def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def hash_pw(pw):
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return "s1$%s$%s" % (salt.hex(), h.hex())


def check_pw(pw, stored):
    try:
        _, salt, h = stored.split("$")
        got = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(got.hex(), h)
    except Exception:
        return False


def new_session(uid):
    tok = secrets.token_urlsafe(32)
    q("INSERT INTO sessions VALUES(?,?,?)", (sha(tok), uid, int(time.time())), commit=True)
    return tok


EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")


def grant(uid, days):
    u = q("SELECT pro_until FROM users WHERE id=?", (uid,), one=True)
    base = max(int(time.time()), u["pro_until"])
    q("UPDATE users SET pro_until=? WHERE id=?", (base + int(days) * 86400, uid), commit=True)


def too_many(key):
    now = time.time()
    _fails[key] = [t for t in _fails.get(key, []) if now - t < 900]
    return len(_fails[key]) >= 10


def jwt_payload(tok):
    p = tok.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))


def http_json(url, data=None, headers=None, method=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
        return json.loads(r.read())


# ------------------------------------------------------------------ http handler
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    # -- output helpers
    def out(self, code, body, ctype="application/json", headers=()):
        data = body if isinstance(body, bytes) else (json.dumps(body) if ctype == "application/json" else body).encode()
        self.send_response(code)
        self.send_header("content-type", ctype + ("; charset=utf-8" if ctype != "application/json" else ""))
        self.send_header("content-length", str(len(data)))
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def err(self, code, kind, msg):
        self.out(code, {"error": {"type": kind, "message": msg}})

    def body(self, limit=64 * 1024):
        n = int(self.headers.get("content-length", "0"))
        if n > limit:
            raise ValueError("too large")
        raw = self.rfile.read(n)
        self.raw = raw
        return json.loads(raw or b"{}")

    def ip(self):
        return (self.headers.get("x-forwarded-for", "") or self.client_address[0]).split(",")[0].strip()

    def token(self):
        t = self.headers.get("x-api-key", "")
        a = self.headers.get("authorization", "")
        return t or (a[7:] if a.lower().startswith("bearer ") else "")

    def user(self):
        t = self.token()
        if not t:
            return None
        return q("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.th=? AND s.created>?",
                 (sha(t), int(time.time()) - SESSION_TTL), one=True)

    def is_admin(self):
        k = self.headers.get("x-admin-key", "")
        if not ADMIN_KEY or too_many("admin:" + self.ip()):
            return False
        ok = hmac.compare_digest(k.encode(), ADMIN_KEY.encode())
        if not ok:
            _fails.setdefault("admin:" + self.ip(), []).append(time.time())
        return ok

    def log_message(self, fmt, *a):
        print("%s %s %s" % (self.ip(), self.command, self.path.split("?")[0]), flush=True)

    # -- routing
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        path, qs = p.path, urllib.parse.parse_qs(p.query)
        try:
            if path == "/":
                return self.out(200, {"ok": True, "service": "bilimai"})
            if path == "/admin":
                with open(os.path.join(HERE, "admin.html"), "rb") as f:
                    return self.out(200, f.read(), "text/html")
            if path in ("/privacy", "/terms"):
                return self.out(200, legal_page(path), "text/html")
            if path == "/me":
                return self.me()
            if path == "/auth/google/start":
                return self.google_start()
            if path == "/auth/google/callback":
                return self.google_callback(qs)
            if path == "/admin/api/stats":
                return self.admin_stats() if self.is_admin() else self.err(401, "auth", "admin key")
            if path == "/admin/api/users":
                return self.admin_users(qs) if self.is_admin() else self.err(401, "auth", "admin key")
            self.err(404, "not_found", "not found")
        except Exception as e:
            self.err(500, "server", str(e))

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            if path == "/v1/messages":
                return self.proxy()
            if path == "/billing/stripe":
                return self.stripe_webhook()
            d = self.body()
            if path == "/auth/register":
                return self.register(d)
            if path == "/auth/login":
                return self.login(d)
            if path == "/auth/logout":
                u = self.user()
                if u:
                    q("DELETE FROM sessions WHERE th=?", (sha(self.token()),), commit=True)
                return self.out(200, {"ok": True})
            if path == "/billing/checkout":
                return self.checkout()
            if path == "/billing/webhook":
                return self.manual_webhook(d)
            if path == "/admin/api/user":
                return self.admin_user(d) if self.is_admin() else self.err(401, "auth", "admin key")
            self.err(404, "not_found", "not found")
        except ValueError as e:
            self.err(400, "bad_request", str(e))
        except Exception as e:
            self.err(500, "server", str(e))

    # -- accounts
    def register(self, d):
        email, pw = str(d.get("email", "")).strip().lower(), str(d.get("password", ""))
        if not EMAIL_RE.match(email):
            return self.err(400, "bad_request", "invalid email")
        if len(pw) < 6:
            return self.err(400, "bad_request", "password must be at least 6 characters")
        if too_many("reg:" + self.ip()):
            return self.err(429, "rate", "too many attempts")
        _fails.setdefault("reg:" + self.ip(), []).append(time.time())
        if q("SELECT 1 FROM users WHERE email=?", (email,), one=True):
            return self.err(409, "exists", "email already registered")
        q("INSERT INTO users(email,pw,created) VALUES(?,?,?)", (email, hash_pw(pw), int(time.time())), commit=True)
        uid = q("SELECT id FROM users WHERE email=?", (email,), one=True)["id"]
        self.out(200, {"token": new_session(uid), "email": email})

    def login(self, d):
        email, pw = str(d.get("email", "")).strip().lower(), str(d.get("password", ""))
        key = "login:%s:%s" % (self.ip(), email)
        if too_many(key):
            return self.err(429, "rate", "too many attempts, try later")
        u = q("SELECT * FROM users WHERE email=?", (email,), one=True)
        if not u or not u["pw"] or not check_pw(pw, u["pw"]):
            _fails.setdefault(key, []).append(time.time())
            return self.err(401, "auth", "wrong email or password")
        if u["banned"]:
            return self.err(403, "banned", "account is blocked")
        self.out(200, {"token": new_session(u["id"]), "email": email})

    def me(self):
        u = self.user()
        if not u:
            return self.err(401, "auth", "invalid or expired session")
        self.out(200, {"email": u["email"], "plan": plan_of(u), "pro_until": u["pro_until"], "used": used_today(u["id"]),
                       "limit": limit_of(u), "can_pay": bool((STRIPE_KEY and STRIPE_PRICE) or PAY_URL)})

    # -- Google OAuth (browser flow; app receives bilimai://auth?token=...)
    def google_start(self):
        if not (GOOGLE_ID and GOOGLE_SECRET and PUBLIC_URL):
            return self.out(404, "Google sign-in is not configured", "text/plain")
        now = time.time()
        for s in [s for s, t in _states.items() if now - t > 600]:
            _states.pop(s, None)
        state = secrets.token_urlsafe(16)
        _states[state] = now
        params = urllib.parse.urlencode({"client_id": GOOGLE_ID, "redirect_uri": PUBLIC_URL + "/auth/google/callback",
                                         "response_type": "code", "scope": "openid email profile", "state": state,
                                         "prompt": "select_account"})
        self.out(302, b"", "text/plain", [("location", GOOGLE_AUTH_URL + "?" + params)])

    def google_callback(self, qs):
        code, state = qs.get("code", [""])[0], qs.get("state", [""])[0]
        if _states.pop(state, 0) < time.time() - 600:
            return self.out(400, "Invalid or expired state. Go back to the app and try again.", "text/plain")
        try:
            tok = http_json(GOOGLE_TOKEN_URL, urllib.parse.urlencode({
                "code": code, "client_id": GOOGLE_ID, "client_secret": GOOGLE_SECRET,
                "redirect_uri": PUBLIC_URL + "/auth/google/callback", "grant_type": "authorization_code"}).encode(),
                {"content-type": "application/x-www-form-urlencoded"})
            c = jwt_payload(tok["id_token"])  # received directly from Google over TLS
        except Exception as e:
            return self.out(400, "Google sign-in failed: %s" % e, "text/plain")
        if c.get("aud") != GOOGLE_ID or not c.get("email_verified") or c.get("exp", 0) < time.time():
            return self.out(400, "Google account could not be verified", "text/plain")
        email, sub = c["email"].lower(), c["sub"]
        u = q("SELECT * FROM users WHERE google_sub=? OR email=?", (sub, email), one=True)
        if u:
            if u["banned"]:
                return self.out(403, "Account is blocked", "text/plain")
            q("UPDATE users SET google_sub=? WHERE id=?", (sub, u["id"]), commit=True)
            uid = u["id"]
        else:
            q("INSERT INTO users(email,google_sub,created) VALUES(?,?,?)", (email, sub, int(time.time())), commit=True)
            uid = q("SELECT id FROM users WHERE email=?", (email,), one=True)["id"]
        link = "bilimai://auth?token=" + new_session(uid)
        page = ('<!doctype html><meta name=viewport content="width=device-width,initial-scale=1"><title>%s</title>'
                '<body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b1530;color:#fff">'
                '<h2>%s</h2><p>Signed in as %s</p><p><a style="background:#2f7df6;color:#fff;padding:14px 22px;'
                'border-radius:10px;text-decoration:none" href="%s">Open %s</a></p>'
                '<script>setTimeout(function(){location.href="%s"},300)</script>') % (
            APP_NAME, APP_NAME, email.replace("<", ""), link, APP_NAME, link)
        self.out(200, page, "text/html")

    # -- billing
    def checkout(self):
        u = self.user()
        if not u:
            return self.err(401, "auth", "invalid or expired session")
        if STRIPE_KEY and STRIPE_PRICE and PUBLIC_URL:
            form = urllib.parse.urlencode({
                "mode": "subscription", "line_items[0][price]": STRIPE_PRICE, "line_items[0][quantity]": "1",
                "success_url": PUBLIC_URL + "/privacy?paid=1", "cancel_url": PUBLIC_URL + "/privacy",
                "client_reference_id": str(u["id"]), "customer_email": u["email"]}).encode()
            auth = base64.b64encode((STRIPE_KEY + ":").encode()).decode()
            try:
                r = http_json(STRIPE_API + "/v1/checkout/sessions", form, {
                    "authorization": "Basic " + auth, "content-type": "application/x-www-form-urlencoded"})
                return self.out(200, {"url": r["url"]})
            except Exception as e:
                return self.err(502, "billing", "payment provider error: %s" % e)
        if PAY_URL:
            sep = "&" if "?" in PAY_URL else "?"
            return self.out(200, {"url": PAY_URL + sep + urllib.parse.urlencode({"email": u["email"]})})
        self.err(404, "billing", "payments are not configured")

    def stripe_webhook(self):
        n = int(self.headers.get("content-length", "0"))
        payload = self.rfile.read(n)
        try:
            parts = dict(p.split("=", 1) for p in self.headers.get("stripe-signature", "").split(","))
            ok = STRIPE_WH and abs(time.time() - int(parts["t"])) < 300 and hmac.compare_digest(
                hmac.new(STRIPE_WH.encode(), parts["t"].encode() + b"." + payload, hashlib.sha256).hexdigest(), parts["v1"])
        except Exception:
            ok = False
        if not ok:
            return self.err(400, "signature", "bad signature")
        ev = json.loads(payload)
        obj = ev.get("data", {}).get("object", {})
        if ev.get("type") == "checkout.session.completed":
            uid, cust = obj.get("client_reference_id"), obj.get("customer")
            if uid and cust:
                q("UPDATE users SET stripe_customer=? WHERE id=?", (cust, int(uid)), commit=True)
        elif ev.get("type") == "invoice.paid":
            u = q("SELECT * FROM users WHERE stripe_customer=? OR email=?",
                  (obj.get("customer", "-"), str(obj.get("customer_email", "")).lower()), one=True)
            if u:
                end = max([ln.get("period", {}).get("end", 0) for ln in obj.get("lines", {}).get("data", [])] or [0])
                until = (end or int(time.time()) + 31 * 86400) + 2 * 86400  # 2 days grace
                q("UPDATE users SET pro_until=MAX(pro_until,?), stripe_customer=? WHERE id=?",
                  (until, obj.get("customer") or u["stripe_customer"], u["id"]), commit=True)
        self.out(200, {"received": True})

    def manual_webhook(self, d):
        if not WEBHOOK_SECRET or not hmac.compare_digest(self.headers.get("x-webhook-secret", "").encode(), WEBHOOK_SECRET.encode()):
            return self.err(401, "auth", "bad secret")
        u = q("SELECT id FROM users WHERE email=?", (str(d.get("email", "")).lower(),), one=True)
        if not u:
            return self.err(404, "not_found", "user not found")
        grant(u["id"], int(d.get("days", 30)))
        self.out(200, {"ok": True})

    # -- proxy to Anthropic
    def proxy(self):
        u = self.user()
        if not u:
            return self.err(401, "auth", "invalid or expired session")
        if u["banned"]:
            return self.err(403, "banned", "account is blocked")
        try:
            body = self.body(40 * 1024 * 1024)
        except ValueError:
            return self.err(400, "bad_request", "bad or too large request")
        plan = plan_of(u)
        if MODELS and body.get("model") not in MODELS:
            return self.err(400, "bad_request", "model not allowed")
        cap = PRO_MAX_TOKENS if plan == "pro" else FREE_MAX_TOKENS
        body["max_tokens"] = min(int(body.get("max_tokens", cap)), cap)
        if plan == "free" and not FREE_WEB:
            body.pop("tools", None)
        with _lock:
            if used_today(u["id"]) >= limit_of(u):
                return self.err(429, "limit", "limit: daily limit reached (%s plan)" % plan)
            q("INSERT INTO usage(user_id,day,req) VALUES(?,?,1) ON CONFLICT(user_id,day) DO UPDATE SET req=req+1",
              (u["id"], today()), commit=True)
        req = urllib.request.Request(UPSTREAM + "/v1/messages", data=json.dumps(body).encode(), headers={
            "content-type": "application/json", "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01"})
        tin = tout = 0
        try:
            with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as r:
                ctype = r.headers.get("content-type", "application/json")
                sse = "event-stream" in ctype
                self.send_response(r.status)
                self.send_header("content-type", ctype)
                self.end_headers()
                buf, whole = b"", b""
                while True:
                    chunk = r.read1(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
                    if not sse:
                        whole += chunk
                        continue
                    buf += chunk
                    lines = buf.split(b"\n")
                    buf = lines.pop()
                    for ln in lines:
                        if ln.startswith(b"data:"):
                            try:
                                ev = json.loads(ln[5:])
                            except ValueError:
                                continue
                            if ev.get("type") == "message_start":
                                tin += ev.get("message", {}).get("usage", {}).get("input_tokens", 0)
                            elif ev.get("type") == "message_delta":
                                tout = max(tout, ev.get("usage", {}).get("output_tokens", 0))
                if whole:
                    try:
                        us = json.loads(whole).get("usage", {})
                        tin, tout = us.get("input_tokens", 0), us.get("output_tokens", 0)
                    except ValueError:
                        pass
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            try:
                self.err(502, "upstream", "upstream error: %s" % e)
            except Exception:
                pass
        if tin or tout:
            q("UPDATE usage SET tin=tin+?, tout=tout+? WHERE user_id=? AND day=?", (tin, tout, u["id"], today()), commit=True)

    # -- admin
    def admin_stats(self):
        t = today()
        s = {"users": q("SELECT COUNT(*) c FROM users", one=True)["c"],
             "pro": q("SELECT COUNT(*) c FROM users WHERE pro_until>?", (int(time.time()),), one=True)["c"],
             "banned": q("SELECT COUNT(*) c FROM users WHERE banned=1", one=True)["c"]}
        r = q("SELECT COALESCE(SUM(req),0) r, COALESCE(SUM(tin),0) i, COALESCE(SUM(tout),0) o FROM usage WHERE day=?", (t,), one=True)
        s.update(req_today=r["r"], tin_today=r["i"], tout_today=r["o"])
        s["days"] = [{"day": x["day"], "req": x["r"], "tin": x["i"], "tout": x["o"]} for x in q(
            "SELECT day, SUM(req) r, SUM(tin) i, SUM(tout) o FROM usage GROUP BY day ORDER BY day DESC LIMIT 14")]
        self.out(200, s)

    def admin_users(self, qs):
        needle = "%" + qs.get("q", [""])[0].lower() + "%"
        rows = q("""SELECT u.*, COALESCE((SELECT req FROM usage WHERE user_id=u.id AND day=?),0) today,
                    COALESCE((SELECT SUM(tin+tout) FROM usage WHERE user_id=u.id),0) tokens
                    FROM users u WHERE email LIKE ? ORDER BY created DESC LIMIT 200""", (today(), needle))
        self.out(200, {"users": [{"id": r["id"], "email": r["email"], "plan": plan_of(r), "pro_until": r["pro_until"],
                                  "banned": bool(r["banned"]), "limit": limit_of(r), "today": r["today"],
                                  "tokens": r["tokens"], "created": r["created"], "google": bool(r["google_sub"])}
                                 for r in rows]})

    def admin_user(self, d):
        uid, act = int(d.get("id", 0)), d.get("action")
        if not q("SELECT 1 FROM users WHERE id=?", (uid,), one=True):
            return self.err(404, "not_found", "user not found")
        if act == "grant":
            grant(uid, int(d.get("days", 30)))
        elif act == "revoke":
            q("UPDATE users SET pro_until=0 WHERE id=?", (uid,), commit=True)
        elif act in ("ban", "unban"):
            q("UPDATE users SET banned=? WHERE id=?", (1 if act == "ban" else 0, uid), commit=True)
            if act == "ban":
                q("DELETE FROM sessions WHERE user_id=?", (uid,), commit=True)
        elif act == "limit":
            v = d.get("limit")
            q("UPDATE users SET limit_override=? WHERE id=?", (None if v in (None, "") else int(v), uid), commit=True)
        elif act == "delete":
            for t in ("sessions", "usage"):
                q("DELETE FROM %s WHERE user_id=?" % t, (uid,), commit=True)
            q("DELETE FROM users WHERE id=?", (uid,), commit=True)
        else:
            return self.err(400, "bad_request", "unknown action")
        self.out(200, {"ok": True})


def legal_page(path):
    title = "Privacy Policy" if path == "/privacy" else "Terms of Use"
    body = ("%s stores your email (or Google account email), a hashed password, your usage counters and, if you subscribe, "
            "payment status. Messages you send are forwarded to the Anthropic API to produce answers and are not stored on our "
            "server. Contact: %s." if path == "/privacy" else
            "%s is provided as is. Answers can be wrong - check important information. Subscriptions renew until cancelled; "
            "contact %s for help.") % (APP_NAME, CONTACT or "the app owner")
    return ("<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><title>%s</title>"
            "<body style='font-family:sans-serif;max-width:640px;margin:40px auto;padding:0 16px'><h1>%s - %s</h1><p>%s</p>"
            "<p><small>Template text - have it reviewed for your country.</small></p>") % (title, APP_NAME, title, body)


if __name__ == "__main__":
    if not ANTHROPIC_KEY or not ADMIN_KEY:
        raise SystemExit("Set ANTHROPIC_API_KEY and ADMIN_KEY (see server/README.md)")
    init_db()
    print("%s server on :%d  db=%s" % (APP_NAME, PORT, DB_PATH), flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()

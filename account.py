"""Accounts: email login/registration, Google sign-in (browser + deep link), plan screen, upgrade."""
import threading
import time
import webbrowser
from urllib.parse import parse_qs, urlparse

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.utils import platform

import client
import config

ANDROID = platform == "android"
if ANDROID:
    from android import activity as android_activity
    from jnius import autoclass


class AccountMixin:
    # ---- setup
    def init_account(self):
        self.login_pop = None
        self.me_info = {}
        if ANDROID:
            android_activity.bind(on_new_intent=self.handle_intent)
            try:  # app was started by the deep link
                self.handle_intent(autoclass("org.kivy.android.PythonActivity").mActivity.getIntent())
            except Exception:
                pass

    def server(self):
        return (config.SERVER_URL or self.cfg.get("server", "")).strip().rstrip("/")

    def account_mode(self):
        return bool(self.server())

    def call_api(self, method, path, body=None, cb=None):
        """Network call in a thread; cb(status, data) runs on the UI thread."""
        def run():
            st, data = client.request(self.server(), method, path, body, self.cfg.get("key", ""))
            if cb:
                Clock.schedule_once(lambda dt: cb(st, data))
        threading.Thread(target=run, daemon=True).start()

    def open_url(self, url):
        if ANDROID:
            try:
                Intent, Uri = autoclass("android.content.Intent"), autoclass("android.net.Uri")
                autoclass("org.kivy.android.PythonActivity").mActivity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                return
            except Exception as e:
                self.info(str(e))
        webbrowser.open(url)

    # ---- flow
    def start_flow(self):
        if self.cfg.get("pin_hash"):
            self.show_lock()
        else:
            self.maybe_login()

    def maybe_login(self):
        if self.account_mode() and not self.cfg.get("key"):
            self.show_login()

    def require_key(self):
        if self.cfg.get("key"):
            return True
        if self.account_mode():
            self.show_login()
        else:
            self.info(self.tt("nokey"))
        return False

    def handle_api_error(self, err):
        """True if the error was handled with a dialog (login / upgrade)."""
        if not self.account_mode():
            return False
        if err.startswith("auth") or "invalid or expired session" in err:
            self.cfg["key"] = ""
            self.save_cfg()
            self.show_login()
            return True
        if err.startswith("limit"):
            self.confirm(self.tt("limit_reached") + "\n" + self.tt("upgrade_q"), self.upgrade)
            return True
        return False

    # ---- login popup
    def show_login(self):
        if self.login_pop:
            return
        th = self.th
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        email = self.text_input(hint_text=self.tt("email"), multiline=False, size_hint_y=None, height=dp(46),
                                padding=(dp(10), dp(13)), input_type="mail")
        pw = self.text_input(hint_text=self.tt("password"), multiline=False, password=True, size_hint_y=None,
                             height=dp(46), padding=(dp(10), dp(13)))
        msg = Label(text="", color=(1, 0.45, 0.45, 1), size_hint_y=None, height=dp(34), font_size=sp(12))
        msg.bind(size=lambda w, s: setattr(w, "text_size", (s[0], None)))
        for w in (email, pw, msg):
            box.add_widget(w)
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        pop = Popup(title=self.tt("login"), content=box, size_hint=(0.92, None), height=dp(380), auto_dismiss=False,
                    background_color=th["popup"])
        self.login_pop = pop
        pop.bind(on_dismiss=lambda *_: setattr(self, "login_pop", None))

        def submit(kind):
            msg.text = self.tt("loading")

            def done(st, d):
                if st == 200 and d.get("token"):
                    self.got_token(d["token"], d.get("email", ""))
                else:
                    msg.text = client.error_text(d) if st else self.tt("network")
            self.call_api("POST", "/auth/" + kind, {"email": email.text, "password": pw.text}, done)
        row.add_widget(self.btn(self.tt("login"), lambda *_: submit("login"), font_size=sp(14)))
        row.add_widget(self.btn(self.tt("register"), lambda *_: submit("register"), font_size=sp(14)))
        box.add_widget(row)
        box.add_widget(self.btn(self.tt("google"), lambda *_: self.open_url(self.server() + "/auth/google/start"),
                                size_hint_y=None, height=dp(46), font_size=sp(14)))
        pw.bind(on_text_validate=lambda *_: submit("login"))
        pop.open()

    def got_token(self, token, email=""):
        self.cfg["key"] = token
        self.save_cfg()
        if self.login_pop:
            self.login_pop.dismiss()
        self.call_api("GET", "/me", None, lambda st, d: self.info("%s %s" % (self.tt("signed_in"), d.get("email", email))) if st == 200 else None)

    def handle_intent(self, intent):
        try:
            data = intent.getData() if intent is not None else None
            if data is None:
                return
            url = str(data.toString())
            if url.startswith("bilimai://auth"):
                tok = parse_qs(urlparse(url).query).get("token", [""])[0]
                if tok:
                    Clock.schedule_once(lambda dt: self.got_token(tok))
        except Exception:
            pass

    # ---- account screen
    def open_account(self, *a):
        if not self.cfg.get("key"):
            return self.show_login()
        self.call_api("GET", "/me", None, self._account_popup)

    def _account_popup(self, st, d):
        if st != 200:
            return self.handle_api_error(client.error_text(d)) or self.info(client.error_text(d))
        th = self.th
        pro = d.get("plan") == "pro"
        lines = [d.get("email", ""), "%s: %s" % (self.tt("plan"), self.tt("pro") if pro else self.tt("free"))]
        if pro:
            lines.append("%s %s" % (self.tt("until"), time.strftime("%Y-%m-%d", time.localtime(d.get("pro_until", 0)))))
        lines.append("%s: %d / %d" % (self.tt("used"), d.get("used", 0), d.get("limit", 0)))
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        box.add_widget(Label(text="\n".join(lines), color=th["text"], font_size=sp(15)))
        pop = Popup(title=self.tt("account"), content=box, size_hint=(0.9, None), height=dp(340), background_color=th["popup"])
        if d.get("can_pay", True):
            box.add_widget(self.btn(self.tt("upgrade") if not pro else self.tt("extend"),
                                    lambda *_: (pop.dismiss(), self.upgrade()), size_hint_y=None, height=dp(46), font_size=sp(14)))
        box.add_widget(self.btn(self.tt("logout"), lambda *_: (pop.dismiss(), self.logout()), size_hint_y=None, height=dp(46),
                                font_size=sp(14)))
        pop.open()

    def upgrade(self, *a):
        def done(st, d):
            if st == 200 and d.get("url"):
                self.open_url(d["url"])
            else:
                self.info(self.tt("pay_unavailable") if st == 404 else client.error_text(d))
        self.call_api("POST", "/billing/checkout", {}, done)

    def logout(self):
        self.call_api("POST", "/auth/logout", {})
        self.cfg["key"] = ""
        self.save_cfg()
        self.maybe_login()

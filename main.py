import json, os, ssl, threading, time, urllib.request, urllib.error, uuid

import certifi
from kivy import kivy_data_dir
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import platform

import hashlib

import study
import config
import util
from account import AccountMixin
from strings import UI, LANGS, MODES, MODE_PROMPTS, LEVELS, LEVEL_PROMPTS

HERE = os.path.dirname(os.path.abspath(__file__))
ANDROID = platform == "android"
REQ_FILE, REQ_VOICE = 4201, 4202
API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"


def P(*a):
    return os.path.join(HERE, *a)


# ---- fonts: DejaVu (Cyrillic/Kazakh/Turkish/etc.) replaces the default font; CJK uses the system font ----
if os.path.exists(P("fonts", "DejaVuSans.ttf")):
    LabelBase.register("Roboto", fn_regular=P("fonts", "DejaVuSans.ttf"), fn_bold=P("fonts", "DejaVuSans-Bold.ttf"))
MONO = P("fonts", "DejaVuSansMono.ttf")
if not os.path.exists(MONO):
    MONO = os.path.join(kivy_data_dir, "fonts", "RobotoMono-Regular.ttf")
CJK_FONT = None
if ANDROID:
    for _p in ("/system/fonts/NotoSansCJK-Regular.ttc", "/system/fonts/NotoSansCJKsc-Regular.otf",
               "/system/fonts/NotoSansSC-Regular.otf", "/system/fonts/NotoSansCJKjp-Regular.otf",
               "/system/fonts/NotoSerifCJK-Regular.ttc", "/system/fonts/DroidSansFallbackFull.ttf",
               "/system/fonts/DroidSansFallback.ttf"):
        if os.path.exists(_p):
            CJK_FONT = _p
            break


def font_for(text):
    return CJK_FONT if (CJK_FONT and util.has_cjk(text)) else "Roboto"


THEMES = {
    "dark": dict(bg="bg_dark.jpg", clear=(0.03, 0.05, 0.1, 1), text=(0.93, 0.95, 0.98, 1), user=(0.12, 0.40, 0.88, 0.96),
                 ai=(0.12, 0.16, 0.25, 0.94), user_text=(1, 1, 1, 1), bar=(0.05, 0.09, 0.18, 0.92),
                 btn=(0.16, 0.24, 0.40, 1), btn_text=(1, 1, 1, 1), inp=(0.10, 0.14, 0.23, 1), inp_text=(1, 1, 1, 1),
                 hint=(0.6, 0.67, 0.78, 1), code="8fe3a8", icode="ffcc66", popup=(0.07, 0.10, 0.18, 1)),
    "light": dict(bg="bg_light.jpg", clear=(0.93, 0.96, 1, 1), text=(0.07, 0.10, 0.17, 1), user=(0.15, 0.46, 0.92, 0.97),
                  ai=(1, 1, 1, 0.95), user_text=(1, 1, 1, 1), bar=(1, 1, 1, 0.92),
                  btn=(0.80, 0.87, 0.97, 1), btn_text=(0.06, 0.12, 0.28, 1), inp=(1, 1, 1, 1), inp_text=(0.05, 0.07, 0.12, 1),
                  hint=(0.4, 0.45, 0.55, 1), code="0b7a4b", icode="a64b00", popup=(0.95, 0.97, 1, 1)),
}
FONT_SIZES = {"S": 14, "M": 16, "L": 19}


# ---------------------------------------------------------------- Android helpers
if ANDROID:
    from android import activity as android_activity
    from jnius import autoclass, cast, PythonJavaClass, java_method

    PythonActivity = autoclass("org.kivy.android.PythonActivity")

    class _InitListener(PythonJavaClass):
        __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]
        __javacontext__ = "app"

        def __init__(self, cb):
            super().__init__()
            self.cb = cb

        @java_method("(I)V")
        def onInit(self, status):
            self.cb(status)

    class Speaker:
        def __init__(self):
            self.tts = None
            self.ready = False
            self.todo = None

        def say(self, text, tag):
            if self.tts is not None and self.ready and self.tts.isSpeaking():
                self.tts.stop()
                return
            self.todo = (text, tag)
            if self.tts is None:
                TTS = autoclass("android.speech.tts.TextToSpeech")
                self._l = _InitListener(self._init)
                self.tts = TTS(PythonActivity.mActivity, self._l)
            elif self.ready:
                self._go()

        def _init(self, status):
            self.ready = status == 0
            if self.ready and self.todo:
                self._go()

        def _go(self):
            text, tag = self.todo
            self.todo = None
            Locale = autoclass("java.util.Locale")
            self.tts.setLanguage(Locale.forLanguageTag(tag))
            self.tts.speak(text[:3900], 0, None, "bilim")

    def prepare_image(src, dst, max_side=1568):
        """Decode, rotate by EXIF, downscale and save as JPEG using Android APIs (no Pillow needed)."""
        BF = autoclass("android.graphics.BitmapFactory")
        Opt = autoclass("android.graphics.BitmapFactory$Options")
        o = Opt()
        o.inJustDecodeBounds = True
        BF.decodeFile(src, o)
        w, h = o.outWidth, o.outHeight
        s = 1
        while max(w, h) // (s * 2) >= max_side:
            s *= 2
        o2 = Opt()
        o2.inSampleSize = s
        bmp = BF.decodeFile(src, o2)
        if bmp is None:
            raise ValueError("cannot decode image")
        deg = 0
        try:
            Exif = autoclass("android.media.ExifInterface")
            ori = Exif(src).getAttributeInt(Exif.TAG_ORIENTATION, 1)
            deg = {6: 90, 3: 180, 8: 270}.get(ori, 0)
        except Exception:
            pass
        Matrix = autoclass("android.graphics.Matrix")
        m = Matrix()
        if deg:
            m.postRotate(float(deg))
        bw, bh = bmp.getWidth(), bmp.getHeight()
        k = min(1.0, float(max_side) / max(bw, bh))
        if k < 1.0:
            m.postScale(k, k)
        Bitmap = autoclass("android.graphics.Bitmap")
        out = Bitmap.createBitmap(bmp, 0, 0, bw, bh, m, True)
        fos = autoclass("java.io.FileOutputStream")(dst)
        out.compress(autoclass("android.graphics.Bitmap$CompressFormat").JPEG, 85, fos)
        fos.close()


# ---------------------------------------------------------------- widgets
class Panel(BoxLayout):
    def __init__(self, color, radius=0, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*color)
            self._r = RoundedRectangle(radius=[radius])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._r.pos, self._r.size = self.pos, self.size


class Opt(SpinnerOption):
    def __init__(self, **kw):
        super().__init__(**kw)
        th = App.get_running_app().th
        self.background_normal = self.background_down = ""
        self.background_color = th["btn"]
        self.color = th["btn_text"]
        self.height = dp(44)


class Msg(BoxLayout):
    """One chat message: bubble (+ Copy/Share/Listen row for assistant)."""

    def __init__(self, app, text, mine, **kw):
        super().__init__(orientation="vertical", size_hint_y=None, spacing=dp(2), **kw)
        th = app.th
        self.app, self.mine, self.raw, self.actions = app, mine, text, None
        self.row = BoxLayout(size_hint_y=None, height=dp(44))
        self.bubble = Panel(th["user"] if mine else th["ai"], radius=dp(14), size_hint_x=0.88,
                            size_hint_y=None, height=dp(44), padding=dp(10))
        self.lbl = Label(markup=True, size_hint_y=None, halign="left", valign="top", font_size=sp(app.fs),
                         color=th["user_text"] if mine else th["text"])
        self.bubble.add_widget(self.lbl)
        gap = Widget(size_hint_x=0.12)
        if mine:
            self.row.add_widget(gap); self.row.add_widget(self.bubble)
        else:
            self.row.add_widget(self.bubble); self.row.add_widget(gap)
        self.add_widget(self.row)
        self.bubble.bind(width=self._wrap)
        self.lbl.bind(texture_size=self._fit)
        self.set_text(text)

    def _wrap(self, *a):
        self.lbl.text_size = (max(self.bubble.width - dp(20), dp(40)), None)

    def _fit(self, *a):
        self.lbl.height = self.lbl.texture_size[1]
        self.bubble.height = self.lbl.height + dp(20)
        self.row.height = self.bubble.height
        self.height = self.row.height + ((self.actions.height + dp(2)) if self.actions else 0)

    def set_text(self, raw):
        self.raw = raw
        th = self.app.th
        self.lbl.font_name = font_for(raw)
        self.lbl.text = util.esc(raw) if self.mine else util.md_to_markup(raw, MONO, th["code"], th["icode"])

    def add_actions(self):
        if self.mine or self.actions or not self.raw:
            return
        a = self.app
        self.actions = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(3), padding=(0, 0, dp(8), 0))
        for key, cb in (("copy", a.copy_text), ("share", a.share_text), ("listen", a.speak_text), ("star", a.add_bookmark)):
            self.actions.add_widget(a.btn(a.tt(key), lambda *_, cb=cb: cb(self.raw), font_size=sp(11)))
        self.add_widget(self.actions)
        self._fit()



# ---------------------------------------------------------------- app
class BilimAi(AccountMixin, App):
    title = "BilimAi"
    icon = P("data", "icon.png")

    # ---- config / chats
    def build(self):
        self.cfg = dict(key="", model=DEFAULT_MODEL, lang="Русский", mode="chat", custom="", theme="dark",
                        size="M", web=False, chat_id="", level="adult", memory="", server="", pin_hash="")
        self.cfg_path = os.path.join(self.user_data_dir, "config.json")
        try:
            with open(self.cfg_path, encoding="utf-8") as f:
                self.cfg.update(json.load(f))
        except Exception:
            pass
        self.chats_dir = os.path.join(self.user_data_dir, "chats")
        self.att_dir = os.path.join(self.user_data_dir, "attachments")
        os.makedirs(self.chats_dir, exist_ok=True)
        os.makedirs(self.att_dir, exist_ok=True)
        Window.softinput_mode = "below_target"

        self.busy = self.cancel = self.dirty = False
        self.stream_text = self.status = ""
        self.cur = None
        self.pending = []
        self.speaker = Speaker() if ANDROID else None
        if ANDROID:
            android_activity.bind(on_activity_result=self.on_result)

        self.chat = self.load_chat(self.cfg.get("chat_id")) or self.new_chat_obj()
        self.root_fl = FloatLayout()
        self.build_ui()
        self.sess = None
        self.locked = False
        self.init_account()
        Clock.schedule_once(lambda dt: self.start_flow(), 0.3)
        return self.root_fl

    @property
    def th(self):
        return THEMES.get(self.cfg["theme"], THEMES["dark"])

    @property
    def fs(self):
        return FONT_SIZES.get(self.cfg["size"], 16)

    def tt(self, key):
        return UI.get(self.cfg["lang"], UI["English"]).get(key) or UI["English"][key]

    def save_cfg(self):
        self.cfg["chat_id"] = self.chat["id"]
        try:
            with open(self.cfg_path, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f)
        except Exception:
            pass

    def new_chat_obj(self):
        return {"id": uuid.uuid4().hex[:12], "title": "", "updated": time.time(), "messages": []}

    def chat_path(self, cid):
        return os.path.join(self.chats_dir, cid + ".json")

    def load_chat(self, cid):
        if not cid:
            return None
        try:
            with open(self.chat_path(cid), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save_chat(self, chat=None):
        chat = chat or self.chat
        if not chat["messages"]:
            return
        try:
            with open(self.chat_path(chat["id"]), "w", encoding="utf-8") as f:
                json.dump(chat, f, ensure_ascii=False)
        except Exception:
            pass

    def list_chats(self):
        out = []
        for fn in os.listdir(self.chats_dir):
            if fn.endswith(".json"):
                c = self.load_chat(fn[:-5])
                if c:
                    out.append(c)
        return sorted(out, key=lambda c: c.get("updated", 0), reverse=True)

    def delete_chat(self, cid):
        try:
            os.remove(self.chat_path(cid))
        except OSError:
            pass
        for fn in os.listdir(self.att_dir):
            if fn.startswith(cid + "_"):
                try:
                    os.remove(os.path.join(self.att_dir, fn))
                except OSError:
                    pass

    # ---- UI building
    def btn(self, text, cb, **kw):
        th = self.th
        b = Button(text=text, background_normal="", background_down="", background_color=th["btn"],
                   color=th["btn_text"], font_size=kw.pop("font_size", sp(13)), **kw)
        b.bind(on_release=cb)
        return b

    def spinner(self, text, values, **kw):
        th = self.th
        return Spinner(text=text, values=values, option_cls=Opt, background_normal="", background_down="",
                       background_color=th["btn"], color=th["btn_text"], font_size=sp(13), **kw)

    def build_ui(self):
        th = self.th
        keep = self.inp.text if getattr(self, "inp", None) else ""
        Window.clearcolor = th["clear"]
        r = self.root_fl
        r.clear_widgets()
        r.add_widget(Image(source=P("data", th["bg"]), fit_mode="cover"))
        main = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(6))
        r.add_widget(main)

        bar = Panel(th["bar"], radius=dp(12), size_hint_y=None, height=dp(50), padding=dp(6), spacing=dp(6))
        bar.add_widget(self.btn(self.tt("chats"), self.open_chats, size_hint_x=0.24))
        mid = BoxLayout(spacing=dp(6))
        mid.add_widget(Image(source=P("data", "icon.png"), size_hint_x=None, width=dp(34)))
        mid.add_widget(Label(text="BilimAi", bold=True, font_size=sp(18), color=th["text"], halign="left"))
        bar.add_widget(mid)
        bar.add_widget(self.btn(self.tt("new"), lambda *_: self.new_chat(), size_hint_x=0.2))
        bar.add_widget(self.btn(self.tt("menu"), self.open_menu, size_hint_x=0.3))
        main.add_widget(bar)

        tools = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.sp_lang = self.spinner(self.cfg["lang"], list(LANGS), size_hint_x=0.36)
        self.sp_lang.bind(text=self.on_lang)
        tools.add_widget(self.sp_lang)
        self.mode_names = {self.tt("m_" + m): m for m in MODES}
        self.sp_mode = self.spinner(self.tt("m_" + self.cfg["mode"]), list(self.mode_names), size_hint_x=0.36)
        self.sp_mode.bind(text=self.on_mode)
        tools.add_widget(self.sp_mode)
        self.btn_web = self.btn(self.tt("web_on" if self.cfg["web"] else "web_off"), self.toggle_web, size_hint_x=0.28)
        tools.add_widget(self.btn_web)
        main.add_widget(tools)

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.chat_box = GridLayout(cols=1, spacing=dp(8), padding=dp(2), size_hint_y=None)
        self.chat_box.bind(minimum_height=self.chat_box.setter("height"))
        self.scroll.add_widget(self.chat_box)
        main.add_widget(self.scroll)

        self.pend_box = BoxLayout(size_hint_y=None, height=0, spacing=dp(4))
        main.add_widget(self.pend_box)

        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(4))
        row.add_widget(self.btn(self.tt("attach"), self.attach, size_hint_x=0.17))
        self.inp = TextInput(text=keep, multiline=False, hint_text=self.tt("hint"), background_normal="",
                             background_active="", background_color=th["inp"], foreground_color=th["inp_text"],
                             hint_text_color=th["hint"], cursor_color=th["inp_text"], font_size=sp(15),
                             padding=(dp(10), dp(14)), write_tab=False)
        self.inp.bind(on_text_validate=self.send, text=self.on_inp_text)
        row.add_widget(self.inp)
        row.add_widget(self.btn(self.tt("voice"), self.voice, size_hint_x=0.17))
        self.btn_send = self.btn(self.tt("stop" if self.busy else "send"), self.send, size_hint_x=0.25)
        row.add_widget(self.btn_send)
        main.add_widget(row)

        self.refresh_pending()
        self.render_chat()

    def on_inp_text(self, _, val):
        self.inp.font_name = font_for(val)

    def render_chat(self):
        self.chat_box.clear_widgets()
        msgs = self.chat["messages"]
        if not msgs:
            self.add_msg(self.tt("welcome"), False, final=True)
        for m in msgs:
            self.add_msg(self.display_text(m), m["role"] == "user", final=True)
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.2)

    def display_text(self, m):
        tags = ["[%s] %s" % (self.tt({"image": "photo", "pdf": "pdf"}.get(a["type"], "file")), a.get("name", ""))
                for a in m.get("atts", [])]
        return "\n".join(tags + ([m["text"]] if m["text"] else []))

    def add_msg(self, text, mine, final=False):
        w = Msg(self, text, mine)
        self.chat_box.add_widget(w)
        if final and not mine:
            w.add_actions()
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.1)
        return w

    # ---- small helpers
    def info(self, text):
        th = self.th
        lbl = Label(text=text, color=th["text"], halign="center", text_size=(dp(260), None))
        Popup(title="", content=lbl, size_hint=(0.85, None), height=dp(150), separator_height=0,
              background_color=th["popup"], auto_dismiss=True).open()

    def confirm(self, text, yes_cb):
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        box.add_widget(Label(text=text, color=self.th["text"]))
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        pop = Popup(title="", content=box, size_hint=(0.85, None), height=dp(190), separator_height=0,
                    background_color=self.th["popup"])
        row.add_widget(self.btn(self.tt("no"), lambda *_: pop.dismiss()))
        row.add_widget(self.btn(self.tt("yes"), lambda *_: (pop.dismiss(), yes_cb())))
        box.add_widget(row)
        pop.open()

    def tag(self):
        return LANGS.get(self.cfg["lang"], LANGS["English"])[1]

    # ---- toolbar callbacks
    def on_lang(self, _, val):
        self.cfg["lang"] = val
        self.save_cfg()
        Clock.schedule_once(lambda dt: self.build_ui(), 0.05)

    def on_mode(self, _, val):
        self.cfg["mode"] = self.mode_names.get(val, "chat")
        self.save_cfg()

    def toggle_web(self, *a):
        self.cfg["web"] = not self.cfg["web"]
        self.btn_web.text = self.tt("web_on" if self.cfg["web"] else "web_off")
        self.save_cfg()

    def new_chat(self):
        if self.busy:
            self.cancel = True
        self.chat = self.new_chat_obj()
        self.pending = []
        self.save_cfg()
        self.build_ui()

    def open_chat(self, cid):
        c = self.load_chat(cid)
        if c:
            if self.busy:
                self.cancel = True
            self.chat, self.pending = c, []
            self.save_cfg()
            self.build_ui()

    # ---- chats popup
    def open_chats(self, *a):
        th = self.th
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        pop = Popup(title=self.tt("chats"), content=box, size_hint=(0.95, 0.85), background_color=th["popup"])
        box.add_widget(self.btn(self.tt("new"), lambda *_: (pop.dismiss(), self.new_chat()),
                                size_hint_y=None, height=dp(44)))
        q = TextInput(hint_text="Search...", multiline=False, size_hint_y=None, height=dp(42), background_normal="",
                      background_active="", background_color=th["inp"], foreground_color=th["inp_text"],
                      hint_text_color=th["hint"], cursor_color=th["inp_text"], padding=(dp(10), dp(11)))
        box.add_widget(q)
        sv = ScrollView()
        lst = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        lst.bind(minimum_height=lst.setter("height"))
        sv.add_widget(lst)
        box.add_widget(sv)
        chats = self.list_chats()

        def fill(*_):
            lst.clear_widgets()
            needle = q.text.strip().lower()
            shown = 0
            for c in chats:
                if needle and needle not in (c.get("title", "").lower() + " " + " ".join(m["text"].lower() for m in c["messages"])):
                    continue
                shown += 1
                r = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
                title = (c.get("title") or self.tt("untitled"))[:30]
                r.add_widget(self.btn(title, lambda *_, i=c["id"]: (pop.dismiss(), self.open_chat(i)), size_hint_x=0.56))
                r.add_widget(self.btn(self.tt("rename"), lambda *_, i=c["id"]: (pop.dismiss(), self.rename_chat(i)),
                                      size_hint_x=0.24, font_size=sp(11)))
                r.add_widget(self.btn(self.tt("delete"), lambda *_, i=c["id"]: (pop.dismiss(), self.ask_delete(i)),
                                      size_hint_x=0.2, font_size=sp(11)))
                lst.add_widget(r)
            if not shown:
                lst.add_widget(Label(text=self.tt("no_chats"), color=th["text"], size_hint_y=None, height=dp(40)))
        q.bind(text=fill)
        fill()
        pop.open()

    def rename_chat(self, cid):
        c = self.load_chat(cid)
        if not c:
            return
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        ti = TextInput(text=c.get("title", ""), multiline=False, size_hint_y=None, height=dp(44))
        box.add_widget(ti)
        pop = Popup(title=self.tt("rename"), content=box, size_hint=(0.9, None), height=dp(190),
                    background_color=self.th["popup"])

        def ok(*_):
            c["title"] = ti.text.strip()[:60] or c["title"]
            self.save_chat(c)
            if cid == self.chat["id"]:
                self.chat["title"] = c["title"]
            pop.dismiss()
        box.add_widget(self.btn(self.tt("save"), ok, size_hint_y=None, height=dp(44)))
        pop.open()

    def ask_delete(self, cid):
        def yes():
            self.delete_chat(cid)
            if cid == self.chat["id"]:
                self.new_chat()
        self.confirm(self.tt("confirm_del"), yes)

    # ---- settings popup
    def open_settings(self, *a):
        th = self.th
        t = self.tt
        grid = GridLayout(cols=1, spacing=dp(6), padding=dp(8), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        def label(txt):
            grid.add_widget(Label(text=txt, color=th["text"], size_hint_y=None, height=dp(24), halign="left",
                                  text_size=(dp(280), None), font_size=sp(13)))

        def ti(text, **kw):
            w = TextInput(text=text, multiline=kw.pop("multiline", False), size_hint_y=None, height=kw.pop("height", dp(44)),
                          background_normal="", background_active="", background_color=th["inp"],
                          foreground_color=th["inp_text"], cursor_color=th["inp_text"], **kw)
            grid.add_widget(w)
            return w

        key = server = None
        if not config.SERVER_URL:
            label(t("key")); key = ti(self.cfg["key"], password=True)
        label(t("model")); model = ti(self.cfg["model"])
        if not config.SERVER_URL:
            label(t("server")); server = ti(self.cfg.get("server", ""))
        themes = {t("dark"): "dark", t("light"): "light"}
        label(t("theme"))
        sp_theme = self.spinner(t(self.cfg["theme"]), list(themes), size_hint_y=None, height=dp(44))
        grid.add_widget(sp_theme)
        sizes = {t("small"): "S", t("medium"): "M", t("large"): "L"}
        label(t("size"))
        sp_size = self.spinner(next(k for k, v in sizes.items() if v == self.cfg["size"]), list(sizes),
                               size_hint_y=None, height=dp(44))
        grid.add_widget(sp_size)
        levels = {t("l_" + l): l for l in LEVELS}
        label(t("level"))
        sp_level = self.spinner(t("l_" + self.cfg.get("level", "adult")), list(levels), size_hint_y=None, height=dp(44))
        grid.add_widget(sp_level)
        label(t("memory")); memory = ti(self.cfg.get("memory", ""), multiline=True, height=dp(90))
        label(t("custom")); custom = ti(self.cfg["custom"], multiline=True, height=dp(90))
        label(t("pin")); pin = ti("", password=True, input_filter="int")

        box = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(4))
        sv = ScrollView()
        sv.add_widget(grid)
        box.add_widget(sv)
        pop = Popup(title=t("settings"), content=box, size_hint=(0.95, 0.9), background_color=th["popup"])

        def save(*_):
            old = (self.cfg["theme"], self.cfg["size"])
            if key is not None:
                self.cfg["key"] = key.text.strip()
            if server is not None:
                self.cfg["server"] = server.text.strip()
            self.cfg.update(model=model.text.strip() or DEFAULT_MODEL, theme=themes[sp_theme.text], size=sizes[sp_size.text],
                            level=levels[sp_level.text], memory=memory.text.strip(), custom=custom.text.strip())
            p = pin.text.strip()
            if p == "0":
                self.cfg["pin_hash"] = ""
            elif len(p) >= 4:
                self.cfg["pin_hash"] = self.pin_hash(p)
            self.save_cfg()
            pop.dismiss()
            if old != (self.cfg["theme"], self.cfg["size"]):
                self.build_ui()
            self.maybe_login()
        box.add_widget(self.btn(t("save"), save, size_hint_y=None, height=dp(46)))
        pop.open()

    # ---- attachments / voice (Android intents)
    def refresh_pending(self):
        self.pend_box.clear_widgets()
        self.pend_box.height = dp(34) if self.pending else 0
        for a in self.pending:
            self.pend_box.add_widget(self.btn("x  " + a.get("name", "")[:14], lambda *_, a=a: self.drop_pending(a),
                                              font_size=sp(11)))

    def drop_pending(self, a):
        if a in self.pending:
            self.pending.remove(a)
        self.refresh_pending()

    def attach(self, *a):
        if not ANDROID:
            return self.info(self.tt("android_only"))
        if len(self.pending) >= 5:
            return
        try:
            Intent = autoclass("android.content.Intent")
            i = Intent(Intent.ACTION_GET_CONTENT)
            i.setType("*/*")
            i.addCategory(Intent.CATEGORY_OPENABLE)
            PythonActivity.mActivity.startActivityForResult(i, REQ_FILE)
        except Exception as e:
            self.info("%s: %s" % (self.tt("err_attach"), e))

    def voice(self, *a):
        if not ANDROID:
            return self.info(self.tt("android_only"))
        try:
            Intent = autoclass("android.content.Intent")
            RI = autoclass("android.speech.RecognizerIntent")
            i = Intent(RI.ACTION_RECOGNIZE_SPEECH)
            i.putExtra(RI.EXTRA_LANGUAGE_MODEL, RI.LANGUAGE_MODEL_FREE_FORM)
            i.putExtra(RI.EXTRA_LANGUAGE, self.tag())
            PythonActivity.mActivity.startActivityForResult(i, REQ_VOICE)
        except Exception:
            self.info(self.tt("err_voice"))

    def on_result(self, req, res, data):
        if req not in (REQ_FILE, REQ_VOICE) or res != -1 or data is None:
            return
        try:
            if req == REQ_FILE:
                uri = data.getData()
                threading.Thread(target=self.read_picked, args=(uri,), daemon=True).start()
            else:
                RI = autoclass("android.speech.RecognizerIntent")
                lst = data.getStringArrayListExtra(RI.EXTRA_RESULTS)
                txt = str(lst.get(0)) if lst is not None and lst.size() > 0 else ""
                Clock.schedule_once(lambda dt: self.add_voice(txt))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.info(str(e)))

    def add_voice(self, txt):
        if txt:
            self.inp.text = (self.inp.text + " " + txt).strip()

    def read_picked(self, uri):
        try:
            cr = PythonActivity.mActivity.getContentResolver()
            mime = str(cr.getType(uri) or "").lower()
            name = "file"
            try:
                cur = cr.query(uri, None, None, None, None)
                if cur is not None:
                    idx = cur.getColumnIndex("_display_name")
                    if idx >= 0 and cur.moveToFirst():
                        name = str(cur.getString(idx))
                    cur.close()
            except Exception:
                pass
            pfd = cr.openFileDescriptor(uri, "r")
            with open("/proc/self/fd/%d" % pfd.getFd(), "rb") as f:
                data = f.read(30 * 1024 * 1024 + 1)
            pfd.close()
            if len(data) > 30 * 1024 * 1024:
                raise ValueError("file > 30 MB")
            low = name.lower()
            base = os.path.join(self.att_dir, "%s_%d" % (self.chat["id"], int(time.time() * 1000)))
            if mime.startswith("image/"):
                with open(base + ".src", "wb") as f:
                    f.write(data)
                prepare_image(base + ".src", base + ".jpg")
                os.remove(base + ".src")
                att = {"type": "image", "path": base + ".jpg", "name": name}
            elif mime == "application/pdf" or low.endswith(".pdf"):
                if len(data) > 20 * 1024 * 1024:
                    raise ValueError("PDF > 20 MB")
                with open(base + ".pdf", "wb") as f:
                    f.write(data)
                att = {"type": "pdf", "path": base + ".pdf", "name": name}
            elif mime.startswith("text/") or low.endswith((".txt", ".md", ".csv", ".json", ".py", ".html", ".xml", ".log", ".kt", ".java", ".js")):
                with open(base + ".txt", "w", encoding="utf-8") as f:
                    f.write(data.decode("utf-8", "replace"))
                att = {"type": "text", "path": base + ".txt", "name": name}
            else:
                raise ValueError("unsupported type: %s" % (mime or name))
            Clock.schedule_once(lambda dt: self.add_pending(att))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.info("%s: %s" % (self.tt("err_attach"), e)))

    def add_pending(self, att):
        self.pending.append(att)
        self.refresh_pending()

    # ---- message actions
    def copy_text(self, text):
        Clipboard.copy(text)
        self.info(self.tt("copied"))

    def share_text(self, text):
        if not ANDROID:
            return self.copy_text(text)
        try:
            Intent = autoclass("android.content.Intent")
            S = autoclass("java.lang.String")
            i = Intent()
            i.setAction(Intent.ACTION_SEND)
            i.setType("text/plain")
            i.putExtra(Intent.EXTRA_TEXT, cast("java.lang.CharSequence", S(text)))
            ch = Intent.createChooser(i, cast("java.lang.CharSequence", S("BilimAi")))
            PythonActivity.mActivity.startActivity(ch)
        except Exception as e:
            self.info(str(e))

    def speak_text(self, text):
        if not self.speaker:
            return self.info(self.tt("android_only"))
        try:
            self.speaker.say(util.plain(text), self.tag())
        except Exception as e:
            self.info(str(e))

    # ---- sending / streaming
    def system_prompt(self):
        mode = self.cfg["mode"]
        base = (self.cfg["custom"] or MODE_PROMPTS["chat"]) if mode == "custom" else MODE_PROMPTS.get(mode, MODE_PROMPTS["chat"])
        lang = LANGS.get(self.cfg["lang"], LANGS["English"])[0]
        extra = LEVEL_PROMPTS.get(self.cfg.get("level", "adult"), "")
        if self.cfg.get("memory"):
            extra += "\nWhat the user told you about themselves (remember it): " + self.cfg["memory"]
        return ("%s\n%s\nReply in %s unless the user asks for another language. Use simple Markdown "
                "(bold, lists, fenced code blocks; no tables). Today is %s.") % (base, extra, lang, time.strftime("%Y-%m-%d"))

    def send(self, *a):
        if self.busy:
            self.cancel = True
            return
        text = self.inp.text.strip()
        if not text and not self.pending:
            return
        if not self.require_key():
            return
        m = {"role": "user", "text": text, "atts": list(self.pending)}
        self.chat["messages"].append(m)
        if not self.chat["title"]:
            self.chat["title"] = (text or m["atts"][0]["name"]).replace("\n", " ")[:40]
        self.chat["updated"] = time.time()
        self.save_chat()
        self.save_cfg()
        self.inp.text = ""
        self.pending = []
        self.refresh_pending()
        if len(self.chat["messages"]) == 1:
            self.chat_box.clear_widgets()
        self.add_msg(self.display_text(m), True)
        self.cur = self.add_msg(self.tt("think"), False)
        self.busy, self.cancel, self.dirty = True, False, False
        self.stream_text = self.status = ""
        self.btn_send.text = self.tt("stop")
        Clock.schedule_interval(self.tick, 0.12)
        threading.Thread(target=self.worker, args=(self.chat, self.cur, self.system_prompt(), self.cfg["key"],
                                                    self.cfg["model"], self.cfg["web"], *self.endpoint()), daemon=True).start()

    def tick(self, dt):
        if not self.dirty or not self.cur:
            return
        self.dirty = False
        follow = self.scroll.scroll_y < 0.08
        self.cur.set_text(self.stream_text or self.tt(self.status or "think"))
        if follow:
            Clock.schedule_once(lambda d: setattr(self.scroll, "scroll_y", 0), 0)

    def worker(self, chat, widget, system, key, model, web, url, headers):
        text, err = "", None
        try:
            body = {"model": model, "max_tokens": 4096, "stream": True, "system": system,
                    "messages": util.build_messages(chat["messages"])}
            if web:
                body["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
            ctx = ssl.create_default_context(cafile=certifi.where())
            with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
                for raw in r:
                    if self.cancel:
                        break
                    ev = util.parse_sse(raw.decode("utf-8", "ignore"))
                    if not ev:
                        continue
                    t = ev.get("type")
                    if t == "content_block_delta":
                        d = ev.get("delta", {})
                        if d.get("type") == "text_delta":
                            text += d.get("text", "")
                            self.stream_text, self.dirty = text, True
                    elif t == "content_block_start":
                        cb = ev.get("content_block", {})
                        if cb.get("type") == "server_tool_use":
                            self.status, self.dirty = "search", True
                        elif cb.get("type") == "text" and text and not text.endswith("\n"):
                            text += "\n\n"
                    elif t == "error":
                        err = ev.get("error", {}).get("message", "error")
                        break
                    elif t == "message_stop":
                        break
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode("utf-8", "ignore"))["error"]["message"]
            except Exception:
                err = "HTTP %s" % e.code
        except Exception as e:
            err = str(e)
        Clock.schedule_once(lambda dt: self.finish(chat, widget, text, err))

    def finish(self, chat, widget, text, err):
        Clock.unschedule(self.tick)
        self.busy = self.cancel = False
        self.cur = None
        if hasattr(self, "btn_send"):
            self.btn_send.text = self.tt("send")
        if text:
            chat["messages"].append({"role": "assistant", "text": text})
            chat["updated"] = time.time()
            self.save_chat(chat)
        handled = bool(err) and self.handle_api_error(err)
        if self.chat is chat and widget.parent:
            if text:
                widget.set_text(text)
                widget.add_actions()
            elif err and not handled:
                widget.set_text("%s: %s" % (self.tt("error"), err))
            else:
                self.chat_box.remove_widget(widget)
            if text and err and not handled:
                self.info("%s: %s" % (self.tt("error"), err))
            Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.1)


    # ================= v0.3: menu, study, saved, export, lock, server =================
    def endpoint(self):
        s = self.server()
        url = (s + "/v1/messages") if s else API_URL
        return url, {"content-type": "application/json", "x-api-key": self.cfg["key"], "anthropic-version": "2023-06-01"}

    def call_once(self, system, user, max_tokens=2000):
        url, headers = self.endpoint()
        body = {"model": self.cfg["model"], "max_tokens": max_tokens, "system": system,
                "messages": [{"role": "user", "content": user}]}
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
        ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
            data = json.load(r)
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")

    def jload(self, name, default):
        try:
            with open(os.path.join(self.user_data_dir, name), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def jsave(self, name, obj):
        try:
            with open(os.path.join(self.user_data_dir, name), "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False)
        except Exception:
            pass

    def text_input(self, **kw):
        th = self.th
        return TextInput(background_normal="", background_active="", background_color=th["inp"],
                         foreground_color=th["inp_text"], hint_text_color=th["hint"], cursor_color=th["inp_text"], **kw)

    def open_menu(self, *a):
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        items = [("study", self.open_study), ("stats", self.open_stats), ("saved", self.open_saved),
                 ("export", self.export_chat), ("settings", self.open_settings)]
        if self.account_mode():
            items.insert(0, ("account", self.open_account))
        pop = Popup(title=self.tt("menu"), content=box, size_hint=(0.85, None), height=dp(len(items) * 54 + 80),
                    background_color=self.th["popup"])
        for key, cb in items:
            box.add_widget(self.btn(self.tt(key), lambda *_, cb=cb: (pop.dismiss(), cb()), size_hint_y=None,
                                    height=dp(46), font_size=sp(14)))
        pop.open()

    # ---- export
    def export_chat(self, *a):
        lines = [("%s: %s" % ("You" if m["role"] == "user" else "BilimAi", self.display_text(m)))
                 for m in self.chat["messages"]]
        if not lines:
            return self.info(self.tt("no_chats"))
        self.share_text("# %s\n\n%s" % (self.chat.get("title") or "BilimAi", "\n\n".join(lines)))

    # ---- saved answers
    def add_bookmark(self, text):
        b = self.jload("bookmarks.json", [])
        b.insert(0, {"id": uuid.uuid4().hex[:8], "text": text, "chat": self.chat.get("title", ""), "ts": time.time()})
        self.jsave("bookmarks.json", b[:300])
        self.info("%s: OK" % self.tt("saved"))

    def open_saved(self, *a):
        th = self.th
        box = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
        pop = Popup(title=self.tt("saved"), content=box, size_hint=(0.95, 0.85), background_color=th["popup"])
        sv = ScrollView()
        lst = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        lst.bind(minimum_height=lst.setter("height"))
        sv.add_widget(lst)
        box.add_widget(sv)
        items = self.jload("bookmarks.json", [])
        if not items:
            lst.add_widget(Label(text=self.tt("no_saved"), color=th["text"], size_hint_y=None, height=dp(40)))
        for it in items:
            prev = it["text"].replace("\n", " ")[:60]
            lst.add_widget(self.btn(prev, lambda *_, it=it: (pop.dismiss(), self.show_saved(it)), size_hint_y=None,
                                    height=dp(46), font_size=sp(12)))
        pop.open()

    def show_saved(self, it):
        th = self.th
        box = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
        sv = ScrollView()
        lbl = Label(text=util.md_to_markup(it["text"], MONO, th["code"], th["icode"]), markup=True, color=th["text"],
                    size_hint_y=None, halign="left", valign="top", font_name=font_for(it["text"]), font_size=sp(self.fs))
        lbl.bind(width=lambda l, w: setattr(l, "text_size", (w - dp(8), None)))
        lbl.bind(texture_size=lambda l, s: setattr(l, "height", s[1] + dp(10)))
        sv.add_widget(lbl)
        box.add_widget(sv)
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        pop = Popup(title=self.tt("saved"), content=box, size_hint=(0.95, 0.85), background_color=th["popup"])

        def delete(*_):
            self.jsave("bookmarks.json", [x for x in self.jload("bookmarks.json", []) if x["id"] != it["id"]])
            pop.dismiss()
        row.add_widget(self.btn(self.tt("copy"), lambda *_: self.copy_text(it["text"])))
        row.add_widget(self.btn(self.tt("share"), lambda *_: self.share_text(it["text"])))
        row.add_widget(self.btn(self.tt("delete"), delete))
        box.add_widget(row)
        pop.open()

    # ---- study: cards, review, stats
    def open_study(self, *a):
        th = self.th
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        pop = Popup(title=self.tt("study"), content=box, size_hint=(0.95, 0.9), background_color=th["popup"])
        ti = self.text_input(hint_text=self.tt("study_hint"), multiline=True, size_hint_y=None, height=dp(110))
        box.add_widget(ti)
        box.add_widget(self.btn(self.tt("make_cards"), lambda *_: (pop.dismiss(), self.make_cards(ti.text.strip())),
                                size_hint_y=None, height=dp(46), font_size=sp(14)))
        box.add_widget(Label(text=self.tt("decks"), color=th["text"], size_hint_y=None, height=dp(26)))
        sv = ScrollView()
        lst = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        lst.bind(minimum_height=lst.setter("height"))
        sv.add_widget(lst)
        box.add_widget(sv)
        decks = self.jload("decks.json", [])

        def drop(did):
            self.jsave("decks.json", [d for d in self.jload("decks.json", []) if d["id"] != did])
            pop.dismiss()
            self.open_study()
        for d in decks:
            r = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
            r.add_widget(self.btn("%s (%d)" % (d["title"][:26], len(d["cards"])),
                                  lambda *_, d=d: (pop.dismiss(), self.start_session(d)), size_hint_x=0.8))
            r.add_widget(self.btn(self.tt("delete"), lambda *_, i=d["id"]: drop(i), size_hint_x=0.2, font_size=sp(11)))
            lst.add_widget(r)
        pop.open()

    def make_cards(self, src):
        if not src:
            src = "\n\n".join(m["text"] for m in self.chat["messages"][-6:] if m["text"])
        if not src.strip():
            return self.info(self.tt("no_cards"))
        if not self.require_key():
            return
        title = src.strip().splitlines()[0][:30]
        self.wait = Popup(title="", content=Label(text=self.tt("loading"), color=self.th["text"]),
                          size_hint=(0.7, None), height=dp(120), auto_dismiss=False, separator_height=0,
                          background_color=self.th["popup"])
        self.wait.open()
        threading.Thread(target=self._cards_worker, args=(src, title), daemon=True).start()

    def _cards_worker(self, src, title):
        lang = LANGS.get(self.cfg["lang"], LANGS["English"])[0]
        system = ("Create 10 study flashcards from the user's material. Reply with ONLY a JSON array of objects "
                  '{"q": "question", "a": "short answer"} and no other text. Write in %s. '
                  "Questions must be specific; answers 1-2 sentences.") % lang
        cards, err = [], None
        try:
            cards = study.parse_cards(self.call_once(system, src[:12000], 3000))
        except urllib.error.HTTPError as e:
            err = "HTTP %s" % e.code
        except Exception as e:
            err = str(e)
        Clock.schedule_once(lambda dt: self._cards_done(cards, title, err))

    def _cards_done(self, cards, title, err):
        self.wait.dismiss()
        if not cards:
            return self.info("%s%s" % (self.tt("err_cards"), (": " + err) if err else ""))
        deck = {"id": uuid.uuid4().hex[:8], "title": title, "cards": cards, "ts": time.time()}
        decks = self.jload("decks.json", [])
        decks.insert(0, deck)
        self.jsave("decks.json", decks[:50])
        self.start_session(deck)

    def start_session(self, deck):
        th = self.th
        self.sess, self.sess_deck, self.sess_saved = study.Session(deck["cards"]), deck, False
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        prog = Label(color=th["hint"], size_hint_y=None, height=dp(24), font_size=sp(13))
        q = Label(color=th["text"], font_size=sp(20), halign="center", valign="middle")
        a = Label(color=th["text"], font_size=sp(17), halign="center", valign="middle")
        for l in (q, a):
            l.bind(size=lambda w, s: setattr(w, "text_size", (s[0], s[1])))
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        pop = Popup(title=deck["title"][:30], content=box, size_hint=(0.95, 0.8), background_color=th["popup"],
                    auto_dismiss=False)
        b_show = self.btn(self.tt("show_answer"), lambda *_: reveal(), font_size=sp(14))
        b_again = self.btn(self.tt("again"), lambda *_: grade(False), font_size=sp(14))
        b_know = self.btn(self.tt("know"), lambda *_: grade(True), font_size=sp(14))
        box.add_widget(prog); box.add_widget(q); box.add_widget(a); box.add_widget(row)
        box.add_widget(self.btn(self.tt("close"), lambda *_: pop.dismiss(), size_hint_y=None, height=dp(40)))
        pop.bind(on_dismiss=lambda *_: self.finish_session())

        def show_card():
            c = self.sess.current()
            prog.text = "%d / %d" % (self.sess.total - len(self.sess.queue) + 1, self.sess.total) if c else ""
            q.text, a.text = c["q"], ""
            q.font_name = font_for(c["q"])
            row.clear_widgets()
            row.add_widget(b_show)

        def reveal():
            c = self.sess.current()
            a.text = c["a"]
            a.font_name = font_for(c["a"])
            row.clear_widgets()
            row.add_widget(b_again); row.add_widget(b_know)

        def grade(known):
            self.sess.answer(known)
            if self.sess.done:
                pop.dismiss()
            else:
                show_card()
        show_card()
        pop.open()

    def finish_session(self):
        s = getattr(self, "sess", None)
        if not s or self.sess_saved or not s.reviewed:
            return
        self.sess_saved = True
        stats = self.jload("stats.json", {})
        today = time.strftime("%Y-%m-%d")
        study.record(stats, today, s.reviewed, s.known, self.sess_deck["title"])
        self.jsave("stats.json", stats)
        if s.done:
            acc = int(100 * s.known / s.reviewed)
            self.info("%s\n%s: %d%%\n%s: %d" % (self.tt("cards_done"), self.tt("accuracy"), acc,
                                                self.tt("streak"), study.streak(stats, today)))

    def open_stats(self, *a):
        th = self.th
        stats = self.jload("stats.json", {})
        today = time.strftime("%Y-%m-%d")
        days = stats.get("days", {})
        tot_r = sum(d["r"] for d in days.values())
        tot_k = sum(d["k"] for d in days.values())
        td = days.get(today, {"r": 0, "k": 0})
        lines = ["%s: %d" % (self.tt("streak"), study.streak(stats, today)),
                 "%s: %d / %d" % (self.tt("today"), td["k"], td["r"]),
                 "%s: %d / %d (%d%%)" % (self.tt("total"), tot_k, tot_r, int(100 * tot_k / tot_r) if tot_r else 0), ""]
        for day in sorted(days)[-7:]:
            r, k = days[day]["r"], days[day]["k"]
            lines.append("%s  %s %d/%d" % (day[5:], "\u2588" * min(20, r // 2 + 1), k, r))
        weak = study.weakest(stats)
        if weak:
            lines += ["", self.tt("weak") + ":"] + ["- %s (%d%%)" % (n[:28], int(100 * v)) for n, v in weak]
        Popup(title=self.tt("stats"), content=Label(text="\n".join(lines), color=th["text"], font_size=sp(15)),
              size_hint=(0.9, 0.7), background_color=th["popup"]).open()

    # ---- PIN lock
    def pin_hash(self, pin):
        return hashlib.sha256(("bilim:" + pin).encode()).hexdigest()

    def show_lock(self):
        if not self.cfg.get("pin_hash") or self.locked:
            return
        self.locked = True
        th = self.th
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        msg = Label(text="", color=(1, 0.4, 0.4, 1), size_hint_y=None, height=dp(24))
        ti = self.text_input(password=True, multiline=False, input_filter="int", size_hint_y=None, height=dp(48),
                             padding=(dp(10), dp(14)))
        box.add_widget(ti); box.add_widget(msg)
        pop = Popup(title=self.tt("app_lock"), content=box, size_hint=(0.85, None), height=dp(230),
                    auto_dismiss=False, background_color=th["popup"])

        def check(*_):
            if self.pin_hash(ti.text.strip()) == self.cfg["pin_hash"]:
                self.locked = False
                pop.dismiss()
                self.maybe_login()
            else:
                msg.text, ti.text = self.tt("wrong_pin"), ""
                Clock.schedule_once(lambda dt: setattr(ti, "focus", True), 0.1)
        ti.bind(on_text_validate=check)
        box.add_widget(self.btn(self.tt("ok"), check, size_hint_y=None, height=dp(44)))
        pop.open()
        Clock.schedule_once(lambda dt: setattr(ti, "focus", True), 0.3)

    def on_pause(self):
        return True

    def on_resume(self):
        self.show_lock()


if __name__ == "__main__":
    BilimAi().run()

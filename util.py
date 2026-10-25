"""Pure helpers (no Kivy imports) so they can be tested anywhere."""
import base64
import re

CJK_RE = re.compile(r"[\u2e80-\u9fff\uac00-\ud7af\uff00-\uffef]")


def has_cjk(s):
    return bool(CJK_RE.search(s or ""))


def esc(s):
    return s.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def _inline(s, mono, ic):
    s = esc(s)
    out = []
    for ln in s.split("\n"):
        m = re.match(r"^\s{0,3}#{1,6}\s+(.*)$", ln)
        if m:
            ln = "[b]" + m.group(1) + "[/b]"
        else:
            ln = re.sub(r"^(\s*)[-*+]\s+", "\\1\u2022 ", ln)
        out.append(ln)
    s = "\n".join(out)
    s = re.sub(r"\*\*(.+?)\*\*", r"[b]\1[/b]", s, flags=re.S)
    s = re.sub(r"`([^`\n]+)`",
               lambda m: "[font=%s][color=%s]%s[/color][/font]" % (mono, ic, m.group(1)), s)
    s = re.sub(r"(?<![\w*])\*(?![\s*])([^*\n]+?)(?<![\s*])\*(?![\w*])", r"\1", s)
    return s


def md_to_markup(text, mono, code_color="8fe3a8", inline_color="ffcc66"):
    """Small Markdown subset -> Kivy markup: **bold**, `code`, ```blocks```, lists, headings."""
    parts = text.split("```")
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 0:
            out.append(_inline(p, mono, inline_color))
        else:
            code = p
            if "\n" in code:
                first, rest = code.split("\n", 1)
                if re.fullmatch(r"\s*[\w+#.\-]*\s*", first):
                    code = rest
            out.append("\n[font=%s][color=%s]%s[/color][/font]\n" % (mono, code_color, esc(code.strip("\n"))))
    return "".join(out)


def plain(text):
    """Strip Markdown so text can be read aloud."""
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[*#`_>|]+", "", t)
    return re.sub(r"\n{2,}", "\n", t).strip()


def parse_sse(line):
    """'data: {...}' -> dict or None."""
    import json
    line = line.strip()
    if not line.startswith("data:"):
        return None
    body = line[5:].strip()
    if not body or body == "[DONE]":
        return None
    try:
        return json.loads(body)
    except ValueError:
        return None


def attachment_blocks(att):
    """Attachment dict -> list of Anthropic content blocks."""
    kind, path, name = att["type"], att["path"], att.get("name", "file")
    if kind == "image":
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}}]
    if kind == "pdf":
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return [{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}}]
    with open(path, encoding="utf-8", errors="replace") as f:
        txt = f.read(100000)
    return [{"type": "text", "text": "File %s:\n%s" % (name, txt)}]


def build_messages(messages, loader=attachment_blocks, keep_media=4, limit=40):
    """Stored chat messages -> API messages. Only the latest `keep_media` user
    messages keep their real attachments (saves tokens); older ones become notes."""
    msgs = messages[-limit:]
    while msgs and msgs[0]["role"] != "user":
        msgs = msgs[1:]
    with_att = [i for i, m in enumerate(msgs) if m["role"] == "user" and m.get("atts")]
    fresh = set(with_att[-keep_media:])
    out = []
    for i, m in enumerate(msgs):
        if m["role"] == "assistant" or not m.get("atts"):
            out.append({"role": m["role"], "content": m["text"]})
            continue
        blocks = []
        for a in m["atts"]:
            if i in fresh:
                try:
                    blocks.extend(loader(a))
                except OSError:
                    blocks.append({"type": "text", "text": "[attachment missing: %s]" % a.get("name", "")})
            else:
                blocks.append({"type": "text", "text": "[earlier attachment omitted: %s]" % a.get("name", "")})
        blocks.append({"type": "text", "text": m["text"] or "(see attachment)"})
        out.append({"role": "user", "content": blocks})
    return out

"""Generates icon, splash and backgrounds for BilimAi (needs Pillow). Run: python make_assets.py"""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

C1, C2, C3 = (9, 24, 66), (22, 92, 190), (0, 201, 167)  # navy -> blue -> teal


def gradient(w, h, stops, diagonal=True):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = (x / w * 0.5 + y / h * 0.5) if diagonal else y / h
            if t < 0.5:
                a, b, k = stops[0], stops[1], t * 2
            else:
                a, b, k = stops[1], stops[2], (t - 0.5) * 2
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))
    return img


def star4(cx, cy, R, r=None):
    r = r or R * 0.26
    pts = []
    for i in range(8):
        ang = math.radians(-90 + i * 45)
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return pts


def logo(size=1024):
    """Open book with sparkles on a transparent canvas."""
    S = 2048
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = S / 1024
    def P(pts): return [(x * k, y * k) for x, y in pts]
    # shadow
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon(P([(150, 470), (512, 535), (874, 470), (874, 800), (512, 865), (150, 800)]), fill=(0, 0, 40, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18 * k)))
    # cover
    d.polygon(P([(140, 440), (512, 505), (884, 440), (884, 790), (512, 860), (140, 790)]), fill=(8, 40, 110, 255))
    # pages
    d.polygon(P([(175, 410), (500, 470), (500, 810), (175, 750)]), fill=(255, 255, 255, 255))
    d.polygon(P([(849, 410), (524, 470), (524, 810), (849, 750)]), fill=(232, 244, 255, 255))
    d.polygon(P([(500, 470), (524, 470), (524, 810), (500, 810)]), fill=(120, 170, 230, 255))
    # text lines
    for i in range(5):
        y = 520 + i * 52
        d.rounded_rectangle([x * k for x in (225, y, 455, y + 14)], radius=7 * k, fill=(60, 120, 220, 255))
        d.rounded_rectangle([x * k for x in (570, y, 800, y + 14)], radius=7 * k, fill=(0, 190, 160, 255))
    # sparkles
    gold = (255, 213, 79, 255)
    d.polygon([(x * k, y * k) for x, y in star4(512, 270, 170)], fill=gold)
    d.polygon([(x * k, y * k) for x, y in star4(715, 250, 70)], fill=(255, 236, 160, 255))
    d.polygon([(x * k, y * k) for x, y in star4(318, 290, 55)], fill=(255, 236, 160, 255))
    return im.resize((size, size), Image.LANCZOS)


def with_logo(bg, scale):
    n = bg.size[0]
    lg = logo(int(n * scale))
    bg = bg.convert("RGBA")
    bg.alpha_composite(lg, ((n - lg.size[0]) // 2, (n - lg.size[1]) // 2))
    return bg


def sparkle_bg(w, h, dark=True, seed=7):
    random.seed(seed)
    if dark:
        base = gradient(w, h, [(7, 12, 30), (12, 30, 70), (6, 50, 62)], diagonal=False)
    else:
        base = gradient(w, h, [(232, 243, 255), (243, 249, 255), (226, 248, 242)], diagonal=False)
    base = base.convert("RGBA")
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(9):  # soft glows
        cx, cy, r = random.randint(0, w), random.randint(0, h), random.randint(w // 5, w // 2)
        col = (30, 120, 230, 40) if dark else (80, 160, 240, 45)
        if random.random() < 0.4:
            col = (0, 200, 165, 34) if dark else (0, 200, 165, 40)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    ov = ov.filter(ImageFilter.GaussianBlur(w // 12))
    base.alpha_composite(ov)
    d2 = ImageDraw.Draw(base)
    for _ in range(26):  # tiny stars
        x, y, R = random.randint(0, w), random.randint(0, h), random.randint(5, 14)
        col = (255, 255, 255, random.randint(35, 90)) if dark else (30, 110, 220, random.randint(25, 60))
        d2.polygon(star4(x, y, R), fill=col)
    return base.convert("RGB")


# --- icons ---
full = with_logo(gradient(1024, 1024, [C1, C2, C3]), 0.86)
full.convert("RGB").resize((512, 512), Image.LANCZOS).save("data/icon.png")
lg = logo(432)  # adaptive foreground: logo inside the safe zone (66%)
fg = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
small = lg.resize((int(432 * 0.66), int(432 * 0.66)), Image.LANCZOS)
fg.alpha_composite(small, ((432 - small.size[0]) // 2, (432 - small.size[1]) // 2))
fg.save("data/icon_fg.png")
gradient(432, 432, [C1, C2, C3]).save("data/icon_bg.png")

# --- splash ---
W, H = 1080, 1920
sp = sparkle_bg(W, H, dark=True, seed=3).convert("RGBA")
lg = logo(620)
sp.alpha_composite(lg, ((W - 620) // 2, 520))
dr = ImageDraw.Draw(sp)
try:
    f = ImageFont.truetype("fonts/DejaVuSans-Bold.ttf", 130)
    f2 = ImageFont.truetype("fonts/DejaVuSans.ttf", 48)
    for txt, font, y, col in (("BilimAi", f, 1180, (255, 255, 255, 255)), ("Білім · Знание · Knowledge", f2, 1350, (160, 220, 255, 255))):
        w = dr.textlength(txt, font=font)
        dr.text(((W - w) / 2, y), txt, font=font, fill=col)
except Exception as e:
    print("font skipped:", e)
sp.convert("RGB").save("data/presplash.png")

# --- in-app backgrounds ---
sparkle_bg(540, 960, True, 11).save("data/bg_dark.jpg", quality=82)
sparkle_bg(540, 960, False, 12).save("data/bg_light.jpg", quality=85)
print("ok")

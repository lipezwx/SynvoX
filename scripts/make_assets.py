"""Generates the Synvox brand assets (logo PNG/SVG, app icon PNG/ICO) from code.

    python scripts/make_assets.py

Palette: Ink #0D1311 / Cream #F6EECA.
"""
import os
from PIL import Image, ImageDraw, ImageFont

INK, CREAM = (13, 19, 17), (246, 238, 202)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "synvox_invoice", "assets")
SS = 4  # supersampling factor for smooth edges


def draw_mark(d, cx, cy, r, w, color):
    """The Synvox S: two stacked arcs forming one stroke, r = centerline radius, w = stroke width.
    Drawn by stamping round dots along the centerline (round caps and joins for free).
    Angles are screen angles: clockwise from 3 o'clock."""
    import math
    for ccx, ccy, a0, a1 in ((cx, cy - r, 90, 330), (cx, cy + r, 270, 510)):
        steps = int((a1 - a0) * 2)
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            x, y = ccx + r * math.cos(a), ccy + r * math.sin(a)
            d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=color)


def icon(size, bg=INK, fg=CREAM):
    s = size * SS
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.22), fill=bg + (255,))
    frame = int(s * 0.07)
    d.rounded_rectangle((frame, frame, s - 1 - frame, s - 1 - frame), radius=int(s * 0.17),
                        outline=fg + (255,), width=max(2, int(s * 0.03)))
    r = s * 0.14
    draw_mark(d, s / 2, s / 2, r, int(s * 0.075), fg + (255,))
    return im.resize((size, size), Image.LANCZOS)


def find_font(size):
    for name in ("seguibl.ttf", "Inter-Black.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def logo(height=256):
    """Horizontal lockup: framed mark + SYNVOX wordmark, cream on transparent."""
    h = height * SS
    font = find_font(int(h * 0.50))
    text_w = int(ImageDraw.Draw(Image.new("L", (1, 1))).textlength("SYNVOX", font=font))
    w = h + int(h * 0.22) + text_w + int(h * 0.06)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((int(h * .03), int(h * .03), h - int(h * .03), h - int(h * .03)),
                        radius=int(h * .24), outline=CREAM + (255,), width=int(h * .045))
    r = h * 0.14
    draw_mark(d, h / 2, h / 2, r, int(h * 0.075), CREAM + (255,))
    d.text((h + int(h * .22), h / 2), "SYNVOX", font=font, fill=CREAM + (255,), anchor="lm")
    return im.resize((w // SS, h // SS), Image.LANCZOS)


SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <rect width="512" height="512" rx="113" fill="#0D1311"/>
  <rect x="36" y="36" width="440" height="440" rx="87" fill="none" stroke="#F6EECA" stroke-width="15"/>
  <path d="M 318 148 A 72 72 0 1 0 256 256 A 72 72 0 1 1 194 364"
        fill="none" stroke="#F6EECA" stroke-width="38" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    big = icon(512)
    big.save(os.path.join(OUT, "synvox_icon.png"))
    big.save(os.path.join(OUT, "synvox_icon.ico"),
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    logo().save(os.path.join(OUT, "synvox_logo.png"))
    with open(os.path.join(OUT, "synvox_icon.svg"), "w", encoding="utf-8") as f:
        f.write(SVG)
    print("assets written to", os.path.abspath(OUT))

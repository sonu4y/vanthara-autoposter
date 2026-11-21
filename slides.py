"""Render 1080x1350 (4:5) Instagram carousel slides with a text banner."""
from PIL import Image, ImageDraw
from reel import _font, _wrap
from config import PHONE

W, H = 1080, 1350


def render_slide(photo, text, out, last=False):
    im = Image.open(photo).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((l, t, l + W, t + H)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(420):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(170 * (1 - y / 420))))
        d.line([(0, H - 1 - y), (W, H - 1 - y)], fill=(0, 0, 0, int(170 * (1 - y / 420))))
    f = _font(66)
    y = 90
    for ln in _wrap(d, text, f, W - 120):
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2 + 3, y + 3), ln, font=f, fill=(0, 0, 0, 200))
        d.text(((W - w) / 2, y), ln, font=f, fill=(255, 255, 255, 255))
        y += 84
    f2 = _font(44)
    foot = "VanThara Homestay | Hyderabad"
    w = d.textlength(foot, font=f2)
    d.text(((W - w) / 2, H - 150), foot, font=f2, fill=(255, 215, 120, 255))
    if last:
        c = f"WhatsApp {PHONE}"
        w = d.textlength(c, font=_font(42))
        d.text(((W - w) / 2, H - 90), c, font=_font(42), fill=(255, 255, 255, 255))
    Image.alpha_composite(im, ov).convert("RGB").save(out, quality=92)
    return out

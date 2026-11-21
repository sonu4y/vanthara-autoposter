"""Render a 1080x1920 reel (Ken-Burns photos + text overlays) with Pillow + ffmpeg."""
import glob, os, random, subprocess
from PIL import Image, ImageDraw, ImageFont
from config import REEL_SECONDS_PER_PHOTO, MUSIC_DIR, PHONE

W, H = 1080, 1920
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _font(size):
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def _wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _frame(photo_path, out_path):
    """Cover-crop photo to 1350x2400 (headroom for zoom)."""
    im = Image.open(photo_path).convert("RGB")
    tw, th = 1350, 2400
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2
    im.crop((l, t, l + tw, t + th)).save(out_path, quality=92)


def _overlay(text, out_path, last=False):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # gradient bands for legibility
    for y in range(520):
        a = int(170 * (1 - y / 520))
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
        d.line([(0, H - 1 - y), (W, H - 1 - y)], fill=(0, 0, 0, a))
    f = _font(78 if not last else 68)
    lines = _wrap(d, text, f, W - 140)
    y = 190
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2 + 3, y + 3), ln, font=f, fill=(0, 0, 0, 200))
        d.text(((W - w) / 2, y), ln, font=f, fill=(255, 255, 255, 255))
        y += 100
    f2 = _font(50)
    foot = "VanThara Homestay | Hyderabad"
    w = d.textlength(foot, font=f2)
    d.text(((W - w) / 2, H - 210), foot, font=f2, fill=(255, 215, 120, 255))
    if last:
        f3 = _font(46)
        c = f"WhatsApp {PHONE}"
        w = d.textlength(c, font=f3)
        d.text(((W - w) / 2, H - 140), c, font=f3, fill=(255, 255, 255, 255))
    ov.save(out_path)


def render(photo_paths, lines, out_mp4, workdir="cache/work"):
    os.makedirs(workdir, exist_ok=True)
    secs = REEL_SECONDS_PER_PHOTO
    fps = 30
    frames = int(secs * fps)
    clips = []
    for i, p in enumerate(photo_paths):
        base = f"{workdir}/f{i}.jpg"
        ovl = f"{workdir}/o{i}.png"
        _frame(p, base)
        _overlay(lines[min(i, len(lines) - 1)] if i < len(photo_paths) - 1 else lines[-1], ovl, last=(i == len(photo_paths) - 1))
        clip = f"{workdir}/c{i}.mp4"
        zoom_in = i % 2 == 0
        z = (f"min(zoom+0.0009,1.12)" if zoom_in else f"if(eq(on,0),1.12,max(zoom-0.0009,1.0))")
        vf = (f"[0:v]zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={fps}[bg];"
              f"[bg][1:v]overlay=0:0,format=yuv420p[v]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", ovl, "-filter_complex", vf,
                        "-map", "[v]", "-t", str(secs), "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", clip], check=True)
        clips.append(clip)
    lst = f"{workdir}/list.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in clips))
    silent = f"{workdir}/silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    music = sorted(glob.glob(os.path.join(MUSIC_DIR, "*.mp3")))
    total = secs * len(clips)
    if music:
        m = random.choice(music)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-stream_loop", "-1", "-i", m, "-t", str(total),
                        "-af", f"afade=t=out:st={total-1.5}:d=1.5,volume=0.8", "-c:v", "copy", "-c:a", "aac", "-shortest", out_mp4], check=True)
    else:
        # silent AAC track so Instagram/YouTube accept the file cleanly
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-t", str(total), "-c:v", "copy", "-c:a", "aac", "-shortest", out_mp4], check=True)
    return out_mp4

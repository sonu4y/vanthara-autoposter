"""Find and download photos from the website."""
import os, re, requests
from PIL import Image
from config import SITE, FALLBACK_PHOTOS, SKIP_PHOTOS

CACHE = "cache/photos"


def discover():
    """Return {stem: absolute_url}. Scrapes homepage + gallery pages, falls back to the known list."""
    found = {}
    pages = [SITE + "/", SITE + "/experience/", SITE + "/area-guide/"]
    for p in pages:
        try:
            html = requests.get(p, timeout=20).text
        except Exception:
            continue
        for m in re.findall(r'(?:src|href|content)=["\']([^"\']+\.(?:jpe?g|png|webp))["\']', html, re.I):
            url = m if m.startswith("http") else SITE + "/" + m.lstrip("/")
            name = os.path.basename(url.split("?")[0])
            if name not in SKIP_PHOTOS and url.startswith(SITE):
                found[os.path.splitext(name)[0]] = url
    for f in FALLBACK_PHOTOS:
        found.setdefault(os.path.splitext(f)[0], f"{SITE}/{f}")
    return found


def download(stem, url):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, os.path.basename(url.split("?")[0]))
    if not os.path.exists(path):
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        open(path, "wb").write(r.content)
    return path


def demo_photos(stems):
    """Synthetic stand-in photos for offline testing."""
    os.makedirs(CACHE, exist_ok=True)
    out = {}
    for i, s in enumerate(stems):
        path = os.path.join(CACHE, s + ".jpg")
        if not os.path.exists(path):
            im = Image.new("RGB", (1600, 1068))
            px = im.load()
            for x in range(0, 1600, 4):
                for y in range(0, 1068, 4):
                    c = ((x * 255) // 1600 + i * 40) % 256, (y * 255) // 1068, (180 + i * 20) % 256
                    for dx in range(4):
                        for dy in range(4):
                            px[x + dx, y + dy] = c
            im.save(path, quality=90)
        out[s] = path
    return out

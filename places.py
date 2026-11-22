"""Fetch reusable photos of nearby attractions from Wikimedia Commons.
Only public-domain / CC0 / CC BY images are used (no share-alike, no non-commercial),
and the photographer credit is returned so it can go in the caption."""
import hashlib, html, os, random, re, datetime, requests

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "VanTharaHomestayAutoposter/1.0 (https://vantharahomestay.com; bot@users.noreply.github.com)"}
CACHE = "cache/places"
BAD_WORDS = re.compile(r"\b(map|logo|flag|diagram|poster|stamp|coat of arms|icon|plan|ticket|signature|svg|screenshot)\b", re.I)


def _license_ok(name):
    n = (name or "").strip().lower()
    if n.startswith("cc0") or n.startswith("public domain") or n.startswith("pd"):
        return True
    return bool(re.match(r"^cc[- ]by[- ]?\d", n))   # CC BY 2.0 / 3.0 / 4.0 only


def _strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def search(query, limit=40, width=1600, min_w=1200):
    r = requests.get(API, headers=UA, timeout=30, params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": width,
        "iiextmetadatafilter": "LicenseShortName|Artist"})
    r.raise_for_status()
    out = []
    for p in (r.json().get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        title = p.get("title", "")
        if ii.get("mime") != "image/jpeg" or not _license_ok(lic) or BAD_WORDS.search(title):
            continue
        if ii.get("width", 0) < min_w or ii.get("height", 0) < 800:
            continue
        artist = _strip(md.get("Artist", {}).get("value", "")) or "Unknown"
        out.append(dict(title=title, url=ii.get("thumburl") or ii["url"], license=lic, artist=artist[:60]))
    return out


def fetch(query, n=3, seed=None, width=1600, min_w=1200, exclude=()):
    """Return up to n dicts {path, credit}. Picks vary by day so repeat cycles look different."""
    found = [f for f in search(query, width=width, min_w=min_w) if f["title"] not in exclude]
    random.Random(datetime.date.today().toordinal() if seed is None else seed).shuffle(found)
    os.makedirs(CACHE, exist_ok=True)
    res = []
    for f in found:
        if len(res) >= n:
            break
        path = os.path.join(CACHE, hashlib.md5(f["url"].encode()).hexdigest() + ".jpg")
        try:
            if not os.path.exists(path):
                r = requests.get(f["url"], headers=UA, timeout=60)
                r.raise_for_status()
                open(path, "wb").write(r.content)
        except Exception as e:
            print("skip photo:", e)
            continue
        res.append(dict(path=path, credit=f"{f['artist']} / Wikimedia Commons ({f['license']})", title=f["title"]))
    return res

"""Build a ~3 minute story film: friends' road trip -> Ramoji, Wonderla, Hyderabad -> VanThara villa.
Renders widescreen (YouTube) + vertical (Instagram) with motion, crossfades, narration and captions.
  python film.py --demo             # offline test with synthetic media
  python film.py                    # render for real (needs internet: Wikimedia, Pexels, edge-tts)
  python film.py --post             # ...and publish to YouTube + Instagram
Env: PEXELS_API_KEY (stock car/road clips), YT_*, IG_* (only for --post)."""
import argparse, asyncio, glob, os, random, re, subprocess, sys
import requests
from PIL import Image, ImageDraw, ImageFilter
import config, content, places, sources
from reel import _font, _wrap

FPS, XF = 25, 0.7
FORMATS = {"wide": (1920, 1080), "tall": (1080, 1920)}
VOICE = "en-IN-NeerjaNeural"
WORK = "cache/film"
SEED = 2026
MIN_PHOTO = 4.5      # seconds each photo stays on screen (at least)
VIL = "VanThara Homestay"

V = lambda *s: list(s)
SCENES = [
    dict(id="intro", kind="places", style="title", chapter="Intro",
         groups=[dict(q=["Hyderabad skyline", "Hussain Sagar Hyderabad"], n=2, cap=("A Day in Hyderabad", "Six friends. One weekend."))],
         fb_villa=["villa-exterior-corner-view"],
         narr="Hyderabad. Six friends. One weekend. And a plan that fits inside a single car."),
    dict(id="car", kind="clip", chapter="The road trip begins", q=["friends road trip car", "friends in car driving", "group of friends car"],
         cap=("The road trip begins", ""),
         narr="It starts the way every good trip starts. Everyone in the car, the playlist too loud, and nobody quite sure who is navigating."),
    dict(id="orr", kind="clip", chapter="Outer Ring Road", q=["highway driving", "car driving on highway", "road trip highway"],
         cap=("Outer Ring Road", "The city falls away"),
         narr="Out on the Outer Ring Road the city falls away. First stop, Ramoji Film City, about thirty minutes from the villa where we will sleep tonight."),
    dict(id="ramoji", kind="places", chapter="Ramoji Film City",
         groups=[dict(q=["Film sets in Ramoji Film City", "Ramoji Film City"], n=5, cap=("Ramoji Film City", "About 30 min from VanThara Homestay"))],
         narr="Ramoji Film City. Streets, palaces and gardens built for the movies, and for one day, you get to walk through all of them."),
    dict(id="car2", kind="clip", chapter=None, q=["car driving road window", "driving car road trip", "car on road"],
         cap=("Next stop", "Wonderla"),
         narr="Back on the road. Next up, Wonderla, just twenty minutes from the villa."),
    dict(id="wonderla", kind="places", chapter="Wonderla",
         groups=[dict(q=["Wonderla Hyderabad", "Wonderla amusement park Hyderabad", "Wonderla"], n=5, cap=("Wonderla Hyderabad", "About 20 min from VanThara Homestay"))],
         narr="Wonderla. Rides that make you scream, a water park that makes you forget the heat, and the kind of laughter you cannot fake."),
    dict(id="city", kind="places", chapter="More of Hyderabad",
         groups=[dict(q=["Charminar Hyderabad", "Charminar"], n=2, cap=("Charminar", "About 35 min from VanThara Homestay")),
                 dict(q=["Golconda Fort"], n=2, cap=("Golconda Fort", "About 50 min from VanThara Homestay")),
                 dict(q=["Hussain Sagar Buddha statue", "Hussain Sagar"], n=1, cap=("Hussain Sagar", "About 45 min from VanThara Homestay"))],
         narr="And Hyderabad still has more. The bazaars around Charminar. The old walls of Golconda. Hussain Sagar at dusk. All of it within an easy drive."),
    dict(id="sunset", kind="clip", chapter=None, q=["driving at sunset road", "sunset car drive", "golden hour road driving"],
         cap=("Time to go home", ""),
         narr="As the light turns gold, the car goes quiet. Then someone says it. Let us go home."),
    dict(id="arrival", kind="villa", chapter="Arriving at VanThara",
         photos=[("grand-entrance-gate", (VIL, "Turkayamjal, Hyderabad")), ("villa-exterior-corner-view", (VIL, "Your private 5 BHK villa"))],
         narr="VanThara Homestay. A private five bedroom villa in Turkayamjal. And tonight, the whole place is yours."),
    dict(id="tour", kind="villa", chapter="Inside the villa",
         photos=[("home-theater-living-room", ("Home theatre", "75-inch 4K screen, surround sound")),
                 ("gallery-lounge", ("Lounge", "Room for the whole group")),
                 ("gallery-kitchen", ("Kitchen", "Cook and eat together")),
                 ("rooftop-terrace", ("Rooftop terrace", "Made for late conversations")),
                 ("private-gym-room", ("Private gym", "Stay fit while you stay")),
                 ("bedroom-wooden-bed", ("5 AC bedrooms", "Across 3 floors")),
                 ("bedroom-with-ac-and-shelves", ("Comfortable rooms", "Room for 15+ guests")),
                 ("gallery-staircase", (VIL, "Turkayamjal, Hyderabad"))],
         narr="A seventy five inch four K home theatre with surround sound. A kitchen big enough to cook together. A rooftop terrace made for late conversations. A private gym. And five air conditioned bedrooms across three floors, with room for fifteen guests."),
    dict(id="end", kind="villa", chapter="Book your stay", style="end",
         photos=[("rooftop-terrace", ("Book the whole villa", f"{VIL} | Turkayamjal, Hyderabad")), ("villa-exterior-corner-view", ("Book the whole villa", config.PHONE))],
         narr="Weekend trips, wedding guests, team offsites and birthdays. Book the whole villa. VanThara Homestay, Turkayamjal, Hyderabad. WhatsApp plus nine one, seven seven three five, seven two six, six zero three."),
]


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr[-800:]}")
    return r.stdout


def dur(path):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())


# ---------- media sources ----------
def pexels(queries, orient, need, used):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    os.makedirs(f"{WORK}/pexels", exist_ok=True)
    for q in queries:
        try:
            r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key}, timeout=30,
                             params=dict(query=q, orientation=orient, size="large", per_page=20))
            r.raise_for_status()
        except Exception as e:
            print("pexels error:", e)
            continue
        for v in r.json().get("videos", []):
            if v["id"] in used or v.get("duration", 0) < min(need, 8):
                continue
            fs = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and f.get("width") and f.get("height")]
            side = (lambda f: f["width"]) if orient == "portrait" else (lambda f: f["height"])
            good = sorted([f for f in fs if side(f) >= 1080], key=side) or sorted(fs, key=side, reverse=True)
            if not good:
                continue
            path = f"{WORK}/pexels/{v['id']}.mp4"
            if not os.path.exists(path):
                d = requests.get(good[0]["link"], timeout=180)
                d.raise_for_status()
                open(path, "wb").write(d.content)
            used.add(v["id"])
            return path
    return None


def tts(text, path, demo):
    if demo:
        sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", str(max(3, len(text.split()) * 0.38)), path])
        return True
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, VOICE, rate="-4%").save(path))
        return os.path.getsize(path) > 1000
    except Exception as e:
        print("TTS failed:", e)
        return False


# ---------- resolve scenes -> visuals ----------
def resolve(demo, used_titles):
    """Returns list of scene dicts with .visuals={'wide':[...], 'tall':[...]}, .audio, .D"""
    villa_urls = {} if demo else sources.discover()
    out, credits, used_clips = [], [], set()
    os.makedirs(WORK, exist_ok=True)
    for s in SCENES:
        s = dict(s)
        vis = {"wide": [], "tall": []}
        if s["kind"] == "places":
            photos = []
            for g in s["groups"]:
                got = []
                if demo:
                    for i in range(g["n"]):
                        p = f"{WORK}/demo_{s['id']}_{len(photos)+i}.jpg"
                        Image.new("RGB", (2400, 1600), (60 + 40 * len(photos) % 200, 90, 160)).save(p)
                        got.append(dict(path=p, credit="Demo", title=p))
                else:
                    for q in g["q"]:
                        if len(got) >= g["n"]:
                            break
                        try:
                            got += places.fetch(q, g["n"] - len(got), seed=SEED, width=2400, min_w=1800, exclude=used_titles | {x["title"] for x in got})
                        except Exception as e:
                            print("commons error:", q, e)
                for x in got:
                    used_titles.add(x["title"])
                    credits.append(x["credit"])
                    photos.append(("photo", x["path"], g["cap"]))
            if not photos and s.get("fb_villa") and not demo:
                st = s["fb_villa"][0]
                photos.append(("photo", sources.download(st, villa_urls[st]), s["groups"][0]["cap"]))
            for f in vis:
                vis[f] = list(photos)
        elif s["kind"] == "villa":
            ph = []
            for st, cap in s["photos"]:
                if demo:
                    p = f"{WORK}/demo_v_{st}.jpg"
                    Image.new("RGB", (1600, 1068), (150, 60 + len(ph) * 20, 90)).save(p)
                else:
                    p = sources.download(st, villa_urls.get(st) or f"{config.SITE}/{st}.jpeg")
                ph.append(("photo", p, cap))
            vis["wide"], vis["tall"] = list(ph), list(ph)
        elif s["kind"] == "clip":
            for f, orient in (("wide", "landscape"), ("tall", "portrait")):
                if demo:
                    p = f"{WORK}/demo_clip_{s['id']}_{f}.mp4"
                    w, h = (1920, 1080) if f == "wide" else (1080, 1920)
                    if not os.path.exists(p):
                        sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size={w}x{h}:rate=25", "-t", "10", "-pix_fmt", "yuv420p", p])
                else:
                    p = pexels(s["q"], orient, 10, used_clips)
                if p:
                    vis[f] = [("clip", p, s["cap"])]
        if not vis["wide"] or not vis["tall"]:
            print(f"scene {s['id']}: skipped (no visuals)")
            continue
        s["visuals"] = vis
        out.append(s)
    return out, sorted(set(credits))


# ---------- drawing ----------
def canvas(photo, W, H, out):
    S = 1.6
    cw, ch = int(W * S), int(H * S)
    im = Image.open(photo).convert("RGB")
    ar, tar = im.width / im.height, W / H
    if abs(__import__("math").log(ar / tar)) < 0.35:      # similar shape: cover
        s = max(cw / im.width, ch / im.height)
        r = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
        l, t = (r.width - cw) // 2, (r.height - ch) // 2
        r.crop((l, t, l + cw, t + ch)).save(out, quality=93)
    else:                                                   # different shape: blurred backdrop + fitted photo
        s = max(cw / im.width, ch / im.height)
        bg = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.BILINEAR)
        l, t = (bg.width - cw) // 2, (bg.height - ch) // 2
        bg = bg.crop((l, t, l + cw, t + ch)).filter(ImageFilter.GaussianBlur(60)).point(lambda v: int(v * 0.55))
        s2 = min(cw / im.width, ch / im.height)
        fg = im.resize((int(im.width * s2), int(im.height * s2)), Image.LANCZOS)
        bg.paste(fg, ((cw - fg.width) // 2, (ch - fg.height) // 2))
        bg.save(out, quality=93)


def caption_png(W, H, cap, style, out):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    k = W / 1920 if W > H else W / 1080
    big, small = int((72 if W > H else 64) * (1 if W > H else 1)), int(40 if W > H else 38)
    if style in ("title", "end"):
        for y in range(int(H * 0.55)):
            d.line([(0, H - 1 - y), (W, H - 1 - y)], fill=(0, 0, 0, int(190 * (1 - y / (H * 0.55)))))
        f1, f2 = _font(int(big * 1.25)), _font(small + 4)
        t1, t2 = cap
        y = int(H * (0.62 if W > H else 0.60))
        for ln in _wrap(d, t1, f1, int(W * 0.86)):
            w = d.textlength(ln, font=f1)
            d.text(((W - w) / 2 + 3, y + 3), ln, font=f1, fill=(0, 0, 0, 210))
            d.text(((W - w) / 2, y), ln, font=f1, fill=(255, 255, 255, 255))
            y += int(f1.size * 1.2)
        w = d.textlength(t2, font=f2)
        d.text(((W - w) / 2, y + 12), t2, font=f2, fill=(255, 215, 120, 255))
        if style == "end":
            f3 = _font(small)
            for i, t in enumerate([f"WhatsApp {config.PHONE}", config.SITE.replace("https://", "")]):
                w = d.textlength(t, font=f3)
                d.text(((W - w) / 2, y + 12 + f2.size + 30 + i * (small + 14)), t, font=f3, fill=(255, 255, 255, 255))
    elif cap and cap[0]:
        band = int(H * 0.30)
        for y in range(band):
            d.line([(0, H - 1 - y), (W, H - 1 - y)], fill=(0, 0, 0, int(185 * (1 - y / band))))
        f1, f2 = _font(big), _font(small)
        x = int(W * 0.06)
        y = H - int(H * (0.17 if W > H else 0.13))
        d.text((x + 3, y + 3), cap[0], font=f1, fill=(0, 0, 0, 210))
        d.text((x, y), cap[0], font=f1, fill=(255, 255, 255, 255))
        if cap[1]:
            d.text((x, y + int(big * 1.25)), cap[1], font=f2, fill=(255, 215, 120, 255))
    fb = _font(int(small * 0.8))
    d.text((int(W * 0.04), int(H * 0.035)), VIL, font=fb, fill=(255, 255, 255, 170))
    ov.save(out)


# ---------- rendering ----------
GRADE = "eq=contrast=1.06:saturation=1.12,vignette=angle=PI/6"
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def segment(fmt, idx, vis, style, d, out):
    W, H = FORMATS[fmt]
    kind, path, cap = vis
    capf = f"{WORK}/cap_{fmt}_{idx}.png"
    caption_png(W, H, cap, style, capf)
    if kind == "photo":
        cv = f"{WORK}/cv_{fmt}_{idx}.jpg"
        canvas(path, W, H, cv)
        n = int(d * FPS)
        m = idx % 4
        if m == 0:
            z, x, y = f"1.0+0.14*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif m == 1:
            z, x, y = f"1.14-0.14*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif m == 2:
            z, x, y = "1.12", f"(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"
        else:
            z, x, y = "1.12", f"(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"
        fc = (f"[0:v]zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},{GRADE}[bg];"
              f"[bg][1:v]overlay=0:0,format=yuv420p[v]")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", cv, "-loop", "1", "-i", capf, "-filter_complex", fc,
               "-map", "[v]", "-t", f"{d:.3f}", *ENC, out]
    else:
        fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,{GRADE}[bg];"
              f"[bg][1:v]overlay=0:0,format=yuv420p[v]")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", path, "-loop", "1", "-i", capf,
               "-filter_complex", fc, "-map", "[v]", "-t", f"{d:.3f}", *ENC, out]
    sh(cmd)


def build(fmt, scenes, plan, audio, total, out, crf, maxrate):
    W, H = FORMATS[fmt]
    segs, lens = [], []
    k = 0
    for s in scenes:
        n = len(s["visuals"][fmt])
        for i, vis in enumerate(s["visuals"][fmt]):
            vd = s["D"] / n
            f = f"{WORK}/seg_{fmt}_{k:02d}.mp4"
            segment(fmt, k, vis, s.get("style") if s.get("style") != "title" or i == 0 else None, vd + XF, f)
            segs.append(f)
            lens.append(vd + XF)
            k += 1
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for s in segs:
        cmd += ["-i", s]
    cmd += ["-i", audio]
    acc, prev, fc = lens[0], "[0:v]", []
    for i in range(1, len(segs)):
        fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={acc - XF:.3f}[v{i}]")
        prev = f"[v{i}]"
        acc += lens[i] - XF
    fc.append(f"{prev}fade=t=in:st=0:d=0.8,fade=t=out:st={total - 1.5:.2f}:d=1.5[vout]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", f"{len(segs)}:a", "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-maxrate", maxrate, "-bufsize", "12M",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    sh(cmd)
    print(f"{fmt}: {out} {os.path.getsize(out)/1e6:.1f} MB")


def make_audio(scenes, narr_files, total, out):
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for f in narr_files:
        cmd += ["-i", f]
    music = sorted(glob.glob(os.path.join(config.MUSIC_DIR, "*.mp3")))
    if music:
        cmd += ["-stream_loop", "-1", "-i", random.Random(SEED).choice(music)]
    cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    parts, labels = [], []
    for i, s in enumerate(scenes):
        ms = int((s["start"] + 0.6) * 1000)
        parts.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[n{i}]")
        labels.append(f"[n{i}]")
    base = len(narr_files)
    mixin = "".join(labels)
    if music:
        parts.append(f"[{base}:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.13[m]")
        mixin += "[m]"
        cnt = len(labels) + 1
        sil = base + 1
    else:
        cnt, sil = len(labels), base
    mixin += f"[{sil}:a]"
    parts.append(f"{mixin}amix=inputs={cnt + 1}:normalize=0:duration=longest,afade=t=out:st={total - 2:.2f}:d=2[aout]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[aout]", "-t", f"{total:.2f}", "-c:a", "aac", "-b:a", "192k", out]
    sh(cmd)


def stamp(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--only", choices=["wide", "tall"])
    ap.add_argument("--check", action="store_true", help="only test sources (Commons, Pexels, voice); no rendering")
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    os.makedirs("out", exist_ok=True)

    scenes, credits = resolve(a.demo, set())
    if a.check:
        for s in scenes:
            print(f"CHECK {s['id']}: wide={[(v[0], os.path.basename(v[1])) for v in s['visuals']['wide']]} tall={len(s['visuals']['tall'])}")
        print("CHECK missing scenes:", [x['id'] for x in SCENES if x['id'] not in [s['id'] for s in scenes]])
        print("CHECK voice:", tts("This is a test of the narration voice.", f"{WORK}/test.mp3", False))
        print("CHECK credits:", credits)
        return
    # narration + timing
    narr_files, t = [], 0.0
    for s in scenes:
        f = f"{WORK}/narr_{s['id']}.mp3"
        ok = tts(s["narr"], f, a.demo)
        if not ok:
            sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "6", f])
        narr_files.append(f)
        n = len(s["visuals"]["wide"])
        mn = MIN_PHOTO if s["visuals"]["wide"][0][0] == "photo" else 6.0
        s["D"] = max(dur(f) + 1.4, n * mn)
        s["start"] = t
        t += s["D"]
    total = t + XF
    print(f"scenes: {[s['id'] for s in scenes]}  total {total:.0f}s")
    audio = f"{WORK}/audio.m4a"
    make_audio(scenes, narr_files, total, audio)

    outs = {}
    for fmt, crf, mr in (("wide", 20, "8M"), ("tall", 23, "3500k")):
        if a.only and a.only != fmt:
            continue
        outs[fmt] = f"out/film-{fmt}.mp4"
        build(fmt, scenes, None, audio, total, outs[fmt], crf, mr)
    chapters = "\n".join(f"{stamp(s['start'])} {s['chapter']}" for s in scenes if s.get("chapter"))
    open("out/chapters.txt", "w").write(chapters + "\n")
    open("out/credits.txt", "w").write("; ".join(credits) + "\n")
    print("CHAPTERS:\n" + chapters + "\nCREDITS:", credits)

    # small widescreen preview for quick review
    if "wide" in outs:
        sh(["ffmpeg", "-y", "-loglevel", "error", "-i", outs["wide"], "-vf", "scale=854:-2", "-c:v", "libx264", "-crf", "29",
            "-preset", "veryfast", "-c:a", "aac", "-b:a", "64k", "out/film-wide-preview.mp4"])

    if a.post:
        post(outs, chapters, credits)
    else:
        import host
        if os.environ.get("GITHUB_REPOSITORY") and "tall" in outs:
            print("PREVIEW tall:", host.host_public(outs["tall"], prefix="film-", keep=1))
            print("PREVIEW wide-small:", host.host_public("out/film-wide-preview.mp4", prefix="film-", keep=2))


def post(outs, chapters, credits):
    import youtube, instagram, host
    title = "A Day in Hyderabad: Ramoji Film City, Wonderla & a Private Villa Stay | VanThara Homestay"
    cr = ("\n\nPhoto credits: " + "; ".join(credits)) if credits else ""
    desc = (f"Six friends, one weekend: a road trip through Ramoji Film City, Wonderla and the best of Hyderabad - ending at VanThara Homestay, "
            f"a private 5-bedroom villa in Turkayamjal.\n\nBook the whole villa for family stays, wedding guests, birthdays and team offsites.\n"
            f"WhatsApp {config.PHONE}\n{config.SITE}\n\n{chapters}{cr}\n\n"
            "#Hyderabad #RamojiFilmCity #Wonderla #HyderabadTourism #VillaStay #VanThara")
    res = {}
    if "wide" in outs and os.environ.get("YT_REFRESH_TOKEN"):
        res["youtube"] = youtube.upload_short(outs["wide"], title, desc,
                                              tags=["Hyderabad", "Ramoji Film City", "Wonderla", "Hyderabad tourism", "villa stay", "VanThara Homestay"])
    if "tall" in outs and os.environ.get("IG_ACCESS_TOKEN"):
        url = host.host_public(outs["tall"], prefix="film-", keep=1)
        cap = (f"Six friends. One weekend. Ramoji Film City, Wonderla, Hyderabad - and a private villa to come home to.\n\n"
               f"Book the whole villa - WhatsApp {config.PHONE}\n{config.SITE}\n📍 {config.LOCATION}{cr}\n.\n"
               "#Hyderabad #RamojiFilmCity #Wonderla #HyderabadTourism #VillaStay #WeekendGetaway #VanThara #VanTharaHomestay")
        res["instagram"] = instagram.publish_reel(url, cap[:2200])
    print("published:", res)
    sys.exit(0 if res else 1)


if __name__ == "__main__":
    main()

"""Pick next content item, render it, publish. Usage:
  python run.py --kind reel                 # render + post reel to YouTube Shorts + Instagram Reels
  python run.py --kind carousel             # Instagram photo carousel (uses website photo URLs)
  python run.py --kind reel --dry-run       # render only, post nothing
  python run.py --kind reel --dry-run --demo  # use synthetic photos (offline test)
"""
import argparse, datetime, json, os, random, sys
import content, sources, reel, places
from config import REEL_PHOTOS

STATE = "state.json"


def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


def pick(kind, state):
    done = state.get(kind, [])
    pool = [i for i in content.ITEMS if i["id"] not in done]
    if not pool:           # everything used -> start a new cycle
        state[kind] = done = []
        pool = content.ITEMS
    return pool[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["reel", "carousel"], default="reel")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--item", help="force a specific item id")
    ap.add_argument("--preview", action="store_true", help="render + host the files publicly but post nothing")
    ap.add_argument("--only", choices=["youtube", "instagram"], help="post to one platform only")
    a = ap.parse_args()

    state = load()
    item = next((i for i in content.ITEMS if i["id"] == a.item), None) if a.item else pick(a.kind, state)
    stems = item["photos"]
    print(f"[{a.kind}] item: {item['id']} - {item['title']}")

    if a.demo:
        paths = sources.demo_photos(stems)
        urls = {}
    else:
        urls = sources.discover()
        stems = [s for s in stems if s in urls] or list(urls)[:REEL_PHOTOS]
        paths = {s: sources.download(s, urls[s]) for s in stems}

    # Attraction scene: photos of the place first (credited), then the villa
    scene_photos, scene_lines, credits = [], [], []
    sc = content.SCENES.get(item["id"])
    if sc and not a.demo:
        try:
            pl = random.Random(datetime.date.today().toordinal()).choice(sc["places"])
            got = places.fetch(pl["query"], 3)
            if len(got) >= 2:
                scene_photos = [g["path"] for g in got]
                scene_lines = [pl["place"]] + sc["hooks"][: len(got) - 1]
                scene_lines += [pl["place"]] * (len(got) - len(scene_lines))
                credits = sorted({g["credit"] for g in got})
                print("scene photos:", [(g["title"], g["credit"]) for g in got])
            else:
                print("scene: not enough reusable photos found, using villa photos only")
        except Exception as e:
            print("scene fetch failed, using villa photos only:", e)
    villa_lines = [sc["near"] or "Then come home to your own villa", "Private 5BHK villa. Book the whole villa"] if sc else []

    if a.kind == "reel":
        os.makedirs("out", exist_ok=True)
        out = f"out/{item['id']}.mp4"
        if scene_photos:
            photo_list = scene_photos + [paths[s] for s in stems[:2]]
            lines = scene_lines + villa_lines
        else:
            photo_list = [paths[s] for s in stems[:REEL_PHOTOS]]
            lines = item["lines"] + [item["lines"][-1], "Book the whole villa"]
        reel.render(photo_list, lines, out)
        print("rendered", out)
        if a.preview:
            import host
            print("PREVIEW:", host.host_public(out))
            return
        if a.dry_run:
            return
        results = {}
        if os.environ.get("YT_REFRESH_TOKEN") and a.only != "instagram":
            import youtube
            try:
                results["youtube"] = youtube.upload_short(out, content.yt_title(item), content.caption(item, "youtube", credits),
                                                          tags=[t.strip("#") for t in item["tags"].split()])
            except Exception as e:
                print("YouTube failed:", e)
        if os.environ.get("IG_ACCESS_TOKEN") and a.only != "youtube":
            import instagram, host
            try:
                results["instagram"] = instagram.publish_reel(host.host_public(out), content.caption(item, "instagram"))
            except Exception as e:
                print("Instagram failed:", e)
        print("published:", results)
        ok = bool(results)
    else:
        if scene_photos:   # branded 4:5 slides: place photos, then villa
            import slides, host
            os.makedirs("out", exist_ok=True)
            photo_list = scene_photos + [paths[s] for s in stems[:3]]
            texts = scene_lines + [sc["near"] or "Then come home to your own villa", "Private 5BHK villa", "Book the whole villa"]
            texts = (texts + [""] * len(photo_list))[: len(photo_list)]
            files = [slides.render_slide(p, t, f"out/{item['id']}-{i}.jpg", last=(i == len(photo_list) - 1))
                     for i, (p, t) in enumerate(zip(photo_list, texts))]
            if a.dry_run:
                print("rendered slides:", files)
                return
            slide_urls = host.host_files(files)
            if a.preview:
                print("PREVIEW:", slide_urls)
                return
        else:
            slide_urls = [urls.get(s, s) for s in stems]
            if a.dry_run:
                print("would post carousel:", slide_urls)
                return
        import instagram
        ok = False
        try:
            r = instagram.publish_carousel(slide_urls, content.caption(item, "instagram", credits))
            print("published carousel", r)
            ok = True
        except Exception as e:
            print("Instagram failed:", e)

    if ok and not a.item:
        state.setdefault(a.kind, []).append(item["id"])
        json.dump(state, open(STATE, "w"), indent=1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

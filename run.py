"""Pick next content item, render it, publish. Usage:
  python run.py --kind reel                 # render + post reel to YouTube Shorts + Instagram Reels
  python run.py --kind carousel             # Instagram photo carousel (uses website photo URLs)
  python run.py --kind reel --dry-run       # render only, post nothing
  python run.py --kind reel --dry-run --demo  # use synthetic photos (offline test)
"""
import argparse, json, os, sys
import content, sources, reel
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

    if a.kind == "reel":
        os.makedirs("out", exist_ok=True)
        out = f"out/{item['id']}.mp4"
        lines = item["lines"] + [item["lines"][-1], "Book the whole villa"]
        reel.render([paths[s] for s in stems[:REEL_PHOTOS]], lines, out)
        print("rendered", out)
        if a.dry_run:
            return
        results = {}
        if os.environ.get("YT_REFRESH_TOKEN"):
            import youtube
            try:
                results["youtube"] = youtube.upload_short(out, content.yt_title(item), content.caption(item, "youtube"),
                                                          tags=[t.strip("#") for t in item["tags"].split()])
            except Exception as e:
                print("YouTube failed:", e)
        if os.environ.get("IG_ACCESS_TOKEN"):
            import instagram
            try:
                results["instagram"] = instagram.publish_reel(out, content.caption(item, "instagram"))
            except Exception as e:
                print("Instagram failed:", e)
        print("published:", results)
        ok = bool(results)
    else:
        if a.dry_run:
            print("would post carousel:", [urls.get(s, s) for s in stems])
            return
        import instagram
        ok = False
        try:
            r = instagram.publish_carousel([urls[s] for s in stems], content.caption(item, "instagram"))
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

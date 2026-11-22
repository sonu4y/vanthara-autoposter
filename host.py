"""Publish a rendered video to this (public) GitHub repo so Instagram can fetch it by URL.
Instagram API with Instagram Login only accepts reels via a public video_url."""
import glob, os, shutil, subprocess, time, requests

KEEP = 4  # newest files kept in media/


def _git(*a):
    subprocess.run(["git", *a], check=True)


def host_files(paths, keep_jpg=16):
    """Commit several images to media/ in one push; return their public raw URLs."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("Hosting needs GitHub Actions (GITHUB_REPOSITORY not set).")
    os.makedirs("media", exist_ok=True)
    stamp, names = int(time.time()), []
    for i, p in enumerate(paths):
        n = f"slide-{stamp}-{i}.jpg"
        shutil.copy(p, os.path.join("media", n))
        names.append(n)
    for old in sorted(glob.glob("media/*.jpg"), key=os.path.getmtime)[:-keep_jpg]:
        os.remove(old)
    _push(f"media: slides {stamp}")
    urls = [f"https://raw.githubusercontent.com/{repo}/main/media/{n}" for n in names]
    for u in urls:
        for _ in range(30):
            if requests.head(u, timeout=20).status_code == 200:
                break
            time.sleep(3)
    return urls


def _push(msg):
    _git("config", "user.name", "vanthara-bot")
    _git("config", "user.email", "bot@users.noreply.github.com")
    _git("add", "-A", "media")
    _git("commit", "-m", msg)
    try:
        _git("push", "origin", "HEAD:main")
    except subprocess.CalledProcessError:
        _git("pull", "--rebase", "origin", "main")
        _git("push", "origin", "HEAD:main")


def host_public(path, prefix=None, keep=KEEP):
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("Hosting reels needs to run inside GitHub Actions (GITHUB_REPOSITORY not set).")
    os.makedirs("media", exist_ok=True)
    name = f"{os.path.splitext(os.path.basename(path))[0]}-{int(time.time())}.mp4"
    shutil.copy(path, os.path.join("media", name))
    pat = f"media/{prefix}*.mp4" if prefix else "media/*.mp4"
    files = sorted([f for f in glob.glob(pat) if prefix or not os.path.basename(f).startswith("film-")], key=os.path.getmtime)
    for old in files[:-keep]:
        os.remove(old)
    _git("config", "user.name", "vanthara-bot")
    _git("config", "user.email", "bot@users.noreply.github.com")
    _git("add", "-A", "media")
    _git("commit", "-m", f"media: {name}")
    try:
        _git("push", "origin", "HEAD:main")
    except subprocess.CalledProcessError:
        _git("pull", "--rebase", "origin", "main")
        _git("push", "origin", "HEAD:main")
    url = f"https://raw.githubusercontent.com/{repo}/main/media/{name}"
    for _ in range(30):
        r = requests.get(url, stream=True, timeout=30)
        ok = r.status_code == 200
        r.close()
        if ok:
            return url
        time.sleep(4)
    raise RuntimeError(f"Hosted video not reachable at {url} - is the repository public?")

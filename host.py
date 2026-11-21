"""Publish a rendered video to this (public) GitHub repo so Instagram can fetch it by URL.
Instagram API with Instagram Login only accepts reels via a public video_url."""
import glob, os, shutil, subprocess, time, requests

KEEP = 4  # newest files kept in media/


def _git(*a):
    subprocess.run(["git", *a], check=True)


def host_public(path):
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("Hosting reels needs to run inside GitHub Actions (GITHUB_REPOSITORY not set).")
    os.makedirs("media", exist_ok=True)
    name = f"{os.path.splitext(os.path.basename(path))[0]}-{int(time.time())}.mp4"
    shutil.copy(path, os.path.join("media", name))
    files = sorted(glob.glob("media/*.mp4"), key=os.path.getmtime)
    for old in files[:-KEEP]:
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

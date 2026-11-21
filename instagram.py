"""Instagram Graph API publishing (Business/Creator account). Env: IG_USER_ID, IG_ACCESS_TOKEN."""
import os, time, requests

V = "v21.0"
# Token from "API setup with Instagram login" -> graph.instagram.com (default).
# If you use a Facebook-login token instead, set IG_GRAPH_HOST=https://graph.facebook.com
G = f"{os.environ.get('IG_GRAPH_HOST', 'https://graph.instagram.com')}/{V}"


def _tok():
    return os.environ["IG_ACCESS_TOKEN"]


def _uid():
    return os.environ["IG_USER_ID"]


def _check(r):
    if not r.ok:
        raise RuntimeError(f"Instagram API error {r.status_code}: {r.text}")
    return r.json()


def _wait(container_id, tries=40):
    for _ in range(tries):
        s = _check(requests.get(f"{G}/{container_id}", params={"fields": "status_code,status", "access_token": _tok()}, timeout=30))
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Container failed: {s}")
        time.sleep(6)
    raise RuntimeError("Timed out waiting for Instagram to process media")


def _publish(container_id):
    return _check(requests.post(f"{G}/{_uid()}/media_publish", data={"creation_id": container_id, "access_token": _tok()}, timeout=60))["id"]


def publish_reel(video_path, caption):
    c = _check(requests.post(f"{G}/{_uid()}/media", data={
        "media_type": "REELS", "upload_type": "resumable", "caption": caption, "share_to_feed": "true", "access_token": _tok()}, timeout=60))
    data = open(video_path, "rb").read()
    up = requests.post(c["uri"], headers={"Authorization": f"OAuth {_tok()}", "offset": "0", "file_size": str(len(data))}, data=data, timeout=600)
    _check(up)
    _wait(c["id"])
    return _publish(c["id"])


def publish_carousel(image_urls, caption):
    """image_urls must be public JPEG URLs (your website photos are)."""
    kids = []
    for u in image_urls[:10]:
        kids.append(_check(requests.post(f"{G}/{_uid()}/media", data={"image_url": u, "is_carousel_item": "true", "access_token": _tok()}, timeout=60))["id"])
    for k in kids:
        _wait(k)
    c = _check(requests.post(f"{G}/{_uid()}/media", data={"media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption, "access_token": _tok()}, timeout=60))
    _wait(c["id"])
    return _publish(c["id"])

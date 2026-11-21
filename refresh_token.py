"""Renew the Instagram long-lived token (valid 60 days) and store it back as the
IG_ACCESS_TOKEN GitHub secret. Runs from .github/workflows/refresh-token.yml.
Needs env: IG_ACCESS_TOKEN, GH_PAT (fine-grained token, 'Secrets: read/write' on this repo),
GITHUB_REPOSITORY."""
import base64, os, sys
import requests
from nacl import encoding, public

HOST = os.environ.get("IG_GRAPH_HOST", "https://graph.instagram.com")


def refresh(token):
    r = requests.get(f"{HOST}/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=60)
    if r.status_code != 200:
        sys.exit(f"Instagram refresh failed {r.status_code}: {r.text[:300]}")
    j = r.json()
    print("refreshed; expires_in days:", round(j.get("expires_in", 0) / 86400))
    return j["access_token"]


def store(secret_value):
    repo, pat = os.environ["GITHUB_REPOSITORY"], os.environ["GH_PAT"]
    h = {"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github+json"}
    k = requests.get(f"https://api.github.com/repos/{repo}/actions/secrets/public-key", headers=h, timeout=60)
    k.raise_for_status(); k = k.json()
    box = public.SealedBox(public.PublicKey(k["key"].encode(), encoding.Base64Encoder()))
    enc = base64.b64encode(box.encrypt(secret_value.encode())).decode()
    r = requests.put(f"https://api.github.com/repos/{repo}/actions/secrets/IG_ACCESS_TOKEN",
                     headers=h, json={"encrypted_value": enc, "key_id": k["key_id"]}, timeout=60)
    r.raise_for_status()
    print("IG_ACCESS_TOKEN secret updated")


if __name__ == "__main__":
    store(refresh(os.environ["IG_ACCESS_TOKEN"]))

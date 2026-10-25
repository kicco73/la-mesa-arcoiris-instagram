#!/usr/bin/env python3
"""Pubblica su Instagram il prossimo post approvato di data/posts.json.

Instagram API con Instagram Login (graph.instagram.com).
Variabili d'ambiente:
  IG_ACCESS_TOKEN  token dell'account (secret del repository)
  RAW_BASE         URL pubblico della cartella del repo, es.
                   https://raw.githubusercontent.com/<owner>/<repo>/<sha>
  MAX_PER_RUN      post da pubblicare per esecuzione (default 1)
  DRY_RUN          "1" = controlla tutto ma non pubblica
"""
import datetime as dt
import json
import os
import pathlib
import sys
import time
from zoneinfo import ZoneInfo

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://graph.instagram.com/v23.0"


class ApiError(RuntimeError):
    pass


def call(method: str, path: str, token: str, **params) -> dict:
    r = requests.request(method, f"{API}/{path}", params={**params, "access_token": token}, timeout=60)
    body = r.json()
    if r.status_code >= 400 or "error" in body:
        raise ApiError(f"{method} {path}: {body.get('error', body)}")
    return body


def wait_ready(container: str, token: str) -> None:
    for _ in range(30):
        status = call("GET", container, token, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise ApiError(f"container {container}: {status}")
        time.sleep(4)
    raise ApiError(f"container {container}: timeout")


def image_urls(post: dict, raw_base: str) -> list[str]:
    folder = ROOT / "images" / post["id"]
    files = sorted(folder.glob("*.jpg"), key=lambda p: int(p.stem))
    if not files:
        raise ApiError(f"post {post['id']}: nessuna immagine generata")
    return [f"{raw_base}/images/{post['id']}/{f.name}" for f in files][:20]


def publish(post: dict, token: str, ig_user: str, raw_base: str, dry: bool) -> str | None:
    urls = image_urls(post, raw_base)
    for u in urls:  # Instagram deve poter scaricare ogni immagine
        h = requests.head(u, timeout=30)
        if h.status_code != 200:
            raise ApiError(f"immagine non raggiungibile ({h.status_code}): {u}")
    if dry:
        print(f"[dry-run] {post['order']:>2} {post['id']}: {len(urls)} immagini, didascalia {len(post['caption'])} caratteri")
        return None
    if len(urls) == 1:
        creation = call("POST", f"{ig_user}/media", token, image_url=urls[0], caption=post["caption"])["id"]
    else:
        children = []
        for u in urls:
            cid = call("POST", f"{ig_user}/media", token, image_url=u, is_carousel_item="true")["id"]
            wait_ready(cid, token)
            children.append(cid)
        creation = call("POST", f"{ig_user}/media", token, media_type="CAROUSEL",
                        children=",".join(children), caption=post["caption"])["id"]
    wait_ready(creation, token)
    return call("POST", f"{ig_user}/media_publish", token, creation_id=creation)["id"]


def main() -> int:
    token = os.environ["IG_ACCESS_TOKEN"]
    raw_base = os.environ["RAW_BASE"].rstrip("/")
    max_per_run = int(os.environ.get("MAX_PER_RUN", "1"))
    dry = os.environ.get("DRY_RUN") == "1"

    path = ROOT / "data/posts.json"
    posts = json.loads(path.read_text())

    if os.environ.get("SCHEDULED") == "1":
        madrid = ZoneInfo("Europe/Madrid")
        now = dt.datetime.now(madrid)
        if not (dt.time(19, 30) <= now.time() < dt.time(21, 0)):
            print(f"Fuori orario ({now:%H:%M} a Madrid), salto.")
            return 0
        today = [p for p in posts if p.get("published_at")
                 and dt.datetime.fromisoformat(p["published_at"]).astimezone(madrid).date() == now.date()]
        if today:
            print("Oggi è già stato pubblicato un post, salto.")
            return 0

    queue = sorted((p for p in posts if p["approved"] and p["status"] == "pending"), key=lambda p: p["order"])
    if not queue:
        print("Nessun post approvato in attesa.")
        return 0

    me = call("GET", "me", token, fields="user_id,username")
    ig_user = me["user_id"]
    print(f"Account: @{me.get('username')}")
    limit = call("GET", f"{ig_user}/content_publishing_limit", token).get("data", [{}])[0]
    print(f"Limite pubblicazioni: {limit}")

    for post in queue[:max_per_run]:
        try:
            media_id = publish(post, token, ig_user, raw_base, dry)
        except ApiError as exc:
            print(f"ERRORE post {post['id']}: {exc}", file=sys.stderr)
            return 1
        if media_id:
            post.update(status="published", ig_media_id=media_id,
                        published_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
            path.write_text(json.dumps(posts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(f"Pubblicato {post['order']} {post['id']} -> {media_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Pubblica come storie le foto dell'evento del post uscito oggi (data/highlights.json).

Ogni locale ha un highlight. Quando esce il post di un evento, escono anche le sue storie:
prima la storia di apertura del locale (solo la prima volta), poi le foto dell'evento.
Gli highlight li crea e aggiorna l'attività serale dal browser (l'API non può farlo),
usando le storie già entrate nell'archivio.

Variabili: IG_ACCESS_TOKEN, RAW_BASE, DRY_RUN, EVENT_IDS (opzionale, id separati da virgola:
se assente usa i post pubblicati oggi a Madrid).
"""
import datetime as dt
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

import requests

from publish import ROOT, ApiError, call, wait_ready

MADRID = ZoneInfo("Europe/Madrid")


def publish_story(url: str, token: str, ig_user: str) -> str:
    for attempt in range(1, 4):
        try:
            cid = call("POST", f"{ig_user}/media", token, image_url=url, media_type="STORIES")["id"]
            wait_ready(cid, token)
            time.sleep(3)  # pubblicare subito dopo FINISHED a volte dà "Media not found"
            return call("POST", f"{ig_user}/media_publish", token, creation_id=cid)["id"]
        except ApiError as exc:
            if "2207006" not in str(exc) or attempt == 3:  # 2207006 "Media not found" è temporaneo
                raise
            print(f"tentativo {attempt} fallito (media not found), riprovo")
            time.sleep(10 * attempt)
    raise AssertionError


def todays_event_ids() -> list[str]:
    today = dt.datetime.now(MADRID).date()
    posts = json.loads((ROOT / "data/posts.json").read_text())
    return [p["id"] for p in posts if p.get("published_at")
            and dt.datetime.fromisoformat(p["published_at"]).astimezone(MADRID).date() == today]


def main() -> int:
    token = os.environ["IG_ACCESS_TOKEN"]
    raw_base = os.environ["RAW_BASE"].rstrip("/")
    dry = os.environ.get("DRY_RUN") == "1"
    wanted = [x for x in os.environ.get("EVENT_IDS", "").split(",") if x] or todays_event_ids()

    path = ROOT / "data/highlights.json"
    highlights = json.loads(path.read_text())
    work = [(h, ev) for h in highlights if h["approved"] for ev in h["events"]
            if ev["id"] in wanted and ev["status"] == "pending"]
    if not work:
        print("Nessuna storia da pubblicare per gli eventi di oggi.")
        return 0

    def save() -> None:
        if not dry:
            path.write_text(json.dumps(highlights, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    ig_user = None if dry else call("GET", "me", token, fields="user_id")["user_id"]
    now = lambda: dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")  # noqa: E731
    for h, ev in work:
        files = [] if h["opening_published"] else ["0.jpg"]
        files += [f"{ev['id']}-{n}.jpg" for n in range(1, len(ev["photos"]) + 1)]
        for name in files:
            url = f"{raw_base}/stories/{h['venue']}/{name}"
            if requests.head(url, timeout=30).status_code != 200:
                print(f"::error::ERRORE immagine non raggiungibile: {url}")
                return 1
            if dry:
                print(f"[dry-run] {h['title']} {name}")
                continue
            try:
                sid = publish_story(url, token, ig_user)
            except ApiError as exc:
                print(f"::error::ERRORE {h['title']} {name}: {exc}")
                save()
                return 1
            if name == "0.jpg":
                h["opening_published"] = True
                h["opening_story_id"] = sid
                h["opening_published_at"] = now()
            else:
                ev["ig_story_ids"].append(sid)
            save()
        if not dry:
            ev["status"] = "published"
            ev["published_at"] = now()
            save()
        print(f"{h['title']}: storie dell'evento {ev['id']} pubblicate ({len(files)})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # errore visibile come annotazione del workflow
        print(f"::error::{type(exc).__name__}: {exc}")
        raise

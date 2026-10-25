#!/usr/bin/env python3
"""Archivia nel repository tutte le foto originali del gruppo Meetup.

Fonti: copertine e album di ogni evento (data/events.json) e l'album del gruppo
(data/group_album.json). Salva archive/photos/<id>.jpeg e archive/photos/index.json.
Scarica solo le foto mancanti, quindi si può rieseguire senza costi.
"""
import json
import pathlib
import re
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://secure.meetupstatic.com/photos/event/"
OUT = ROOT / "archive" / "photos"


def photo_id(url: str) -> str:
    return re.search(r"(\d+)\.jpe?g$", url).group(1)


def collect() -> dict[str, dict]:
    photos: dict[str, dict] = {}

    def add(url: str, origin: str) -> None:
        entry = photos.setdefault(photo_id(url), {"url": url, "origins": []})
        if origin not in entry["origins"]:
            entry["origins"].append(origin)

    for e in json.loads((ROOT / "data/events.json").read_text()):
        if e.get("featuredEventPhoto"):
            add(e["featuredEventPhoto"]["highResUrl"], f"evento {e['id']} copertina")
        for p in (e.get("photoAlbum") or {}).get("photoSample") or []:
            add(p["highResUrl"], f"evento {e['id']} album {e['photoAlbum']['id']}")
    group = json.loads((ROOT / "data/group_album.json").read_text())
    for path in group["photos"]:
        add(BASE + path, f"album gruppo {group['album_id']}")
    return photos


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    photos = collect()
    errors = 0
    for pid, entry in sorted(photos.items()):
        target = OUT / f"{pid}.jpeg"
        entry["file"] = target.name
        if target.exists() and target.stat().st_size > 0:
            continue
        try:
            r = requests.get(entry["url"], headers={"user-agent": "Mozilla/5.0"}, timeout=60)
            r.raise_for_status()
            target.write_bytes(r.content)
            print(f"ok   {pid}")
        except Exception as exc:
            errors += 1
            entry.pop("file")
            print(f"ERR  {pid}: {exc}", file=sys.stderr)
    (OUT / "index.json").write_text(json.dumps(photos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(photos)} foto nell'archivio, errori: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Pubblica come storie le immagini degli highlight approvati (data/highlights.json).

Le storie restano nell'archivio di Instagram: da lì si raggruppano in highlight dall'app
(l'API non permette di creare highlight). Pubblica gli highlight in ordine, tutte le storie
di un highlight di fila, fino a MAX_STORIES per esecuzione (il limite Instagram è ~100 in 24 ore).
Variabili: IG_ACCESS_TOKEN, RAW_BASE, MAX_STORIES (default 40), DRY_RUN.
"""
import json
import os
import sys
import time

import requests

from publish import ROOT, ApiError, call, wait_ready


def main() -> int:
    token = os.environ["IG_ACCESS_TOKEN"]
    raw_base = os.environ["RAW_BASE"].rstrip("/")
    budget = int(os.environ.get("MAX_STORIES", "40"))
    dry = os.environ.get("DRY_RUN") == "1"

    path = ROOT / "data/highlights.json"
    highlights = json.loads(path.read_text())
    queue = [h for h in highlights if h["approved"] and h["status"] != "published"]
    if not queue:
        print("Nessun highlight approvato da pubblicare.")
        return 0
    ig_user = call("GET", "me", token, fields="user_id")["user_id"]

    for h in queue:
        files = ["0.jpg"] + [f"{n}.jpg" for n in range(1, len(h["photos"]) + 1)]
        todo = files[len(h["ig_story_ids"]):]          # riprende da dove si era fermato
        if len(todo) > budget:
            print(f"{h['title']}: rimandato al prossimo giro ({len(todo)} storie, budget {budget})")
            break
        for name in todo:
            url = f"{raw_base}/stories/{h['venue']}/{name}"
            if requests.head(url, timeout=30).status_code != 200:
                print(f"::error::ERRORE immagine non raggiungibile: {url}", file=sys.stderr)
                return 1
            if dry:
                print(f"[dry-run] {h['title']} {name}")
                continue
            sid = None
            for attempt in range(1, 4):
                try:
                    cid = call("POST", f"{ig_user}/media", token, image_url=url, media_type="STORIES")["id"]
                    wait_ready(cid, token)
                    time.sleep(3)  # pubblicare subito dopo FINISHED a volte dà "Media not found"
                    sid = call("POST", f"{ig_user}/media_publish", token, creation_id=cid)["id"]
                    break
                except ApiError as exc:
                    # 2207006 "Media not found" è temporaneo: nuovo container e nuovo tentativo
                    if "2207006" not in str(exc) or attempt == 3:
                        print(f"::error::ERRORE {h['title']} {name}: {exc}", file=sys.stderr)
                        return 1
                    print(f"{h['title']} {name}: tentativo {attempt} fallito (media not found), riprovo")
                    time.sleep(10 * attempt)
            h["ig_story_ids"].append(sid)
            path.write_text(json.dumps(highlights, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            budget -= 1
        if not dry:
            h["status"] = "published"
            path.write_text(json.dumps(highlights, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(f"Pubblicato highlight {h['title']}: {len(files)} storie")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # errore visibile come annotazione del workflow
        print(f"::error::{type(exc).__name__}: {exc}")
        raise

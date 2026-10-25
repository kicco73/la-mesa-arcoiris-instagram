#!/usr/bin/env python3
"""Genera data/highlights.json: un highlight per locale con le foto di tutti gli eventi lì.

Ogni highlight = una storia di copertina con nome del locale + fino a 8 storie foto
(prima le foto degli album, poi le copertine degli eventi). Da eseguire una volta,
poi highlights.json si modifica direttamente.
"""
import datetime as dt
import json
import pathlib

from make_posts import DATE_FIX, EXCLUDED, MESES, PHOTO_BASE, ROOT, category

MAX_PHOTOS = 8

# categoria dei post -> locale dell'highlight
VENUE_OF = {"piazzetta_gv": "piazzetta", "navidad": "foz"}

# locale -> (titolo highlight, max 15 caratteri; sottotitolo)
VENUES = {
    "piazzetta": ("Piazzetta", "Pizza napoletana · Eixample"),
    "romana": ("Le Romane", "Pizza romana · Eixample"),
    "lapala": ("La Pala", "Pizza romana · Paral·lel"),
    "bloc34": ("Bloc 34", "Bar · Gràcia"),
    "aperegina": ("Ape Regina", "Cocina italiana"),
    "abasto": ("El Abasto", "Cocina argentina · Poblenou"),
    "fiorito": ("El Fiorito", "Cocina argentina · Sant Antoni"),
    "federica": ("La Federica", "Bar · Poble-sec"),
    "delias": ("D'Elias", "Cocina griega · Poble-sec"),
    "tootsie": ("Tootsie", "Musical · Teatro Apolo"),
    "maroazul": ("Maro Azul", "Cocina mexicana · Eixample"),
    "pummarola": ("AperiPizza", "Pizza y spritz · Sant Antoni"),
    "lodecarmen": ("Lo de Carmen", "Bar · Paral·lel"),
    "boxer": ("Boxer", "Bar · Eixample"),
    "foz": ("Foz", "Cocina fusión · Eixample"),
    "bardaixa": ("Bardaixa", "Bar · Sant Antoni"),
    "mangarosa": ("Manga Rosa", "Cocina brasileña · Sant Antoni"),
    "lacarra": ("La Carrà", "Bar · Eixample"),
    "outofchina": ("Out of China", "Cocina china · Eixample"),
    "elephanta": ("Elephanta", "Cócteles · Gràcia"),
    "leggenda": ("Leggenda", "Pizza con Gay Meeting Point"),
    "phohanoi": ("Pho Ha Noi", "Cocina vietnamita · Eixample"),
    "bocachancla": ("Bocachancla", "Tapas · Eixample"),
    "rioja": ("Rioja Pasión", "Viaje a Logroño"),
}


def period(dates: list[dt.date]) -> str:
    a, b = min(dates), max(dates)
    if (a.year, a.month) == (b.year, b.month):
        return f"{MESES[a.month - 1]} {a.year}"
    if a.year == b.year:
        return f"{MESES[a.month - 1]} – {MESES[b.month - 1]} {a.year}"
    return f"{MESES[a.month - 1]} {a.year} – {MESES[b.month - 1]} {b.year}"


def main() -> None:
    events = [e for e in json.loads((ROOT / "data/events_min.json").read_text()) if e[0] not in EXCLUDED]
    events.sort(key=lambda e: e[2])
    groups: dict[str, dict] = {}
    for e in events:
        venue = VENUE_OF.get(category(e), category(e))
        g = groups.setdefault(venue, {"events": [], "album": [], "covers": []})
        g["events"].append(dt.datetime.fromisoformat(DATE_FIX.get(e[0], e[2])).date())
        for p in e[8]:
            if p not in g["album"]:
                g["album"].append(p)
        if e[6] and e[6] not in g["covers"]:
            g["covers"].append(e[6])

    highlights = []
    for venue, g in sorted(groups.items(), key=lambda kv: -len(kv[1]["events"])):
        title, subtitle = VENUES[venue]
        photos = g["album"] + [c for c in g["covers"] if c not in g["album"]]
        n = len(g["events"])
        highlights.append({
            "venue": venue,
            "title": title,
            "subtitle": subtitle,
            "line": f"{n} {'encuentro' if n == 1 else 'encuentros'} · {period(g['events'])}",
            "photos": [PHOTO_BASE + p for p in photos[:MAX_PHOTOS]],
            "approved": False,
            "status": "pending",
            "ig_story_ids": [],
        })
    (ROOT / "data/highlights.json").write_text(json.dumps(highlights, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(highlights)} highlight, {sum(len(h['photos']) + 1 for h in highlights)} storie")


if __name__ == "__main__":
    main()

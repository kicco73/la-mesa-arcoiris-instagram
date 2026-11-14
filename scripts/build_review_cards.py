#!/usr/bin/env python3
"""Genera le card (1080x1350) dei post review in review_cards/<id>/<n>.png.

I post review sono le voci di data/posts.json con "kind": "review"; il campo "review" dice cosa mostrare:
  {"type": "summary"}                  valutazione media e distribuzione delle stelle
  {"type": "attributes"}               cosa è piaciuto di più (attributi con conteggio)
  {"type": "quote", "index": n}        la review n di data/reviews.json, con il suo testo
  {"type": "event", "event_id": id}    copertina dell'evento + le sue review (quante ne entrano per card)
Dei recensori compare solo il nome ("name" in data/reviews.json), mai cognome o foto.

Le card vanno committate: build_images.py le legge da "photos" come qualsiasi altra foto
(fit "contain", "enhance": false per non alterarne i colori) e aggiunge il logo in basso a destra,
per questo quell'angolo resta libero.
Da rieseguire a mano quando cambiano i post review o data/reviews.json.
"""
import datetime as dt
import json
import math
import pathlib
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_stories import INK, ORANGE, WHITE, fit, font  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "review_cards"
W, H = 1080, 1350
M = 70  # margine laterale
STAR = (214, 59, 99)
STAR_OFF = (236, 222, 205)
SOFT = (150, 96, 50)
CHIP = (255, 240, 220)
GAP = 46  # spazio tra due review
ROOM = 860  # altezza utile del pannello per le review
MESES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()


def star(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, fill) -> None:
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def stars(d: ImageDraw.ImageDraw, x: float, cy: float, n: float, r: float, gap: float = 0.5) -> float:
    """Disegna 5 stelle da x (bordo sinistro); n può avere la mezza stella. Ritorna la larghezza."""
    step = 2 * r + gap * r
    for i in range(5):
        cx = x + r + i * step
        star(d, cx, cy, r, STAR if n >= i + 0.75 else STAR_OFF)
        if i + 0.25 <= n < i + 0.75:  # mezza stella: metà sinistra piena
            half = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            star(ImageDraw.Draw(half), cx, cy, r, STAR)
            box = (int(cx - r), int(cy - r), int(cx), int(cy + r) + 1)
            d._image.paste(half.crop(box), box[:2], half.crop(box))
    return 5 * 2 * r + 4 * gap * r


def wrap(d: ImageDraw.ImageDraw, text: str, f, max_w: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        t = f"{cur} {word}".strip()
        if d.textlength(t, font=f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    return lines + [cur] if cur else lines


def base(kicker: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), ORANGE)
    d = ImageDraw.Draw(img)
    d.text((M, 110), kicker.upper(), font=font(34, "Bold"), fill=WHITE, anchor="lm")
    return img, d


def footer(d: ImageDraw.ImageDraw, text: str = "Reseñas de nuestro grupo en Meetup") -> None:
    d.text((M, H - 95), text, font=font(32, "SemiBold"), fill=INK, anchor="lm")


def panel(d: ImageDraw.ImageDraw, top: int, bottom: int) -> None:
    d.rounded_rectangle((M - 20, top, W - M + 20, bottom), radius=44, fill=WHITE)


def event_label(ev: dict) -> tuple[str, str]:
    title = ev["title"].split(" - ")[0].strip()
    when = dt.datetime.fromisoformat(ev["dateTime"])
    return title, f"{when.day} de {MESES[when.month - 1]} de {when.year}"


def summary(data: dict) -> list[Image.Image]:
    img, d = base("Lo que opináis")
    panel(d, 190, 1130)
    d.text((W // 2, 370), f"{data['rating']:.1f}".replace(".", ","), font=font(250), fill=INK, anchor="mm")
    r = 38
    width = 5 * 2 * r + 4 * 0.5 * r
    stars(d, (W - width) / 2, 540, data["rating"], r)
    d.text((W // 2, 640), f"{data['total']} valoraciones", font=font(50, "SemiBold"), fill=SOFT, anchor="mm")
    y, x0, x1 = 760, M + 110, W - M - 130
    for n in (5, 4, 3, 2, 1):
        c = data["distribution"][str(n)]
        d.text((M + 40, y), str(n), font=font(40, "Bold"), fill=INK, anchor="mm")
        star(d, M + 80, y - 2, 16, STAR)
        d.rounded_rectangle((x0, y - 9, x1, y + 9), radius=9, fill=STAR_OFF)
        if c:
            d.rounded_rectangle((x0, y - 9, x0 + max(18, (x1 - x0) * c / data["total"]), y + 9), radius=9, fill=STAR)
        d.text((W - M - 40, y), str(c), font=font(40, "Bold"), fill=INK, anchor="mm")
        y += 68
    footer(d)
    return [img]


def attributes(data: dict) -> list[Image.Image]:
    img, d = base("Lo que más os gustó")
    panel(d, 190, 1130)
    top = data["attributes"][0]["count"]
    y = 265
    for a in data["attributes"]:
        d.text((M + 30, y), a["label"], font=font(42, "Bold"), fill=INK, anchor="lm")
        d.text((W - M - 30, y), str(a["count"]), font=font(42, "ExtraBold"), fill=STAR, anchor="rm")
        x0, x1 = M + 30, W - M - 30
        d.rounded_rectangle((x0, y + 34, x1, y + 46), radius=6, fill=STAR_OFF)
        d.rounded_rectangle((x0, y + 34, x0 + (x1 - x0) * a["count"] / top, y + 46), radius=6, fill=STAR)
        y += 95
    footer(d, f"{data['total']} valoraciones en Meetup")
    return [img]


def quote(data: dict, events: dict, index: int) -> list[Image.Image]:
    rv = data["reviews"][index]
    title, when = event_label(events[rv["event_id"]])
    img, d = base("Reseña")
    panel(d, 190, 1130)
    d.text((M + 30, 330), "“", font=font(260), fill=STAR, anchor="ls")
    size = 64
    while True:
        f = font(size, "SemiBold")
        lines = wrap(d, rv["text"], f, W - 2 * M - 60)
        if len(lines) * size * 1.25 <= 520 or size <= 40:
            break
        size -= 4
    y = 400
    for line in lines:
        d.text((M + 30, y), line, font=f, fill=INK, anchor="lm")
        y += size * 1.25
    stars(d, M + 30, 950, rv["stars"], 26)
    d.text((M + 30, 1025), rv["name"], font=font(54), fill=INK, anchor="lm")
    d.text((M + 30, 1085), f"{title} · {when}", font=fit(d, f"{title} · {when}", W - 2 * M - 60, 34, "Medium"),
           fill=SOFT, anchor="lm")
    footer(d)
    return [img]


def chips(d: ImageDraw.ImageDraw, labels: list[str], x0: int, y: int, max_x: int) -> int:
    """Etichette degli attributi su più righe; ritorna la y sotto l'ultima riga."""
    f, x, h = font(27, "SemiBold"), x0, 46
    for label in labels:
        w = d.textlength(label, font=f) + 36
        if x + w > max_x and x > x0:
            x, y = x0, y + h + 10
        d.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=CHIP)
        d.text((x + 18, y + h / 2), label, font=f, fill=INK, anchor="lm")
        x += w + 12
    return y + h if labels else y


def event(data: dict, events: dict, event_id: str) -> list[Image.Image]:
    ev = events[event_id]
    title, when = event_label(ev)
    revs = [r for r in data["reviews"] if r["event_id"] == event_id]
    avg = sum(r["stars"] for r in revs) / len(revs)
    img, d = base("Reseñas del encuentro")
    panel(d, 190, 1130)
    d.text((W // 2, 330), title, font=fit(d, title, W - 2 * M - 60, 84), fill=INK, anchor="mm")
    venue = (ev.get("venue") or {}).get("name", "")
    sub = f"{venue.title() if venue.isupper() else venue} · {when}" if venue else when
    d.text((W // 2, 420), sub, font=fit(d, sub, W - 2 * M - 60, 38, "Medium"), fill=SOFT, anchor="mm")
    d.text((W // 2, 650), f"{avg:.1f}".replace(".", ","), font=font(230), fill=INK, anchor="mm")
    r = 36
    width = 5 * 2 * r + 4 * 0.5 * r
    stars(d, (W - width) / 2, 820, avg, r)
    d.text((W // 2, 930), f"{len(revs)} valoraciones", font=font(48, "SemiBold"), fill=SOFT, anchor="mm")
    d.text((W // 2, 1040), "Desliza para leerlas", font=font(36, "Bold"), fill=STAR, anchor="mm")
    footer(d)
    cards = [img]

    def block(d: ImageDraw.ImageDraw, rv: dict, y: float) -> float:
        """Disegna una review da y e ritorna la y sotto il blocco."""
        d.text((M + 30, y + 30), rv["name"], font=font(50), fill=INK, anchor="lm")
        stars(d, W - M - 30 - (5 * 44 + 4 * 11), y + 28, rv["stars"], 22)
        y += 76
        if rv.get("text"):
            f = font(32, "Medium")
            for line in wrap(d, f"“{rv['text']}”", f, W - 2 * M - 60):
                d.text((M + 30, y + 16), line, font=f, fill=INK, anchor="lm")
                y += 42
            y += 12
        return chips(d, rv["attributes"], M + 30, y, W - M - 30)

    # quante review entrano in una card: si misura disegnando su un'immagine di prova
    scratch = ImageDraw.Draw(Image.new("RGB", (W, H)))
    heights = [block(scratch, rv, 0) for rv in revs]
    groups, cur, used = [], [], 0.0
    for rv, h in zip(revs, heights):
        if cur and used + GAP + h > ROOM:
            groups.append((cur, used))
            cur, used = [], 0.0
        used += (GAP if cur else 0) + h
        cur.append(rv)
    groups.append((cur, used))
    for group, used in groups:
        img, d = base(title)
        panel(d, 190, 1130)
        y = 190 + (940 - used) / 2  # blocco centrato nel pannello
        for rv in group:
            y = block(d, rv, y) + GAP
        footer(d)
        cards.append(img)
    return cards


def render(spec: dict, data: dict, events: dict) -> list[Image.Image]:
    kind = spec["type"]
    if kind == "summary":
        return summary(data)
    if kind == "attributes":
        return attributes(data)
    if kind == "quote":
        return quote(data, events, spec["index"])
    if kind == "event":
        return event(data, events, spec["event_id"])
    raise SystemExit(f"tipo di post review sconosciuto: {kind}")


def main() -> int:
    data = json.loads((ROOT / "data/reviews.json").read_text())
    events = {e["id"]: e for e in json.loads((ROOT / "data/events.json").read_text())}
    posts = [p for p in json.loads((ROOT / "data/posts.json").read_text()) if p.get("kind") == "review"]
    errors = 0
    for post in posts:
        cards = render(post["review"], data, events)
        folder = OUT / post["id"]
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.png"):
            old.unlink()
        names = []
        for n, card in enumerate(cards, start=1):
            card.save(folder / f"{n}.png", optimize=True)
            names.append(f"review_cards/{post['id']}/{n}.png")
        if [p["src"] for p in post["photos"]] != names:
            errors += 1
            print(f"ERR  {post['id']}: \"photos\" in posts.json deve elencare {names}", file=sys.stderr)
        else:
            print(f"ok   {post['id']}: {len(cards)} card")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

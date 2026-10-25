#!/usr/bin/env python3
"""Scarica le foto di ogni post e le converte in JPEG 1080x1350 (4:5) in images/<id>/<n>.jpg.

- fit "cover":   foto reali verticali, ritaglio a riempire (centrato un po' in alto, dove stanno i volti);
                 le foto orizzontali o quadrate vengono trattate come "contain"
- fit "contain": immagini evento (spesso grafiche con testo), intere su sfondo sfocato

Rigenera solo le immagini la cui sorgente è cambiata (images/<id>/sources.json).
"""
import io
import json
import pathlib
import re
import sys

import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1080, 1350


ARCHIVE = ROOT / "archive" / "photos"


def load(src: str) -> Image.Image:
    # le foto Meetup si leggono dall'archivio del repository: l'account Meetup verrà chiuso
    m = re.search(r"meetupstatic\.com/.*?(\d+)\.jpe?g$", src)
    if m and (ARCHIVE / f"{m.group(1)}.jpeg").exists():
        src = str(ARCHIVE / f"{m.group(1)}.jpeg")
    if src.startswith("http"):
        r = requests.get(src, headers={"user-agent": "Mozilla/5.0"}, timeout=60)
        r.raise_for_status()
        data = io.BytesIO(r.content)
    else:
        data = open(src, "rb")
    img = Image.open(data)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


def cover(img: Image.Image, y_bias: float = 0.4) -> Image.Image:
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x = (img.width - W) // 2
    y = round((img.height - H) * y_bias)
    return img.crop((x, y, x + W, y + H))


def contain(img: Image.Image) -> Image.Image:
    bg = cover(img, 0.5).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.75)
    scale = min(W / img.width, H / img.height)
    fg = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg


def main() -> int:
    posts = json.loads((ROOT / "data/posts.json").read_text())
    errors = 0
    for post in posts:
        folder = ROOT / "images" / post["id"]
        folder.mkdir(parents=True, exist_ok=True)
        manifest_path = folder / "sources.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        wanted = {}
        for n, photo in enumerate(post["photos"], start=1):
            name = f"{n}.jpg"
            key = f'{photo["src"]}|{photo["fit"]}|v2'
            wanted[name] = key
            if manifest.get(name) == key and (folder / name).exists():
                continue
            try:
                img = load(photo["src"])
                # una foto orizzontale ritagliata a 4:5 perde le persone ai lati: la teniamo intera
                use_cover = photo["fit"] == "cover" and img.width / img.height < 0.95
                out = cover(img) if use_cover else contain(img)
                out.save(folder / name, "JPEG", quality=90, optimize=True, progressive=False)
                print(f"ok   {post['id']}/{name}")
            except Exception as exc:  # una foto rotta non deve bloccare le altre
                errors += 1
                wanted.pop(name)
                print(f"ERR  {post['id']}/{name}: {exc}", file=sys.stderr)
        for stale in folder.glob("*.jpg"):
            if stale.name not in wanted:
                stale.unlink()
        manifest_path.write_text(json.dumps(wanted, indent=1) + "\n")
    print(f"fatto, errori: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

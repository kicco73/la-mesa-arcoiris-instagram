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


def enhance(img: Image.Image) -> Image.Image:
    """Correzione leggera: contrasto automatico, un po' di colore e nitidezza."""
    img = ImageOps.autocontrast(img, cutoff=(0.5, 0.5), preserve_tone=True)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.04)
    return img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=60, threshold=3))


_LOGO = None


def add_logo(img: Image.Image) -> Image.Image:
    """Logo in basso a destra, con un'ombra morbida per leggerlo anche su fondi chiari."""
    global _LOGO
    if _LOGO is None:
        logo = Image.open(ROOT / "assets" / "logo.png").convert("RGBA")
        w = 190
        logo = logo.resize((w, round(logo.height * w / logo.width)), Image.LANCZOS)
        pad = 16
        shadow = Image.new("RGBA", (logo.width + 2 * pad, logo.height + 2 * pad), (0, 0, 0, 0))
        alpha = logo.getchannel("A").point(lambda a: a * 0.55)
        shadow.paste((0, 0, 0, 255), (pad, pad + 2), alpha)
        shadow = shadow.filter(ImageFilter.GaussianBlur(7))
        shadow.alpha_composite(logo, (pad, pad))
        _LOGO = shadow
    out = img.convert("RGBA")
    margin = 28
    out.alpha_composite(_LOGO, (W - _LOGO.width - margin, H - _LOGO.height - margin))
    return out.convert("RGB")


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
            key = f'{photo["src"]}|{photo["fit"]}|v4'
            wanted[name] = key
            if manifest.get(name) == key and (folder / name).exists():
                continue
            try:
                img = enhance(load(photo["src"]))
                # una foto orizzontale ritagliata a 4:5 perde le persone ai lati: la teniamo intera
                use_cover = photo["fit"] == "cover" and img.width / img.height < 0.95
                out = add_logo(cover(img) if use_cover else contain(img))
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

#!/usr/bin/env python3
"""Genera le storie degli highlight (1080x1920) e le copertine.

Per ogni highlight di data/highlights.json:
  stories/<venue>/0.jpg     storia di apertura: logo, nome del locale, sottotitolo, numero di incontri
  stories/<venue>/<n>.jpg   una storia per foto, con nome del locale e logo
  stories/<venue>/cover.jpg copertina dell'highlight (da caricare a mano in app)
"""
import json
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_images import ROOT, add_logo, contain, cover, enhance, load  # noqa: E402

W, H = 1080, 1920
ORANGE = (254, 174, 78)
INK = (92, 46, 12)
WHITE = (255, 255, 255)
FONT = ROOT / "assets" / "fonts" / "BricolageGrotesque.ttf"
LOGO = Image.open(ROOT / "assets" / "logo.png").convert("RGBA")
RAINBOW = LOGO.crop((0, 0, LOGO.width, round(LOGO.height * 0.47)))  # solo l'arcobaleno


def font(size: int, weight: str = "ExtraBold") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_name(weight)
    return f


def fit(draw: ImageDraw.ImageDraw, text: str, max_w: int, size: int, weight: str = "ExtraBold"):
    while size > 30:
        f = font(size, weight)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return font(size, weight)


def shadow_text(img: Image.Image, xy, text: str, f, fill=WHITE, anchor="mm") -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((xy[0], xy[1] + 4), text, font=f, fill=(90, 40, 0, 110), anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(layer)
    ImageDraw.Draw(img).text(xy, text, font=f, fill=fill, anchor=anchor)


def paste_scaled(img: Image.Image, src: Image.Image, width: int, center_y: int) -> int:
    s = src.resize((width, round(src.height * width / src.width)), Image.LANCZOS)
    img.alpha_composite(s, ((W - s.width) // 2, center_y - s.height // 2))
    return s.height


def opening(h: dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), ORANGE + (255,))
    paste_scaled(img, LOGO, 560, 560)
    d = ImageDraw.Draw(img)
    shadow_text(img, (W // 2, 1010), h["title"], fit(d, h["title"], 940, 180))
    d.text((W // 2, 1150), h["subtitle"], font=fit(d, h["subtitle"], 900, 60, "SemiBold"), fill=INK, anchor="mm")
    d.text((W // 2, 1240), h["line"], font=fit(d, h["line"], 900, 48, "Medium"), fill=INK, anchor="mm")
    d.text((W // 2, 1640), "@la.mesa.arcoiris", font=font(44, "Bold"), fill=WHITE, anchor="mm")
    return img.convert("RGB")


def photo_story(src: str, title: str) -> Image.Image:
    photo = enhance(load(src))
    base = cover(photo, 0.4, W, H) if photo.width / photo.height < 0.7 else contain(photo, W, H)
    img = base.convert("RGBA")
    d = ImageDraw.Draw(img)
    f = font(46, "Bold")
    tw = d.textlength(title, font=f)
    pill = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle((60, 262, 60 + tw + 56, 338), radius=38, fill=(20, 12, 4, 150))
    img.alpha_composite(pill)
    d.text((60 + 28, 300), title, font=f, fill=WHITE, anchor="lm")
    return add_logo(img.convert("RGB"), bottom=270)


def highlight_cover(h: dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), ORANGE + (255,))
    paste_scaled(img, RAINBOW, 420, 830)
    d = ImageDraw.Draw(img)
    shadow_text(img, (W // 2, 1060), h["title"], fit(d, h["title"], 560, 120))
    return img.convert("RGB")


def main() -> int:
    highlights = json.loads((ROOT / "data/highlights.json").read_text())
    errors = 0
    for h in highlights:
        folder = ROOT / "stories" / h["venue"]
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.jpg"):
            old.unlink()
        opening(h).save(folder / "0.jpg", "JPEG", quality=90)
        highlight_cover(h).save(folder / "cover.jpg", "JPEG", quality=90)
        for n, src in enumerate(h["photos"], start=1):
            try:
                photo_story(src, h["title"]).save(folder / f"{n}.jpg", "JPEG", quality=90)
            except Exception as exc:
                errors += 1
                print(f"ERR  {h['venue']}/{n}: {exc}", file=sys.stderr)
        print(f"ok   {h['venue']}: {len(h['photos']) + 1} storie")
    print(f"fatto, errori: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

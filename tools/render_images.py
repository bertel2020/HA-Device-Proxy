"""Renders the app's icon.png and logo.png from the icon geometry (128-unit grid)."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ACCENT = (10, 106, 168, 255)
WHITE = (255, 255, 255, 255)
TEXT = (27, 31, 36, 255)
MUTED = (91, 98, 112, 255)
SS = 8  # supersampling


def draw_icon(
    size: int, *, pins: bool = True, stroke: float = 6.0, node: float = 8.0
) -> Image.Image:
    big = size * SS
    k = big / 128
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, big - 1, big - 1), radius=28 * k, fill=ACCENT)
    w = stroke * k

    def line(points: list[tuple[float, float]], closed: bool = False) -> None:
        pts = [(x * k, y * k) for x, y in points]
        if closed:
            pts.append(pts[0])
        d.line(pts, fill=WHITE, width=round(w))
        for x, y in pts:
            d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=WHITE)

    def dot(x: float, y: float, r: float) -> None:
        d.ellipse(((x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k), fill=WHITE)

    line([(16, 46), (70, 46), (64, 82), (22, 82)], closed=True)
    line([(67, 64), (84, 64)])
    for end in [(104, 40), (108, 64), (104, 88)]:
        line([(84, 64), end])
        dot(*end, node)
    if pins:
        for x, y in [(31, 58), (43, 58), (55, 58), (37, 70), (49, 70)]:
            dot(x, y, 3.5)
    return img.resize((size, size), Image.LANCZOS)


def bold_font(px: int) -> ImageFont.FreeTypeFont:
    path = "/System/Library/Fonts/HelveticaNeue.ttc"
    for index in range(16):
        try:
            font = ImageFont.truetype(path, px, index=index)
        except OSError:
            break
        if font.getname()[1] == "Bold":
            return font
    return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", px)


def medium_font(px: int) -> ImageFont.FreeTypeFont:
    path = "/System/Library/Fonts/HelveticaNeue.ttc"
    for index in range(16):
        try:
            font = ImageFont.truetype(path, px, index=index)
        except OSError:
            break
        if font.getname()[1] == "Medium":
            return font
    return bold_font(px)


def draw_logo(width: int, height: int) -> Image.Image:
    scale = SS
    W, H = width * scale, height * scale
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    icon_px = round(height * 0.72)
    icon = draw_icon(icon_px * scale, stroke=6.5, node=8.5)
    top = (H - icon.height) // 2
    img.alpha_composite(icon, (0, top))
    d = ImageDraw.Draw(img)
    left = icon.width + round(height * 0.14 * scale)
    room = W - left - scale * 4
    word_px, sub_px = round(height * 0.34 * scale), round(height * 0.12 * scale)
    while bold_font(word_px).getlength("DeviceProxy") > room:
        word_px -= scale
    while medium_font(sub_px).getlength("SERIAL · MODBUS · NETWORK") > room:
        sub_px -= scale
    word = bold_font(word_px)
    sub = medium_font(sub_px)
    asc = word.getbbox("S")[3]
    y = top + round(icon.height * 0.18)
    x: float = left
    for part, color in (("Device", TEXT), ("Proxy", ACCENT)):
        d.text((x, y), part, font=word, fill=color)
        x += d.textlength(part, font=word)
    d.text(
        (left, y + asc + round(height * 0.08 * scale)),
        "SERIAL · MODBUS · NETWORK",
        font=sub,
        fill=MUTED,
    )
    return img.resize((width, height), Image.LANCZOS)


if __name__ == "__main__":
    # python3 tools/render_images.py device_proxy  (needs Pillow; fonts from macOS)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    draw_icon(256).save(out / "icon.png")
    draw_logo(500, 200).save(out / "logo.png")

#!/usr/bin/env python3
"""
Generate synthetic Android phone and tablet home screen fixtures for framing tests.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


OUT_DIR = Path(__file__).resolve().parent / "fixtures" / "android-home-screens"
PHONE_DIR = OUT_DIR / "phones"
TABLET_DIR = OUT_DIR / "tablets"

FIXTURES = [
    ("phones", "pixel-5-home-portrait.png", (1080, 2340), "portrait", "Pixel"),
    ("phones", "pixel-5-home-landscape.png", (2340, 1080), "landscape", "Pixel"),
    ("phones", "galaxy-s21-ultra-home-portrait.png", (1440, 3200), "portrait", "Galaxy"),
    ("phones", "galaxy-s21-ultra-home-landscape.png", (3200, 1440), "landscape", "Galaxy"),
    ("tablets", "pixel-slate-home-portrait.png", (2000, 3000), "portrait", "Slate"),
    ("tablets", "pixel-slate-home-landscape.png", (3000, 2000), "landscape", "Slate"),
]


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def wallpaper_gradient(draw: ImageDraw.ImageDraw, width: int, height: int, palette: str) -> None:
    colors = {
        "Pixel": ((36, 49, 83), (102, 94, 255), (167, 235, 255)),
        "Galaxy": ((24, 20, 52), (110, 64, 216), (255, 124, 164)),
        "Slate": ((18, 42, 54), (42, 120, 148), (202, 239, 246)),
    }[palette]
    for y in range(height):
        t = y / max(1, height - 1)
        if t < 0.55:
            local_t = t / 0.55
            start, end = colors[0], colors[1]
        else:
            local_t = (t - 0.55) / 0.45
            start, end = colors[1], colors[2]
        r = round(start[0] + (end[0] - start[0]) * local_t)
        g = round(start[1] + (end[1] - start[1]) * local_t)
        b = round(start[2] + (end[2] - start[2]) * local_t)
        draw.line((0, y, width, y), fill=(r, g, b))


def add_light_blobs(base: Image.Image, width: int, height: int) -> None:
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((-width * 0.2, height * 0.04, width * 0.55, height * 0.62), fill=(255, 255, 255, 38))
    draw.ellipse((width * 0.42, -height * 0.12, width * 1.1, height * 0.38), fill=(255, 255, 255, 30))
    draw.ellipse((width * 0.18, height * 0.58, width * 0.98, height * 1.2), fill=(255, 255, 255, 24))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(20, width // 40)))
    base.alpha_composite(overlay)


def rounded_rect(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], radius: int, fill: tuple[int, ...]) -> None:
    draw.rounded_rectangle(rect, radius=radius, fill=fill)


def draw_status(draw: ImageDraw.ImageDraw, width: int, height: int, orientation: str) -> None:
    font = load_font(max(20, width // 48), bold=True)
    small = load_font(max(14, width // 72))
    top = round(height * 0.022)
    left = round(width * 0.04)
    right = round(width * 0.96)
    draw.text((left, top), "9:41", font=font, fill=(255, 255, 255, 220))
    weather = "72°"
    bbox = draw.textbbox((0, 0), weather, font=small)
    draw.text((right - (bbox[2] - bbox[0]) - 120, top + 8), weather, font=small, fill=(255, 255, 255, 200))
    x = right - 56
    cy = top + 18
    draw.line((x, cy, x + 24, cy), fill=(255, 255, 255, 200), width=3)
    draw.line((x + 4, cy - 8, x + 12, cy), fill=(255, 255, 255, 200), width=3)
    draw.line((x + 12, cy, x + 20, cy - 10), fill=(255, 255, 255, 200), width=3)
    bx = right - 18
    draw.rounded_rectangle((bx - 34, cy - 10, bx, cy + 10), radius=6, outline=(255, 255, 255, 210), width=2)
    draw.rounded_rectangle((bx - 31, cy - 7, bx - 9, cy + 7), radius=4, fill=(255, 255, 255, 180))


def draw_search(draw: ImageDraw.ImageDraw, width: int, height: int, orientation: str) -> None:
    if orientation == "portrait":
        rect = (round(width * 0.08), round(height * 0.14), round(width * 0.92), round(height * 0.19))
    else:
        rect = (round(width * 0.12), round(height * 0.11), round(width * 0.88), round(height * 0.19))
    rounded_rect(draw, rect, (rect[3] - rect[1]) // 2, (255, 255, 255, 74))
    font = load_font(max(20, width // 54))
    draw.text((rect[0] + 28, rect[1] + 14), "Search", font=font, fill=(245, 245, 245, 210))


def draw_widgets(draw: ImageDraw.ImageDraw, width: int, height: int, orientation: str) -> None:
    radius = max(28, width // 48)
    fill = (255, 255, 255, 58)
    if orientation == "portrait":
        rects = [
            (round(width * 0.07), round(height * 0.23), round(width * 0.47), round(height * 0.4)),
            (round(width * 0.53), round(height * 0.23), round(width * 0.93), round(height * 0.4)),
        ]
    else:
        rects = [
            (round(width * 0.07), round(height * 0.26), round(width * 0.31), round(height * 0.52)),
            (round(width * 0.35), round(height * 0.26), round(width * 0.59), round(height * 0.52)),
            (round(width * 0.63), round(height * 0.26), round(width * 0.87), round(height * 0.52)),
        ]
    for rect in rects:
        rounded_rect(draw, rect, radius, fill)


def icon_color(index: int) -> tuple[int, int, int]:
    palette = [
        (66, 133, 244),
        (234, 67, 53),
        (251, 188, 5),
        (52, 168, 83),
        (171, 71, 188),
        (0, 188, 212),
        (255, 112, 67),
        (124, 179, 66),
    ]
    return palette[index % len(palette)]


def draw_icons(base: Image.Image, width: int, height: int, orientation: str) -> None:
    draw = ImageDraw.Draw(base)
    icon_size = round(width * (0.13 if orientation == "portrait" else 0.075))
    cols = 4 if orientation == "portrait" else 7
    rows = 4 if orientation == "portrait" else 2
    gap_x = round(icon_size * 0.34)
    gap_y = round(icon_size * 0.42)
    start_x = round((width - (cols * icon_size + (cols - 1) * gap_x)) / 2)
    start_y = round(height * (0.45 if orientation == "portrait" else 0.59))
    label_font = load_font(max(16, icon_size // 3), bold=True)

    index = 0
    for row in range(rows):
        for col in range(cols):
            x0 = start_x + col * (icon_size + gap_x)
            y0 = start_y + row * (icon_size + gap_y)
            rounded_rect(draw, (x0, y0, x0 + icon_size, y0 + icon_size), max(18, icon_size // 4), (*icon_color(index), 255))
            label = chr(ord("A") + index % 26)
            bbox = draw.textbbox((0, 0), label, font=label_font)
            draw.text((x0 + (icon_size - (bbox[2] - bbox[0])) / 2, y0 + (icon_size - (bbox[3] - bbox[1])) / 2 - 3), label, font=label_font, fill=(255, 255, 255, 225))
            index += 1


def draw_dock(draw: ImageDraw.ImageDraw, width: int, height: int, orientation: str) -> None:
    dock_h = round(height * (0.09 if orientation == "portrait" else 0.13))
    y0 = height - dock_h - round(height * 0.03)
    x0 = round(width * 0.08)
    x1 = width - x0
    rounded_rect(draw, (x0, y0, x1, y0 + dock_h), dock_h // 2, (255, 255, 255, 74))
    icon_size = round(dock_h * 0.58)
    gap = round(icon_size * 0.3)
    slots = 5 if orientation == "portrait" else 7
    total_w = slots * icon_size + (slots - 1) * gap
    start_x = round((width - total_w) / 2)
    iy = y0 + (dock_h - icon_size) // 2
    for idx in range(slots):
        ix = start_x + idx * (icon_size + gap)
        rounded_rect(draw, (ix, iy, ix + icon_size, iy + icon_size), max(14, icon_size // 4), (*icon_color(idx + 11), 255))


def generate_fixture(folder: str, filename: str, size: tuple[int, int], orientation: str, palette: str) -> None:
    width, height = size
    base = Image.new("RGBA", size, (0, 0, 0, 255))
    draw = ImageDraw.Draw(base)
    wallpaper_gradient(draw, width, height, palette)
    add_light_blobs(base, width, height)
    draw = ImageDraw.Draw(base)
    draw_status(draw, width, height, orientation)
    draw_search(draw, width, height, orientation)
    draw_widgets(draw, width, height, orientation)
    draw_icons(base, width, height, orientation)
    draw = ImageDraw.Draw(base)
    draw_dock(draw, width, height, orientation)

    out_dir = PHONE_DIR if folder == "phones" else TABLET_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    base.save(out_dir / filename)


def main() -> int:
    for folder, filename, size, orientation, palette in FIXTURES:
        generate_fixture(folder, filename, size, orientation, palette)
        print(f"[done] {folder}/{filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

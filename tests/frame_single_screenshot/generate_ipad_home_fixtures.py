#!/usr/bin/env python3
"""
Generate synthetic iPad home screen fixtures for framing tests.

These are intentionally generic, deterministic home-screen-like images sized to
match common iPad screenshot buckets. They avoid depending on Simulator UI
automation for landscape captures.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


OUT_DIR = Path(__file__).resolve().parent / "fixtures" / "ipad-home-screens"

FIXTURES = [
    ("ipad-pro-11-home-portrait.png", (1668, 2420), "portrait"),
    ("ipad-pro-11-home-landscape.png", (2420, 1668), "landscape"),
    ("ipad-pro-13-home-portrait.png", (2064, 2752), "portrait"),
    ("ipad-pro-13-home-landscape.png", (2752, 2064), "landscape"),
]


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def draw_wallpaper(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    for y in range(height):
        t = y / max(1, height - 1)
        r = round(77 + (233 - 77) * t)
        g = round(94 + (236 - 94) * t)
        b = round(140 + (252 - 140) * t)
        draw.line((0, y, width, y), fill=(r, g, b))


def add_blobs(base: Image.Image, width: int, height: int) -> None:
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((-width * 0.15, height * 0.08, width * 0.5, height * 0.62), fill=(255, 190, 140, 72))
    draw.ellipse((width * 0.45, -height * 0.08, width * 1.08, height * 0.46), fill=(120, 220, 255, 68))
    draw.ellipse((width * 0.2, height * 0.48, width * 0.95, height * 1.12), fill=(130, 110, 255, 52))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(24, width // 32)))
    base.alpha_composite(overlay)


def rounded_panel(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], radius: int, fill: tuple[int, ...]) -> None:
    draw.rounded_rectangle(rect, radius=radius, fill=fill)


def draw_status_bar(draw: ImageDraw.ImageDraw, width: int, height: int, orientation: str) -> None:
    font = load_font(max(24, width // 38), bold=True)
    top = round(height * 0.03)
    left = round(width * 0.05)
    right = round(width * 0.95)
    draw.text((left, top), "9:41", font=font, fill=(255, 255, 255, 235))

    cy = top + font.size // 2
    x = right
    battery_w = round(width * 0.032)
    battery_h = max(12, battery_w // 2)
    x -= battery_w
    draw.rounded_rectangle((x, cy - battery_h // 2, x + battery_w, cy + battery_h // 2), radius=4, outline=(255, 255, 255, 230), width=2)
    draw.rounded_rectangle((x + battery_w + 2, cy - battery_h // 4, x + battery_w + 5, cy + battery_h // 4), radius=2, fill=(255, 255, 255, 230))
    x -= round(width * 0.028)
    for index, bar_h in enumerate((8, 11, 14, 17)):
        bx = x - index * 8
        draw.rounded_rectangle((bx, cy - bar_h // 2, bx + 4, cy + bar_h // 2), radius=2, fill=(255, 255, 255, 220))
    x -= round(width * 0.04)
    draw.arc((x - 18, cy - 18, x + 18, cy + 18), start=210, end=330, fill=(255, 255, 255, 220), width=3)
    draw.arc((x - 10, cy - 10, x + 10, cy + 10), start=215, end=325, fill=(255, 255, 255, 220), width=3)
    draw.ellipse((x - 2, cy - 2, x + 2, cy + 2), fill=(255, 255, 255, 220))

    if orientation == "landscape":
        island_w = round(width * 0.1)
        island_h = round(height * 0.05)
    else:
        island_w = round(width * 0.12)
        island_h = round(height * 0.036)
    island_x = (width - island_w) // 2
    island_y = top - 6
    draw.rounded_rectangle((island_x, island_y, island_x + island_w, island_y + island_h), radius=island_h // 2, fill=(8, 12, 18, 255))


def draw_widgets(draw: ImageDraw.ImageDraw, width: int, height: int, orientation: str) -> None:
    radius = max(28, width // 42)
    panel_fill = (255, 255, 255, 78)
    if orientation == "portrait":
        weather = (round(width * 0.05), round(height * 0.11), round(width * 0.42), round(height * 0.26))
        stack = (round(width * 0.47), round(height * 0.11), round(width * 0.95), round(height * 0.26))
    else:
        weather = (round(width * 0.05), round(height * 0.1), round(width * 0.31), round(height * 0.31))
        stack = (round(width * 0.34), round(height * 0.1), round(width * 0.62), round(height * 0.31))

    rounded_panel(draw, weather, radius, panel_fill)
    rounded_panel(draw, stack, radius, panel_fill)

    large_font = load_font(max(42, width // 28), bold=True)
    body_font = load_font(max(22, width // 52))

    wx0, wy0, _, _ = weather
    draw.text((wx0 + 28, wy0 + 22), "Cupertino", font=body_font, fill=(255, 255, 255, 230))
    draw.text((wx0 + 26, wy0 + 58), "72°", font=large_font, fill=(255, 255, 255, 240))
    draw.text((wx0 + 34, wy0 + 126), "Sunny all afternoon", font=body_font, fill=(255, 255, 255, 210))

    sx0, sy0, sx1, sy1 = stack
    draw.text((sx0 + 28, sy0 + 22), "Calendar", font=body_font, fill=(255, 255, 255, 230))
    draw.text((sx0 + 28, sy0 + 64), "Saturday 14", font=large_font, fill=(255, 255, 255, 240))
    draw.text((sx0 + 30, sy1 - 56), "Design review at 1:00 PM", font=body_font, fill=(255, 255, 255, 210))


def app_color(index: int) -> tuple[int, int, int]:
    palette = [
        (255, 108, 117),
        (255, 183, 77),
        (116, 203, 120),
        (92, 167, 255),
        (143, 120, 255),
        (255, 126, 216),
        (106, 220, 213),
        (255, 214, 102),
    ]
    return palette[index % len(palette)]


def draw_icons(base: Image.Image, width: int, height: int, orientation: str) -> None:
    draw = ImageDraw.Draw(base)
    icon_size = round(width * (0.092 if orientation == "portrait" else 0.07))
    gap_x = round(icon_size * 0.32)
    gap_y = round(icon_size * 0.28)
    cols = 5 if orientation == "portrait" else 7
    rows = 5 if orientation == "portrait" else 3
    start_x = round((width - (cols * icon_size + (cols - 1) * gap_x)) / 2)
    start_y = round(height * (0.31 if orientation == "portrait" else 0.38))
    radius = max(18, icon_size // 4)
    icon_font = load_font(max(18, icon_size // 3), bold=True)

    index = 0
    for row in range(rows):
        for col in range(cols):
            x0 = start_x + col * (icon_size + gap_x)
            y0 = start_y + row * (icon_size + gap_y)
            color = app_color(index)
            rounded_panel(draw, (x0, y0, x0 + icon_size, y0 + icon_size), radius, (*color, 255))
            label = chr(ord("A") + (index % 26))
            bbox = draw.textbbox((0, 0), label, font=icon_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((x0 + (icon_size - tw) / 2, y0 + (icon_size - th) / 2 - 4), label, font=icon_font, fill=(255, 255, 255, 230))
            index += 1


def draw_dock(draw: ImageDraw.ImageDraw, width: int, height: int, orientation: str) -> None:
    dock_h = round(height * (0.105 if orientation == "portrait" else 0.145))
    dock_y0 = height - dock_h - round(height * 0.03)
    dock_x0 = round(width * 0.08)
    dock_x1 = width - dock_x0
    radius = dock_h // 2
    rounded_panel(draw, (dock_x0, dock_y0, dock_x1, dock_y0 + dock_h), radius, (255, 255, 255, 86))
    icon_size = round(dock_h * 0.58)
    gap = round(icon_size * 0.33)
    slots = 6 if orientation == "portrait" else 8
    total_w = slots * icon_size + (slots - 1) * gap
    start_x = round((width - total_w) / 2)
    y0 = dock_y0 + (dock_h - icon_size) // 2
    for index in range(slots):
        x0 = start_x + index * (icon_size + gap)
        rounded_panel(draw, (x0, y0, x0 + icon_size, y0 + icon_size), max(16, icon_size // 4), (*app_color(index + 10), 255))


def generate_fixture(filename: str, size: tuple[int, int], orientation: str) -> None:
    width, height = size
    base = Image.new("RGBA", size, (0, 0, 0, 255))
    draw = ImageDraw.Draw(base)
    draw_wallpaper(draw, width, height)
    add_blobs(base, width, height)
    draw = ImageDraw.Draw(base)
    draw_status_bar(draw, width, height, orientation)
    draw_widgets(draw, width, height, orientation)
    draw_icons(base, width, height, orientation)
    draw = ImageDraw.Draw(base)
    draw_dock(draw, width, height, orientation)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base.save(OUT_DIR / filename)


def main() -> int:
    for filename, size, orientation in FIXTURES:
        generate_fixture(filename, size, orientation)
        print(f"[done] {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

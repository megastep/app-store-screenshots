#!/usr/bin/env python3
"""
Measure screen inset geometry for bezel PNGs in a frame directory.

The script detects the largest interior transparent window in each frame image,
which corresponds to the screen opening used by Fastlane's frameit assets.
It emits both JSON data and an optional TypeScript `FRAME_SPECS` skeleton that
fits the app-store-screenshots skill templates.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is expected locally, but keep fallback support.
    Image = None


DEFAULT_FRAME_DIR = str(Path.home() / ".fastlane" / "frameit" / "latest")
TRANSPARENT_ALPHA_THRESHOLD = 254
RADIUS_ALPHA_THRESHOLD = 0


def build_frame_key(path: Path) -> str:
    return path.stem.lower()


def build_frame_path(filename: str) -> str:
    return f"/frames/{filename}"


def is_image(path: Path) -> bool:
    return path.suffix.lower() in {".png", ".jpg", ".jpeg"}


def infer_family(name: str) -> str:
    lowered = name.lower()
    if "macbook" in lowered or lowered.startswith("apple-macbook"):
        return "mac"
    if "pixel slate" in lowered:
        return "android-tablet"
    if any(term in lowered for term in ("pixel", "galaxy", "nexus", "htc", "huawei", "moto")):
        return "android-phone"
    if "ipad" in lowered:
        return "ipad"
    if "iphone" in lowered:
        return "iphone"
    return "other"


def read_image_alpha_size(path: Path) -> tuple[int, int, bytes]:
    if path.suffix.lower() != ".png":
        raise ValueError("Only PNG frame measurement is supported")

    if Image is not None:
        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            width, height = rgba.size
            return width, height, rgba.getchannel("A").tobytes()

    return read_png_alpha_size(path)


def read_png_alpha_size(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Only PNG frame measurement is supported")

    offset = 8
    width = height = None
    idat = bytearray()
    color_type = bit_depth = None
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBBBBB", chunk_data[:13])[:4]
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width is None or height is None:
        raise ValueError("Invalid PNG: missing IHDR")

    import zlib

    raw = zlib.decompress(bytes(idat))
    if bit_depth != 8:
        raise ValueError("Unsupported PNG bit depth")
    channels_by_color = {6: 4, 2: 3, 0: 1}
    if color_type not in channels_by_color:
        raise ValueError(f"Unsupported PNG color type: {color_type}")
    channels = channels_by_color[color_type]
    stride = width * channels
    rows: list[bytearray] = []
    i = 0
    prev = bytearray(stride)
    for _ in range(height):
        filter_type = raw[i]
        i += 1
        row = bytearray(raw[i : i + stride])
        i += stride
        if filter_type == 1:
            for x in range(channels, stride):
                row[x] = (row[x] + row[x - channels]) & 0xFF
        elif filter_type == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 0xFF
        elif filter_type == 3:
            for x in range(stride):
                left = row[x - channels] if x >= channels else 0
                up = prev[x]
                row[x] = (row[x] + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            for x in range(stride):
                a = row[x - channels] if x >= channels else 0
                b = prev[x]
                c = prev[x - channels] if x >= channels else 0
                p = a + b - c
                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                row[x] = (row[x] + pr) & 0xFF
        elif filter_type != 0:
            raise ValueError(f"Unsupported PNG filter: {filter_type}")
        rows.append(row)
        prev = row

    alpha = bytearray(width * height)
    if color_type == 6:
        for y, row in enumerate(rows):
            for x in range(width):
                alpha[y * width + x] = row[x * 4 + 3]
    elif color_type == 2:
        alpha[:] = b"\xff" * (width * height)
    else:
        alpha[:] = b"\xff" * (width * height)

    return width, height, bytes(alpha)


def transparent_runs(alpha: bytes, width: int, y: int, threshold: int = TRANSPARENT_ALPHA_THRESHOLD) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    in_run = False
    start = 0
    row_offset = y * width
    for x in range(width + 1):
        transparent = x < width and alpha[row_offset + x] <= threshold
        if transparent and not in_run:
            start = x
            in_run = True
        elif in_run and not transparent:
            end = x - 1
            if start > 0 and end < width - 1:
                runs.append((start, end))
            in_run = False
    return runs


def infer_top_overlay_cutout(
    alpha: bytes,
    frame_w: int,
    screen: dict,
    family: str,
    orientation: str,
) -> dict | None:
    if family != "iphone" or orientation != "portrait":
        return None

    screen_width = int(screen["width"])
    current_top = int(screen["top"])
    if current_top <= 0:
        return None

    min_display_width = screen_width * 0.3
    min_run_width = max(40, round(screen_width * 0.12))
    min_total_width = screen_width * 0.4
    display_rows: list[int] = []
    shoulder_rows: list[tuple[int, list[tuple[int, int]]]] = []

    for y in range(current_top - 1, -1, -1):
        interior_runs = [
            (start, end)
            for start, end in transparent_runs(alpha, frame_w, y)
            if start > 0 and end < frame_w - 1
        ]
        display_width = sum(end - start + 1 for start, end in interior_runs)
        if display_width >= min_display_width:
            display_rows.append(y)
        elif display_rows:
            break

    for y in range(current_top - 1, -1, -1):
        runs = [
            (start, end)
            for start, end in transparent_runs(alpha, frame_w, y)
            if (end - start + 1) >= min_run_width
        ]
        total_width = sum(end - start + 1 for start, end in runs)
        if len(runs) >= 2 and total_width >= min_total_width:
            shoulder_rows.append((y, runs))
            continue
        if shoulder_rows:
            break

    if not shoulder_rows:
        return None

    display_top = min(display_rows) if display_rows else min(y for y, _ in shoulder_rows)
    cutout_top = min(y for y, _ in shoulder_rows)
    if display_top >= current_top:
        return None

    # Use the lowest split row because it most closely matches the full display width
    # immediately before the transparent regions merge into one uninterrupted screen run.
    _, anchor_runs = max(shoulder_rows, key=lambda item: item[0])
    left_run = anchor_runs[0]
    right_run = anchor_runs[-1]
    cutout_left = left_run[1] + 1
    cutout_right = right_run[0] - 1
    if cutout_right < cutout_left:
        return None

    return {
        "screenTop": display_top,
        "cutout": {
            "left": cutout_left,
            "top": cutout_top,
            "width": cutout_right - cutout_left + 1,
            "height": current_top - cutout_top,
        },
    }


def radius_row_width(runs: list[tuple[int, int]], center_x: float, screen_w: int) -> tuple[int | None, bool]:
    total_width = sum(end - start + 1 for start, end in runs)
    if len(runs) > 1 and total_width >= screen_w * 0.85:
        return total_width, True
    centered_run = next(((start, end) for start, end in runs if start <= center_x <= end), None)
    if centered_run:
        return centered_run[1] - centered_run[0] + 1, False
    return None, False


def detect_screen(alpha: bytes, width: int, height: int) -> dict | None:
    rows: list[tuple[int, list[tuple[int, int]], int]] = []
    max_width = 0
    for y in range(height):
        runs = transparent_runs(alpha, width, y)
        if not runs:
            continue
        widest = max(end - start + 1 for start, end in runs)
        max_width = max(max_width, widest)
        rows.append((y, runs, widest))

    if not rows or max_width == 0:
        return None

    candidates = [row for row in rows if row[2] >= max_width * 0.7]
    if not candidates:
        return None

    groups: list[list[tuple[int, list[tuple[int, int]], int]]] = []
    current = [candidates[0]]
    for row in candidates[1:]:
        if row[0] == current[-1][0] + 1:
            current.append(row)
        else:
            groups.append(current)
            current = [row]
    groups.append(current)
    group = max(groups, key=lambda g: sum(item[2] for item in g))

    rows_by_y = {row[0]: row for row in rows}
    y0 = group[0][0]
    y1 = group[-1][0]
    center_x = sum((start + end) / 2 for _, runs, _ in group for start, end in runs) / sum(len(runs) for _, runs, _ in group)
    while y0 - 1 in rows_by_y:
        prev = rows_by_y[y0 - 1]
        if prev[2] < max_width * 0.2:
            break
        if not any(start <= center_x <= end for start, end in prev[1]):
            break
        y0 -= 1
    while y1 + 1 in rows_by_y:
        nxt = rows_by_y[y1 + 1]
        if nxt[2] < max_width * 0.2:
            break
        if not any(start <= center_x <= end for start, end in nxt[1]):
            break
        y1 += 1

    selected = [rows_by_y[y] for y in range(y0, y1 + 1) if y in rows_by_y]
    center_rows = [
        (y, [(start, end) for start, end in runs if start <= center_x <= end], widest)
        for y, runs, widest in selected
        if any(start <= center_x <= end for start, end in runs)
    ]
    horizontal_source = center_rows or selected
    x0 = min(start for _, runs, _ in horizontal_source for start, _ in runs)
    x1 = max(end for _, runs, _ in horizontal_source for _, end in runs)
    screen_w = x1 - x0 + 1
    screen_h = y1 - y0 + 1

    radius_rows = [(y, transparent_runs(alpha, width, y, threshold=RADIUS_ALPHA_THRESHOLD)) for y, _, _ in selected]
    top_centered_rows: list[tuple[int, int, bool]] = []
    seen_narrowed_top = False
    top_band_limit = y0 + min(max(48, screen_h // 12), 200)
    for y, runs in radius_rows:
        if y > top_band_limit:
            break
        run_width, is_split_cutout = radius_row_width(runs, center_x, screen_w)
        if run_width is not None:
            if run_width < screen_w * 0.995:
                seen_narrowed_top = seen_narrowed_top or not is_split_cutout
                top_centered_rows.append((y, run_width, is_split_cutout))
                continue
            if not seen_narrowed_top:
                top_centered_rows.append((y, run_width, is_split_cutout))
                continue
            break
        if top_centered_rows:
            break

    if top_centered_rows:
        min_centered_width = min(width for _, width, _ in top_centered_rows)
        rx = max(0.0, (screen_w - min_centered_width) / 2)
        narrowed_rows = [y for y, run_width, is_split_cutout in top_centered_rows if run_width < screen_w * 0.995 and not is_split_cutout]
        ry = max(0.0, (max(narrowed_rows) - y0 + 1) if narrowed_rows else 0.0)
    else:
        first_single = next(((y, runs) for y, runs in radius_rows if len(runs) == 1), None)
        if first_single:
            single_width = first_single[1][0][1] - first_single[1][0][0] + 1
            rx = max(0.0, (screen_w - single_width) / 2)
            ry = max(0.0, first_single[0] - y0)
        else:
            rx = 0.0
            ry = 0.0

    has_cutout = any(len(runs) > 1 for _, runs, _ in selected[: max(1, min(16, screen_h // 8 or 1))])

    return {
        "left": x0,
        "top": y0,
        "width": screen_w,
        "height": screen_h,
        "rx": rx,
        "ry": ry,
        "hasCutout": has_cutout,
    }


def is_plausible_screen(screen: dict, frame_w: int, frame_h: int) -> bool:
    width_ratio = screen["width"] / frame_w
    height_ratio = screen["height"] / frame_h
    area_ratio = (screen["width"] * screen["height"]) / (frame_w * frame_h)
    screen_center_x = screen["left"] + (screen["width"] / 2)
    frame_center_x = frame_w / 2
    center_offset_ratio = abs(screen_center_x - frame_center_x) / frame_w

    return (
        width_ratio >= 0.35
        and height_ratio >= 0.35
        and area_ratio >= 0.2
        and center_offset_ratio <= 0.2
    )


def measure_frame(path: Path) -> dict | None:
    if path.suffix.lower() != ".png":
        return None
    try:
        frame_w, frame_h, alpha = read_image_alpha_size(path)
    except Exception as exc:
        print(f"[warn] skipping {path.name}: {exc}")
        return None
    screen = detect_screen(alpha, frame_w, frame_h)
    if not screen:
        print(f"[warn] no interior screen opening detected in {path.name}")
        return None
    if not is_plausible_screen(screen, frame_w, frame_h):
        print(f"[warn] implausible screen opening detected in {path.name}")
        return None
    filename = path.name
    key = build_frame_key(path)
    family = infer_family(filename)
    orientation = "landscape" if frame_w > frame_h else "portrait"
    top_overlay = infer_top_overlay_cutout(alpha, frame_w, screen, family, orientation)
    if top_overlay:
        original_top = screen["top"]
        screen["top"] = top_overlay["screenTop"]
        screen["height"] += original_top - top_overlay["screenTop"]
        screen["hasCutout"] = True
        screen["hasTopOverlayCutout"] = True
    return {
        "key": key,
        "filename": filename,
        "family": family,
        "orientation": orientation,
        "frameW": frame_w,
        "frameH": frame_h,
        "framePath": build_frame_path(filename),
        "screen": screen,
        "screenPercent": {
            "left": round(screen["left"] / frame_w * 100, 4),
            "top": round(screen["top"] / frame_h * 100, 4),
            "width": round(screen["width"] / frame_w * 100, 4),
            "height": round(screen["height"] / frame_h * 100, 4),
            "rx": round(screen["rx"] / screen["width"] * 100, 4) if screen["width"] else 0.0,
            "ry": round(screen["ry"] / screen["height"] * 100, 4) if screen["height"] else 0.0,
        },
        **(
            {
                "topOverlayCutout": top_overlay["cutout"],
                "topOverlayCutoutPercent": {
                    "left": round(top_overlay["cutout"]["left"] / frame_w * 100, 4),
                    "top": round(top_overlay["cutout"]["top"] / frame_h * 100, 4),
                    "width": round(top_overlay["cutout"]["width"] / frame_w * 100, 4),
                    "height": round(top_overlay["cutout"]["height"] / frame_h * 100, 4),
                },
            }
            if top_overlay
            else {}
        ),
    }


def build_markdown(entries: list[dict], source_label: str) -> str:
    lines = [
        "# Frame Insets Reference",
        "",
        f"Source: `{source_label}`",
        "",
        f"Entries: {len(entries)}",
        "",
        "| Filename | Family | Orientation | Frame | Screen Insets | Screen Size | Radius | Cutout | Top Overlay |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        screen = entry["screen"]
        top_overlay = entry.get("topOverlayCutout")
        overlay_text = (
            f'left {top_overlay["left"]}, top {top_overlay["top"]}, {top_overlay["width"]} x {top_overlay["height"]}'
            if top_overlay
            else "-"
        )
        lines.append(
            "| {filename} | {family} | {orientation} | {frameW} x {frameH} | "
            "left {left}, top {top} | {width} x {height} | rx {rx:.1f}, ry {ry:.1f} | {hasCutout} | {overlay_text} |".format(
                **entry,
                **screen,
                overlay_text=overlay_text,
            )
        )
    lines.append("")
    return "\n".join(lines)


def build_ts(entries: list[dict]) -> str:
    lines = [
        "export const MEASURED_FRAME_SPECS = {",
    ]
    for entry in entries:
        sp = entry["screenPercent"]
        lines.extend(
            [
                f'  "{entry["key"]}": {{',
                f'    framePath: {json.dumps(entry["framePath"])},',
                f'    frameW: {entry["frameW"]},',
                f'    frameH: {entry["frameH"]},',
                "    screen: {",
                f'      left: {sp["left"]},',
                f'      top: {sp["top"]},',
                f'      width: {sp["width"]},',
                f'      height: {sp["height"]},',
                f'      rx: {sp["rx"]},',
                f'      ry: {sp["ry"]},',
                "    },",
                *(
                    [
                        "    topOverlayCutout: {",
                        f'      left: {entry["topOverlayCutoutPercent"]["left"]},',
                        f'      top: {entry["topOverlayCutoutPercent"]["top"]},',
                        f'      width: {entry["topOverlayCutoutPercent"]["width"]},',
                        f'      height: {entry["topOverlayCutoutPercent"]["height"]},',
                        "    },",
                    ]
                    if entry.get("topOverlayCutoutPercent")
                    else []
                ),
                "  },",
            ]
        )
    lines.append("} as const;\n")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure screen inset geometry for all available bezel PNGs.")
    parser.add_argument("--frame-dir", default=DEFAULT_FRAME_DIR, help="Directory containing frame PNGs. Default: ~/.fastlane/frameit/latest")
    parser.add_argument("--json-out", default="frame-insets-latest.json", help="JSON output path. Default: frame-insets-latest.json")
    parser.add_argument("--markdown-out", help="Optional markdown output path for a quick inset reference")
    parser.add_argument("--source-label", help="Optional source label written to markdown output")
    parser.add_argument("--ts-out", help="Optional TypeScript output path for a FRAME_SPECS skeleton")
    parser.add_argument("--limit", type=int, help="Optional max number of frames to emit")
    args = parser.parse_args()

    frame_dir = Path(args.frame_dir).expanduser()
    if not frame_dir.exists():
        raise SystemExit(f"Frame directory does not exist: {frame_dir}")

    entries = []
    for path in sorted(frame_dir.iterdir()):
        if not path.is_file() or not is_image(path):
            continue
        measured = measure_frame(path)
        if measured:
            entries.append(measured)

    entries.sort(key=lambda item: (item["family"], item["orientation"], item["filename"]))
    if args.limit:
        entries = entries[: args.limit]

    json_out = Path(args.json_out).expanduser()
    json_out.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"[done] wrote {json_out}")
    print(f"[done] frames: {len(entries)}")

    if args.markdown_out:
        markdown_out = Path(args.markdown_out).expanduser()
        source_label = args.source_label or frame_dir.name or "frame-cache"
        markdown_out.write_text(build_markdown(entries, source_label), encoding="utf-8")
        print(f"[done] wrote {markdown_out}")

    if args.ts_out:
        ts_out = Path(args.ts_out).expanduser()
        ts_out.write_text(build_ts(entries), encoding="utf-8")
        print(f"[done] wrote {ts_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

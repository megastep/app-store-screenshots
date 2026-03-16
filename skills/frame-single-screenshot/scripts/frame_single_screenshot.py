#!/usr/bin/env python3
"""
Render one framed device screenshot from a flat screenshot image and a Fastlane frame PNG.
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
from pathlib import Path
import re

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


DEFAULT_FRAME_DIR = Path.home() / ".fastlane" / "frameit" / "latest"
SHARED_INSETS_JSON = Path(__file__).resolve().parents[2] / "app-store-screenshots" / "references" / "frame-insets-latest.json"
DEFAULT_SCREEN_BLEED = 2
TRANSPARENT_ALPHA_THRESHOLD = 254
RADIUS_ALPHA_THRESHOLD = 0


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9+]+", " ", value.lower()).strip()


def infer_orientation(width: int, height: int) -> str:
    return "landscape" if width > height else "portrait"


def load_shared_entries() -> list[dict]:
    if not SHARED_INSETS_JSON.exists():
        return []
    return json.loads(SHARED_INSETS_JSON.read_text(encoding="utf-8"))


def build_shared_entry_map(shared_entries: list[dict]) -> dict[str, dict]:
    return {str(entry.get("filename")): entry for entry in shared_entries if entry.get("filename")}


def infer_frame_orientation_hint(path: Path, shared_entry: dict | None) -> str | None:
    if shared_entry and shared_entry.get("orientation") in {"portrait", "landscape"}:
        return str(shared_entry["orientation"])
    normalized = normalize_text(path.stem)
    tokens = set(normalized.split())
    if "landscape" in tokens or "horizontal" in tokens:
        return "landscape"
    if "portrait" in tokens or "vertical" in tokens:
        return "portrait"
    return None


def rank_frame_paths(
    frame_paths: list[Path],
    query: str,
    orientation: str | None,
    color_priority: list[str],
    shared_entry_map: dict[str, dict],
) -> list[tuple[float, Path]]:
    ranked: list[tuple[float, Path]] = []
    normalized_query = normalize_text(query)
    query_tokens = set(normalized_query.split())
    for path in frame_paths:
        normalized_filename = normalize_text(path.stem)
        filename_tokens = set(normalized_filename.split())
        score = difflib.SequenceMatcher(None, normalized_query, normalized_filename).ratio() * 100
        if normalized_query and normalized_query in normalized_filename:
            score += 60
        score += len(filename_tokens & query_tokens) * 12
        if orientation:
            orientation_hint = infer_frame_orientation_hint(path, shared_entry_map.get(path.name))
            if orientation_hint == orientation:
                score += 15
        lowered_filename = path.name.lower()
        for index, color in enumerate(color_priority):
            if color and color.lower() in lowered_filename:
                score += max(1, 10 - index)
        ranked.append((score, path))
    ranked.sort(key=lambda item: (-item[0], item[1].name.lower()))
    return ranked


def resolve_frame_path(
    frame_dir: Path,
    device: str | None,
    frame_file: str | None,
    orientation: str | None,
    color_priority: list[str],
    shared_entry_map: dict[str, dict],
) -> tuple[Path, list[tuple[float, Path]]]:
    if frame_file:
        candidate = Path(frame_file).expanduser()
        if candidate.is_file():
            return candidate, []
        # If the user supplied a path-like value (absolute or containing directories)
        # and it does not exist, fail fast with an explicit error instead of searching frame_dir.
        if candidate.is_absolute() or candidate.parent != Path("."):
            raise SystemExit(f"Frame file does not exist: {candidate}")
        if not frame_dir.exists():
            raise SystemExit(f"Frame directory does not exist: {frame_dir}")
        if not frame_dir.is_dir():
            raise SystemExit(f"Frame directory is not a directory: {frame_dir}")
        frame_paths = sorted(path for path in frame_dir.iterdir() if path.is_file() and path.suffix.lower() == ".png")
        if not frame_paths:
            raise SystemExit(f"No PNG frames found in {frame_dir}")
        matches = [path for path in frame_paths if path.name == frame_file or path.stem == frame_file]
        if not matches:
            raise SystemExit(f'Frame file not found in {frame_dir}: "{frame_file}"')
        return matches[0], []

    if not device:
        raise SystemExit("--device is required unless --frame-file is provided")

    if not frame_dir.exists():
        raise SystemExit(f"Frame directory does not exist: {frame_dir}")
    if not frame_dir.is_dir():
        raise SystemExit(f"Frame directory is not a directory: {frame_dir}")
    frame_paths = sorted(path for path in frame_dir.iterdir() if path.is_file() and path.suffix.lower() == ".png")
    if not frame_paths:
        raise SystemExit(f"No PNG frames found in {frame_dir}")

    ranked = rank_frame_paths(frame_paths, device, orientation, color_priority, shared_entry_map)
    if not ranked or ranked[0][0] <= 0:
        raise SystemExit(f'No suitable Fastlane frame match found for "{device}" in {frame_dir}')
    return ranked[0][1], ranked


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


def radius_row_width(runs: list[tuple[int, int]], center_x: float, screen_w: int) -> tuple[int | None, bool]:
    total_width = sum(end - start + 1 for start, end in runs)
    if len(runs) > 1 and total_width >= screen_w * 0.85:
        return total_width, True
    centered_run = next(((start, end) for start, end in runs if start <= center_x <= end), None)
    if centered_run:
        return centered_run[1] - centered_run[0] + 1, False
    return None, False


def build_visible_screen_mask(alpha: bytes, frame_size: tuple[int, int], screen: dict) -> Image.Image:
    frame_w, frame_h = frame_size
    box_left = math.floor(float(screen["left"]))
    box_top = math.floor(float(screen["top"]))
    box_right = math.ceil(float(screen["left"]) + float(screen["width"]))
    box_bottom = math.ceil(float(screen["top"]) + float(screen["height"]))

    mask = Image.new("L", frame_size, 0)
    draw = ImageDraw.Draw(mask)
    any_pixels = False
    for y in range(max(0, box_top), min(frame_h, box_bottom)):
        for start, end in transparent_runs(alpha, frame_w, y):
            clipped_start = max(start, box_left)
            clipped_end = min(end, box_right - 1)
            if clipped_start <= clipped_end:
                draw.line((clipped_start, y, clipped_end, y), fill=255)
                any_pixels = True

    if any_pixels:
        return mask

    corner_radius = int(round(max(float(screen.get("rx", 0.0)), float(screen.get("ry", 0.0)))))
    draw.rounded_rectangle(
        (box_left, box_top, box_right - 1, box_bottom - 1),
        radius=max(0, corner_radius),
        fill=255,
    )
    return mask


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
        if prev[2] < max_width * 0.2 or not any(start <= center_x <= end for start, end in prev[1]):
            break
        y0 -= 1
    while y1 + 1 in rows_by_y:
        nxt = rows_by_y[y1 + 1]
        if nxt[2] < max_width * 0.2 or not any(start <= center_x <= end for start, end in nxt[1]):
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
        min_centered_width = min(run_width for _, run_width, _ in top_centered_rows)
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

    return {
        "left": x0,
        "top": y0,
        "width": screen_w,
        "height": screen_h,
        "rx": rx,
        "ry": ry,
    }


def measure_frame(frame_path: Path) -> dict:
    with Image.open(frame_path) as image:
        rgba = image.convert("RGBA")
        frame_w, frame_h = rgba.size
        alpha = rgba.getchannel("A").tobytes()
    screen = detect_screen(alpha, frame_w, frame_h)
    if not screen:
        raise SystemExit(f"Could not detect the screen opening in {frame_path.name}")
    return {
        "filename": frame_path.name,
        "framePath": f"/frames/{frame_path.name}",
        "frameW": frame_w,
        "frameH": frame_h,
        "screen": screen,
    }


def infer_family(frame_entry: dict, frame_path: Path) -> str | None:
    family = frame_entry.get("family")
    if isinstance(family, str) and family:
        return family
    normalized_name = normalize_text(frame_path.stem)
    if "iphone" in normalized_name:
        return "iphone"
    return None


def extend_screen_under_top_cutout(frame: Image.Image, frame_entry: dict, frame_path: Path) -> dict:
    screen = dict(frame_entry["screen"])
    if frame_entry.get("topOverlayCutout"):
        screen["hasTopOverlayCutout"] = True
        return screen

    family = infer_family(frame_entry, frame_path)
    if family != "iphone" or int(screen["height"]) <= int(screen["width"]):
        return screen

    alpha = frame.getchannel("A").tobytes()
    frame_w, _ = frame.size
    screen_width = int(screen["width"])
    current_top = int(screen["top"])
    if current_top <= 0:
        return screen

    min_run_width = max(40, round(screen_width * 0.12))
    min_total_width = screen_width * 0.4
    cutout_rows: list[int] = []

    for y in range(current_top - 1, -1, -1):
        runs = [
            (start, end)
            for start, end in transparent_runs(alpha, frame_w, y)
            if (end - start + 1) >= min_run_width
        ]
        total_width = sum(end - start + 1 for start, end in runs)
        if len(runs) >= 2 and total_width >= min_total_width:
            cutout_rows.append(y)
            continue
        if cutout_rows:
            break

    if not cutout_rows:
        return screen

    extended_top = min(cutout_rows)
    if extended_top >= current_top:
        return screen

    screen["top"] = extended_top
    screen["height"] = int(screen["height"]) + (current_top - extended_top)
    screen["hasTopOverlayCutout"] = True
    return screen


def resolve_frame_entry(frame_path: Path, shared_entries: list[dict]) -> tuple[dict, str]:
    for entry in shared_entries:
        if entry.get("filename") == frame_path.name:
            stored_w = entry.get("frameW")
            stored_h = entry.get("frameH")
            if stored_w is None or stored_h is None:
                return measure_frame(frame_path), "measured"
            with Image.open(frame_path) as frame_image:
                actual_w, actual_h = frame_image.size
            if int(stored_w) == int(actual_w) and int(stored_h) == int(actual_h):
                return entry, "shared-reference"
            return measure_frame(frame_path), "measured"
    return measure_frame(frame_path), "measured"


def rotate_rect(rect: dict, source_w: int, source_h: int, direction: str) -> dict:
    if direction == "counterclockwise":
        return {
            **rect,
            "left": int(rect["top"]),
            "top": source_w - (int(rect["left"]) + int(rect["width"])),
            "width": int(rect["height"]),
            "height": int(rect["width"]),
        }
    return {
        **rect,
        "left": source_h - (int(rect["top"]) + int(rect["height"])),
        "top": int(rect["left"]),
        "width": int(rect["height"]),
        "height": int(rect["width"]),
    }


def rotate_frame_geometry(frame: Image.Image, frame_entry: dict, direction: str) -> tuple[Image.Image, dict]:
    rotation = Image.Transpose.ROTATE_90 if direction == "counterclockwise" else Image.Transpose.ROTATE_270
    rotated_frame = frame.transpose(rotation)
    source_w = int(frame_entry["frameW"])
    source_h = int(frame_entry["frameH"])

    rotated_entry = dict(frame_entry)
    rotated_entry["frameW"] = source_h
    rotated_entry["frameH"] = source_w

    screen = dict(frame_entry["screen"])
    rotated_screen = rotate_rect(screen, source_w, source_h, direction)
    rotated_screen["rx"] = float(screen.get("ry", 0.0))
    rotated_screen["ry"] = float(screen.get("rx", 0.0))
    rotated_entry["screen"] = rotated_screen

    top_overlay = frame_entry.get("topOverlayCutout")
    if top_overlay:
        rotated_entry["topOverlayCutout"] = rotate_rect(top_overlay, source_w, source_h, direction)

    return rotated_frame, rotated_entry


def render_framed_image(
    image_path: Path,
    frame_path: Path,
    frame_entry: dict,
    fit_mode: str,
    landscape_rotation: str,
    screen_bleed: int,
) -> Image.Image:
    with Image.open(image_path) as screenshot_image:
        screenshot = screenshot_image.convert("RGBA")
    with Image.open(frame_path) as frame_image:
        frame = frame_image.convert("RGBA")

    screenshot_orientation = infer_orientation(*screenshot.size)
    frame_orientation = infer_orientation(*frame.size)
    effective_entry = frame_entry
    if screenshot_orientation != frame_orientation:
        frame, effective_entry = rotate_frame_geometry(frame, frame_entry, landscape_rotation)

    screen = extend_screen_under_top_cutout(frame, effective_entry, frame_path)
    frame_alpha = frame.getchannel("A")
    frame_alpha_bytes = frame_alpha.tobytes()
    box_left = math.floor(float(screen["left"]))
    box_top = math.floor(float(screen["top"]))
    box_right = math.ceil(float(screen["left"]) + float(screen["width"]))
    box_bottom = math.ceil(float(screen["top"]) + float(screen["height"]))
    box_width = max(1, box_right - box_left)
    box_height = max(1, box_bottom - box_top)
    bleed = max(0, int(screen_bleed))
    paste_left = max(0, box_left - bleed)
    paste_top = max(0, box_top - bleed)
    paste_right = min(frame.width, box_right + bleed)
    paste_bottom = min(frame.height, box_bottom + bleed)
    paste_width = max(1, paste_right - paste_left)
    paste_height = max(1, paste_bottom - paste_top)

    if fit_mode == "contain":
        composed_screen = ImageOps.contain(screenshot, (box_width, box_height), Image.Resampling.LANCZOS)
        fitted = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
        x = (box_width - composed_screen.width) // 2
        y = (box_height - composed_screen.height) // 2
        fitted.paste(composed_screen, (x, y), composed_screen)
        fitted_layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        fitted_layer.paste(fitted, (box_left, box_top), fitted)
    else:
        fitted = ImageOps.fit(screenshot, (paste_width, paste_height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        fitted_layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        fitted_layer.paste(fitted, (paste_left, paste_top), fitted)

    mask = build_visible_screen_mask(frame_alpha_bytes, frame.size, screen)
    if fit_mode == "cover" and bleed:
        filter_size = max(3, bleed * 2 + 1)
        if filter_size % 2 == 0:
            filter_size += 1
        under_frame_mask = mask.filter(ImageFilter.MaxFilter(filter_size))
        ring_mask = ImageChops.subtract(under_frame_mask, mask)
        ring_mask = ImageChops.multiply(ring_mask, frame_alpha)
        mask = ImageChops.lighter(mask, ring_mask)

    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    canvas = Image.composite(fitted_layer, canvas, mask)
    canvas.alpha_composite(frame)
    return canvas


def infer_output_format(output_path: Path, requested_format: str | None) -> str:
    if requested_format:
        normalized = requested_format.lower()
        if normalized in {"jpg", "jpeg"}:
            return "jpeg"
        if normalized in {"png", "webp"}:
            return normalized
        raise SystemExit(f"Unsupported output format: {requested_format}")

    suffix = output_path.suffix.lower().lstrip(".")
    if suffix in {"jpg", "jpeg"}:
        return "jpeg"
    if suffix in {"png", "webp"}:
        return suffix
    return "png"


def resize_output(image: Image.Image, width: int | None, height: int | None) -> Image.Image:
    if not width and not height:
        return image
    source_w, source_h = image.size
    if width and height:
        target_size = (width, height)
    elif width:
        target_size = (width, max(1, round(source_h * (width / source_w))))
    else:
        target_size = (max(1, round(source_w * (height / source_h))), height)
    return image.resize(target_size, Image.Resampling.LANCZOS)


def save_output(image: Image.Image, output_path: Path, output_format: str, quality: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "jpeg":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        background.save(output_path, format="JPEG", quality=quality, optimize=True)
        return
    if output_format == "webp":
        image.save(output_path, format="WEBP", quality=quality, method=6)
        return
    image.save(output_path, format="PNG")


def main() -> int:
    parser = argparse.ArgumentParser(description="Frame one screenshot image with a Fastlane device bezel.")
    parser.add_argument("--image", required=True, help="Input screenshot PNG/JPG path")
    parser.add_argument("--device", help='Target device query, for example "iPhone 16 Pro Max"')
    parser.add_argument("--frame-file", help="Exact frame filename or absolute path to a frame PNG")
    parser.add_argument("--frame-dir", default=str(DEFAULT_FRAME_DIR), help="Directory containing Fastlane frame PNGs")
    parser.add_argument("--output", help="Output image path (PNG/JPEG/WEBP). Format defaults to the file extension, or png")
    parser.add_argument("--format", choices=("png", "jpeg", "jpg", "webp"), help="Output format. Defaults to the output file extension, or png")
    parser.add_argument("--width", type=int, help="Optional output width in pixels")
    parser.add_argument("--height", type=int, help="Optional output height in pixels")
    parser.add_argument("--quality", type=int, default=95, help="JPEG/WEBP quality from 1-100. Default: 95")
    parser.add_argument(
        "--screen-bleed",
        type=int,
        default=DEFAULT_SCREEN_BLEED,
        help=f"Extra screenshot overscan under the frame in pixels. Default: {DEFAULT_SCREEN_BLEED}",
    )
    parser.add_argument("--orientation", choices=("portrait", "landscape"), help="Preferred frame orientation")
    parser.add_argument(
        "--landscape-rotation",
        choices=("clockwise", "counterclockwise"),
        default="clockwise",
        help="How a portrait frame should be rotated when framing a landscape screenshot. Default: clockwise",
    )
    parser.add_argument("--color-priority", default="", help='Comma-separated preferred color terms, for example "black,silver"')
    parser.add_argument("--fit", choices=("cover", "contain"), default="cover", help="How the screenshot should fill the screen opening")
    parser.add_argument("--list-matches", action="store_true", help="Print the top cached frame matches and exit")
    args = parser.parse_args()

    image_path = Path(args.image).expanduser()
    if not image_path.is_file():
        raise SystemExit(f"Input image does not exist: {image_path}")

    if not args.output and not args.list_matches:
        raise SystemExit("--output is required unless --list-matches is used")
    if args.width is not None and args.width <= 0:
        raise SystemExit("--width must be greater than 0")
    if args.height is not None and args.height <= 0:
        raise SystemExit("--height must be greater than 0")
    if not 1 <= args.quality <= 100:
        raise SystemExit("--quality must be between 1 and 100")
    if args.screen_bleed < 0:
        raise SystemExit("--screen-bleed must be 0 or greater")

    with Image.open(image_path) as image:
        inferred_orientation = infer_orientation(*image.size)

    frame_dir = Path(args.frame_dir).expanduser()
    shared_entries = load_shared_entries()
    shared_entry_map = build_shared_entry_map(shared_entries)
    color_priority = [part.strip() for part in args.color_priority.split(",") if part.strip()]
    frame_path, ranked = resolve_frame_path(
        frame_dir=frame_dir,
        device=args.device,
        frame_file=args.frame_file,
        orientation=args.orientation or inferred_orientation,
        color_priority=color_priority,
        shared_entry_map=shared_entry_map,
    )

    if args.list_matches:
        if not ranked:
            print(frame_path.name)
            return 0
        for score, path in ranked[:10]:
            print(f"{score:6.2f}  {path.name}")
        return 0

    frame_entry, source = resolve_frame_entry(frame_path, shared_entries)
    output_path = Path(args.output).expanduser()
    output_format = infer_output_format(output_path, args.format)
    rendered = render_framed_image(
        image_path,
        frame_path,
        frame_entry,
        args.fit,
        args.landscape_rotation,
        args.screen_bleed,
    )
    resized = resize_output(rendered, args.width, args.height)
    save_output(resized, output_path, output_format, args.quality)

    print(f"[done] wrote {output_path}")
    print(f"[frame] {frame_path.name}")
    print(f"[insets] {source}")
    print(f"[format] {output_format}")
    print(f"[size] {resized.size[0]}x{resized.size[1]}")
    print(f"[screen-bleed] {args.screen_bleed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

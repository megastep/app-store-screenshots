#!/usr/bin/env python3
"""
Render one framed device screenshot from a flat screenshot image and a Fastlane frame PNG.
"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageOps


DEFAULT_FRAME_DIR = Path.home() / ".fastlane" / "frameit" / "latest"
SHARED_INSETS_JSON = Path(__file__).resolve().parents[2] / "app-store-screenshots" / "references" / "frame-insets-latest.json"


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


def transparent_runs(alpha: bytes, width: int, y: int, threshold: int = 0) -> list[tuple[int, int]]:
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

    top_centered_rows: list[tuple[int, int]] = []
    seen_narrowed_top = False
    for y, runs, _ in selected:
        centered_run = next(((start, end) for start, end in runs if start <= center_x <= end), None)
        if centered_run:
            run_width = centered_run[1] - centered_run[0] + 1
            if run_width < screen_w * 0.995:
                seen_narrowed_top = True
                top_centered_rows.append((y, run_width))
                continue
            if not seen_narrowed_top:
                top_centered_rows.append((y, run_width))
                continue
            break
            continue
        if top_centered_rows:
            break

    if top_centered_rows:
        min_centered_width = min(run_width for _, run_width in top_centered_rows)
        rx = max(0.0, (screen_w - min_centered_width) / 2)
        narrowed_rows = [y for y, run_width in top_centered_rows if run_width < screen_w * 0.995]
        ry = max(0.0, (max(narrowed_rows) - y0 + 1) if narrowed_rows else 0.0)
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


def render_framed_image(image_path: Path, frame_path: Path, frame_entry: dict, fit_mode: str) -> Image.Image:
    with Image.open(image_path) as screenshot_image:
        screenshot = screenshot_image.convert("RGBA")
    with Image.open(frame_path) as frame_image:
        frame = frame_image.convert("RGBA")

    screen = extend_screen_under_top_cutout(frame, frame_entry, frame_path)
    box_size = (int(screen["width"]), int(screen["height"]))
    if fit_mode == "contain":
        composed_screen = ImageOps.contain(screenshot, box_size, Image.Resampling.LANCZOS)
        fitted = Image.new("RGBA", box_size, (0, 0, 0, 0))
        x = (box_size[0] - composed_screen.width) // 2
        y = (box_size[1] - composed_screen.height) // 2
        fitted.paste(composed_screen, (x, y), composed_screen)
    else:
        fitted = ImageOps.fit(screenshot, box_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

    box_left = int(screen["left"])
    box_top = int(screen["top"])
    box_width = int(screen["width"])
    box_height = int(screen["height"])
    corner_radius = int(round(max(float(screen.get("rx", 0.0)), float(screen.get("ry", 0.0)))))

    fitted_layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    fitted_layer.paste(fitted, (box_left, box_top), fitted)

    mask = Image.new("L", frame.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        (box_left, box_top, box_left + box_width - 1, box_top + box_height - 1),
        radius=max(0, corner_radius),
        fill=255,
    )

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
    parser.add_argument("--orientation", choices=("portrait", "landscape"), help="Preferred frame orientation")
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
    rendered = render_framed_image(image_path, frame_path, frame_entry, args.fit)
    resized = resize_output(rendered, args.width, args.height)
    save_output(resized, output_path, output_format, args.quality)

    print(f"[done] wrote {output_path}")
    print(f"[frame] {frame_path.name}")
    print(f"[insets] {source}")
    print(f"[format] {output_format}")
    print(f"[size] {resized.size[0]}x{resized.size[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

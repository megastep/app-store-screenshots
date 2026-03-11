#!/usr/bin/env python3
"""
Generate a quick markdown/json reference of frame image dimensions.

Useful for local Fastlane cached frames in ~/.fastlane/frameit/latest and for the
project's narrowed public/frames directory after selection.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


DEFAULT_FRAME_DIR = str(Path.home() / ".fastlane" / "frameit" / "latest")


def is_image(path: Path) -> bool:
    return path.suffix.lower() in {".png", ".jpg", ".jpeg"}


def read_png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(24)
    if signature[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG file")
    width, height = struct.unpack(">II", signature[16:24])
    return width, height


def read_jpeg_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        data = handle.read()
    if data[:2] != b"\xff\xd8":
        raise ValueError("Not a JPEG file")
    offset = 2
    while offset < len(data):
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > len(data):
            break
        block_length = struct.unpack(">H", data[offset:offset + 2])[0]
        if block_length < 2 or offset + block_length > len(data):
            break
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            height, width = struct.unpack(">HH", data[offset + 3:offset + 7])
            return width, height
        offset += block_length
    raise ValueError("Could not determine JPEG dimensions")


def read_image_size(path: Path) -> tuple[int, int]:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return read_png_size(path)
    if suffix in {".jpg", ".jpeg"}:
        return read_jpeg_size(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def infer_family(name: str) -> str:
    lowered = name.lower()
    normalized = lowered.replace("-", " ").replace("_", " ")
    if "macbook" in normalized or "macbook air" in normalized or "macbook pro" in normalized or normalized.startswith("apple macbook"):
        return "mac"
    if "pixel slate" in normalized:
        return "android-tablet"
    if any(term in normalized for term in ("pixel", "galaxy", "nexus", "htc", "huawei", "moto")):
        return "android-phone"
    if "ipad" in normalized:
        return "ipad"
    if "iphone" in normalized:
        return "iphone"
    return "other"


def infer_orientation(width: int, height: int) -> str:
    return "landscape" if width > height else "portrait"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a markdown/json reference of local frame image dimensions.")
    parser.add_argument("--frame-dir", default=DEFAULT_FRAME_DIR, help="Directory to scan for frame images. Default: ~/.fastlane/frameit/latest")
    parser.add_argument("--markdown-out", default="frame-dimensions.md", help="Markdown output path. Default: frame-dimensions.md")
    parser.add_argument("--json-out", default="frame-dimensions.json", help="JSON output path. Default: frame-dimensions.json")
    parser.add_argument("--limit", type=int, help="Optional max number of rows to emit after sorting")
    args = parser.parse_args()

    frame_dir = Path(args.frame_dir).expanduser()
    if not frame_dir.exists():
        raise SystemExit(f"Frame directory does not exist: {frame_dir}")

    rows = []
    for path in sorted(frame_dir.rglob("*")):
        if not path.is_file() or not is_image(path):
            continue
        try:
            width, height = read_image_size(path)
        except Exception:
            continue
        rows.append(
            {
                "filename": path.name,
                "family": infer_family(path.name),
                "orientation": infer_orientation(width, height),
                "width": width,
                "height": height,
            }
        )

    rows.sort(key=lambda row: (row["family"], row["orientation"], row["width"] * row["height"], row["filename"]))
    if args.limit:
        rows = rows[: args.limit]

    markdown_lines = [
        "# Frame Dimensions",
        "",
        f"Source: `{frame_dir.name}`",
        "",
        "| Family | Orientation | Dimensions | Name |",
        "|---|---|---:|---|",
    ]
    for row in rows:
        markdown_lines.append(
            f"| {row['family']} | {row['orientation']} | {row['width']} x {row['height']} | {row['filename']} |"
        )
    markdown_lines.append("")

    markdown_out = Path(args.markdown_out).expanduser()
    json_out = Path(args.json_out).expanduser()
    markdown_out.write_text("\n".join(markdown_lines), encoding="utf-8")
    json_out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    print(f"[done] wrote {markdown_out}")
    print(f"[done] wrote {json_out}")
    print(f"[done] rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
